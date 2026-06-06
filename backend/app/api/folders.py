"""文件夹管理 API。"""
from datetime import datetime, timezone
import re

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.db.models.paper import Folder, Paper, PaperFolderItem, UserPaper
from app.core.security import get_current_user
from app.services.paper_search import PaperResult, create_remote_ingest_token, search_scholarly_papers

router = APIRouter(prefix="/folders", tags=["文件夹"])

STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that", "into", "using", "based", "paper",
    "study", "towards", "toward", "approach", "method", "model", "models", "large", "language",
    "learning", "deep", "neural", "network", "networks", "efficient", "robust", "survey",
    "benchmark", "analysis", "research", "review", "system", "systems", "task", "tasks",
}

DOMAIN_TOPIC_HINTS = [
    (
        ("video", "grounding"),
        [
            ("Temporal Video Grounding", "temporal video grounding"),
            ("Video Moment Retrieval", "video moment retrieval"),
            ("Video-Language Grounding", "video language grounding"),
            ("Spatio-temporal Localization", "spatio temporal localization video grounding"),
            ("Grounding Benchmarks", "video grounding benchmark dataset"),
        ],
    ),
    (
        ("multimodal",),
        [
            ("Vision-Language Alignment", "vision language alignment multimodal"),
            ("Multimodal Benchmark", "multimodal benchmark evaluation"),
            ("Video Multimodal Models", "video multimodal large language model"),
        ],
    ),
    (
        ("rag", "retrieval"),
        [
            ("Retrieval Augmentation", "retrieval augmented generation"),
            ("RAG Evaluation", "retrieval augmented generation evaluation benchmark"),
            ("Citation Grounding", "retrieval citation grounding"),
        ],
    ),
]

class FolderCreate(BaseModel):
    name: str = Field(..., max_length=200)
    parent_id: Optional[str] = None
    description: Optional[str] = None


class FolderPaperRequest(BaseModel):
    paper_ids: List[str] = Field(..., min_length=1, max_length=100)

class FolderResponse(BaseModel):
    id: str; name: str; parent_id: Optional[str]; children: list = []
    paper_count: int = 0
    diagnostics: Optional[dict] = None
    model_config = {"from_attributes": True}


class FolderRecommendationResponse(BaseModel):
    items: list[dict]
    query: str
    kind: str
    reason: str
    excluded_existing: int = 0


def _readiness_from_counts(
    *,
    paper_count: int,
    full_text_count: int,
    embedding_count: int,
    read_status_counts: dict[str, int],
) -> dict:
    full_text_coverage = full_text_count / paper_count if paper_count else 0
    embedding_coverage = embedding_count / paper_count if paper_count else 0
    completed_count = read_status_counts.get("completed", 0)
    warnings = []
    if paper_count < 3:
        warnings.append("分类论文少于 3 篇，Idea 生成可能缺少对比证据")
    if full_text_coverage < 0.5:
        warnings.append("全文覆盖率偏低，模型可能只能基于摘要推断")
    if embedding_coverage < 0.5:
        warnings.append("向量覆盖率偏低，相关论文检索命中会受影响")
    if paper_count and completed_count == 0:
        warnings.append("该分类还没有已读论文，建议先完成核心论文阅读")
    return {
        "paper_count": paper_count,
        "full_text_count": full_text_count,
        "full_text_coverage": round(full_text_coverage, 3),
        "embedding_count": embedding_count,
        "embedding_coverage": round(embedding_coverage, 3),
        "read_status_counts": read_status_counts,
        "ready_for_idea": paper_count >= 3 and full_text_coverage >= 0.5 and embedding_coverage >= 0.5,
        "warnings": warnings,
    }


async def _folder_diagnostics(db: AsyncSession, folder_id, user_id) -> dict:
    rows = await _folder_paper_rows(db, folder_id, user_id)
    paper_count = len(rows)
    full_text_count = sum(1 for paper, _status in rows if paper.full_text and len(paper.full_text) > 500)
    embedding_count = sum(1 for paper, _status in rows if paper.embedding is not None)
    read_status_counts = {"unread": 0, "reading": 0, "completed": 0}
    for _paper, status in rows:
        read_status_counts[status if status in read_status_counts else "unread"] += 1
    return _readiness_from_counts(
        paper_count=paper_count,
        full_text_count=full_text_count,
        embedding_count=embedding_count,
        read_status_counts=read_status_counts,
    )


async def _folder_paper_rows(db: AsyncSession, folder_id, user_id) -> list[tuple[Paper, Optional[str]]]:
    result = await db.execute(
        select(Paper, UserPaper.read_status)
        .join(PaperFolderItem, PaperFolderItem.paper_id == Paper.id)
        .outerjoin(UserPaper, (UserPaper.paper_id == Paper.id) & (UserPaper.user_id == user_id))
        .where(PaperFolderItem.folder_id == folder_id, PaperFolderItem.user_id == user_id)
        .order_by(PaperFolderItem.created_at.desc())
    )
    return list(result.all())

def build_tree(folder: Folder, user_id, counts: dict | None = None, diagnostics: dict | None = None) -> dict:
    return {"id": str(folder.id), "name": folder.name, "parent_id": str(folder.parent_id) if folder.parent_id else None,
            "children": [build_tree(c, user_id, counts, diagnostics) for c in (folder.children or []) if c.user_id == user_id], "paper_count": (counts or {}).get(str(folder.id), 0),
            "diagnostics": (diagnostics or {}).get(str(folder.id))}


def _paper_brief(paper: Paper, read_status: str | None = None) -> dict:
    return {
        "id": str(paper.id),
        "title": paper.title,
        "authors": paper.authors,
        "year": paper.year,
        "abstract": paper.abstract[:500] if paper.abstract else None,
        "abstract_full": paper.abstract,
        "arxiv_id": paper.arxiv_id,
        "doi": paper.doi,
        "source": paper.source,
        "citation_count": paper.citation_count,
        "created_at": paper.created_at.isoformat() if paper.created_at else "",
        "read_status": read_status,
    }


def _normalize_text_key(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _strip_arxiv_version(arxiv_id: str) -> str:
    return re.sub(r"v\d+$", "", arxiv_id.lower())


def _paper_existing_keys(paper: Paper) -> set[str]:
    keys = set()
    if paper.arxiv_id:
        keys.add(f"arxiv:{_strip_arxiv_version(paper.arxiv_id)}")
    if paper.doi:
        keys.add(f"doi:{paper.doi.lower().removeprefix('https://doi.org/').removeprefix('http://doi.org/')}")
    metadata = paper.metadata_json or {}
    remote_id = metadata.get("remote_id") or metadata.get("external_id")
    if remote_id:
        keys.add(f"{paper.source}:{remote_id}")
    if paper.title:
        keys.add(f"title:{_normalize_text_key(paper.title)}")
    return keys


def _remote_existing_keys(paper: PaperResult) -> set[str]:
    keys = set()
    if paper.arxiv_id:
        keys.add(f"arxiv:{_strip_arxiv_version(paper.arxiv_id)}")
    if paper.doi:
        keys.add(f"doi:{paper.doi.lower().removeprefix('https://doi.org/').removeprefix('http://doi.org/')}")
    remote_id = (paper.metadata or {}).get("remote_id")
    if remote_id:
        keys.add(f"{paper.source}:{remote_id}")
    if paper.title:
        keys.add(f"title:{_normalize_text_key(paper.title)}")
    return keys


def _tokenize_topic_text(text: str) -> list[str]:
    return [
        token.lower()
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}", text or "")
        if token.lower() not in STOPWORDS and not token.isdigit()
    ]


def _collection_topic_terms(folder: Folder, rows: list[tuple[Paper, Optional[str]]], limit: int = 8) -> list[str]:
    weighted: dict[str, int] = {}

    def add(token: str, weight: int):
        weighted[token] = weighted.get(token, 0) + weight

    for token in _tokenize_topic_text(folder.name):
        add(token, 5)
    for paper, _status in rows:
        for token in _tokenize_topic_text(paper.title):
            add(token, 4)
        for token in _tokenize_topic_text((paper.abstract or "")[:1200]):
            add(token, 1)
        for tag in paper.tags or []:
            for token in _tokenize_topic_text(str(tag)):
                add(token, 3)

    ranked = sorted(weighted.items(), key=lambda item: (-item[1], item[0]))
    return [term for term, _score in ranked[:limit]]


def _paper_matches_query_terms(paper: Paper, query: str) -> bool:
    haystack = f"{paper.title} {paper.abstract or ''} {' '.join(str(tag) for tag in (paper.tags or []))}".lower()
    terms = [term for term in _tokenize_topic_text(query) if term not in {"seminal", "classic", "recent"}]
    if not terms:
        return False
    required = max(1, min(2, len(terms)))
    return sum(1 for term in terms if term in haystack) >= required


def _coverage_topics(folder: Folder, rows: list[tuple[Paper, Optional[str]]], topic_terms: list[str]) -> list[dict]:
    base_query = " ".join(topic_terms[:4]) or folder.name
    candidate_topics: list[tuple[str, str]] = [
        ("Survey / Overview", f"{base_query} survey"),
        ("Benchmark / Dataset", f"{base_query} benchmark dataset"),
        ("Methods", f"{base_query} method architecture"),
        ("Evaluation", f"{base_query} evaluation experiment"),
        ("Recent Work", f"{base_query} recent"),
    ]
    lowered_terms = set(topic_terms) | set(_tokenize_topic_text(folder.name))
    for triggers, hints in DOMAIN_TOPIC_HINTS:
        if all(trigger in lowered_terms for trigger in triggers):
            candidate_topics.extend(hints)

    seen_queries = set()
    topics = []
    for label, query in candidate_topics:
        query_key = _normalize_text_key(query)
        if query_key in seen_queries:
            continue
        seen_queries.add(query_key)
        matched = [paper for paper, _status in rows if _paper_matches_query_terms(paper, query)]
        if len(matched) >= 2:
            status = "covered"
        elif len(matched) == 1:
            status = "thin"
        else:
            status = "missing"
        topics.append({
            "label": label,
            "query": query,
            "matched_count": len(matched),
            "matched_titles": [paper.title for paper in matched[:3]],
            "status": status,
        })
    return topics


def _coverage_summary(topics: list[dict], paper_count: int) -> str:
    missing = [topic["label"] for topic in topics if topic["status"] == "missing"]
    thin = [topic["label"] for topic in topics if topic["status"] == "thin"]
    if paper_count == 0:
        return "这个分类还没有论文，建议先用经典/综述类查询建立种子集合。"
    if missing:
        return f"分类已有 {paper_count} 篇论文，但 {missing[0]} 等主题还没有命中，建议优先补缺口论文。"
    if thin:
        return f"分类已有 {paper_count} 篇论文，{thin[0]} 等主题覆盖偏薄，建议补 1-2 篇代表作。"
    return f"分类已有 {paper_count} 篇论文，核心主题覆盖较均衡，可以继续补近期工作保持新鲜度。"


def _recommended_queries(folder: Folder, topic_terms: list[str], topics: list[dict]) -> dict:
    base = " ".join(topic_terms[:4]) or folder.name
    gap_topic = next((topic for topic in topics if topic["status"] in {"missing", "thin"}), None)
    return {
        "classic": f"{base} seminal survey benchmark",
        "recent": f"{base} recent",
        "gap": gap_topic["query"] if gap_topic else f"{base} open problems",
        "related": base,
    }


def _recommendation_reason(kind: str, query: str) -> str:
    return {
        "classic": "用于补齐该分类的经典论文、综述或基准工作。",
        "recent": "用于补齐该分类近两年的新论文。",
        "gap": f"该方向在分类覆盖分析中偏薄，建议优先检索：{query}",
        "related": "基于分类主题词扩展相近论文。",
    }.get(kind, "基于分类主题词推荐。")


def _remote_recommendation_brief(paper: PaperResult, kind: str, reason: str) -> dict:
    return {
        "id": "",
        "title": paper.title,
        "authors": paper.authors,
        "year": paper.year,
        "abstract": paper.abstract[:500] if paper.abstract else None,
        "abstract_full": paper.abstract or None,
        "arxiv_id": paper.arxiv_id,
        "doi": paper.doi,
        "source": paper.source,
        "citation_count": paper.citation_count,
        "created_at": "",
        "remote_id": (paper.metadata or {}).get("remote_id"),
        "remote_ingest_token": create_remote_ingest_token(paper),
        "pdf_url": paper.pdf_url,
        "source_url": paper.source_url,
        "recommendation_kind": kind,
        "recommendation_reason": reason,
    }


async def _owned_folder(db: AsyncSession, folder_id: str, user) -> Folder:
    from uuid import UUID
    try:
        fid = UUID(folder_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid folder_id")
    folder = (await db.execute(
        select(Folder).where(Folder.id == fid, Folder.user_id == user.id)
    )).scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="分类未找到")
    return folder

@router.get("/", response_model=List[dict])
async def list_folders(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    stats_result = await db.execute(
        select(PaperFolderItem.folder_id, func.count(PaperFolderItem.paper_id))
        .where(PaperFolderItem.user_id == user.id)
        .group_by(PaperFolderItem.folder_id)
    )
    counts = {str(folder_id): int(count or 0) for folder_id, count in stats_result.all()}
    result = await db.execute(
        select(Folder).where(
            Folder.parent_id.is_(None),
            Folder.user_id == user.id,
        ).options(selectinload(Folder.children))
    )
    folders = result.scalars().all()
    diagnostics = {str(folder.id): await _folder_diagnostics(db, folder.id, user.id) for folder in folders}
    return [build_tree(f, user.id, counts, diagnostics) for f in folders]

@router.post("/", status_code=201)
async def create_folder(req: FolderCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    from uuid import UUID
    try:
        parent_id = UUID(req.parent_id) if req.parent_id else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid parent_id")
    if parent_id:
        parent = (await db.execute(
            select(Folder).where(Folder.id == parent_id, Folder.user_id == user.id)
        )).scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=404, detail="文件夹未找到")
    folder = Folder(name=req.name, parent_id=parent_id, user_id=user.id)
    db.add(folder); await db.commit(); await db.refresh(folder)
    return {"id": str(folder.id), "name": folder.name, "paper_count": 0}


@router.get("/{folder_id}/papers")
async def list_folder_papers(folder_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """列出某个用户分类下的论文。"""
    folder = await _owned_folder(db, folder_id, user)
    result = await db.execute(
        select(Paper, UserPaper.read_status)
        .join(PaperFolderItem, PaperFolderItem.paper_id == Paper.id)
        .outerjoin(UserPaper, (UserPaper.paper_id == Paper.id) & (UserPaper.user_id == user.id))
        .where(PaperFolderItem.folder_id == folder.id, PaperFolderItem.user_id == user.id)
        .order_by(PaperFolderItem.created_at.desc())
    )
    return [_paper_brief(paper, read_status) for paper, read_status in result.all()]


@router.get("/{folder_id}/diagnostics")
async def get_folder_diagnostics(folder_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """获取分类覆盖率与 Idea 生成准备度。"""
    folder = await _owned_folder(db, folder_id, user)
    diagnostics = await _folder_diagnostics(db, folder.id, user.id)
    return {"folder_id": str(folder.id), "name": folder.name, **diagnostics}


@router.get("/{folder_id}/coverage")
async def get_folder_coverage(folder_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """分析分类主题覆盖与补论文查询建议。"""
    folder = await _owned_folder(db, folder_id, user)
    rows = await _folder_paper_rows(db, folder.id, user.id)
    topic_terms = _collection_topic_terms(folder, rows)
    topics = _coverage_topics(folder, rows, topic_terms)
    return {
        "folder_id": str(folder.id),
        "name": folder.name,
        "paper_count": len(rows),
        "topic_terms": topic_terms,
        "topics": topics,
        "summary": _coverage_summary(topics, len(rows)),
        "recommended_queries": _recommended_queries(folder, topic_terms, topics),
    }


@router.get("/{folder_id}/recommendations", response_model=FolderRecommendationResponse)
async def get_folder_recommendations(
    folder_id: str,
    kind: Literal["classic", "recent", "gap", "related"] = Query("related"),
    query: Optional[str] = Query(None, min_length=2, max_length=300),
    limit: int = Query(6, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """为分类推荐可一键入库的外部论文候选。"""
    folder = await _owned_folder(db, folder_id, user)
    rows = await _folder_paper_rows(db, folder.id, user.id)
    topic_terms = _collection_topic_terms(folder, rows)
    topics = _coverage_topics(folder, rows, topic_terms)
    suggested_queries = _recommended_queries(folder, topic_terms, topics)
    recommendation_query = query.strip() if query and query.strip() else suggested_queries.get(kind) or suggested_queries["related"]
    current_year = datetime.now(timezone.utc).year
    year_from = current_year - 2 if kind == "recent" else None
    sort_by = "date" if kind == "recent" else "relevance"
    reason = _recommendation_reason(kind, recommendation_query)

    existing_keys = set()
    for paper, _status in rows:
        existing_keys.update(_paper_existing_keys(paper))

    candidates = await search_scholarly_papers(
        recommendation_query,
        source="scholarly",
        max_results=max(limit * 3, 12),
        year_from=year_from,
        sort_by=sort_by,
    )
    items: list[dict] = []
    excluded_existing = 0
    seen_remote_keys: set[str] = set()
    for candidate in candidates:
        candidate_keys = _remote_existing_keys(candidate)
        if candidate_keys & existing_keys:
            excluded_existing += 1
            continue
        dedupe_key = next(iter(candidate_keys), f"title:{_normalize_text_key(candidate.title)}")
        if dedupe_key in seen_remote_keys:
            continue
        seen_remote_keys.add(dedupe_key)
        items.append(_remote_recommendation_brief(candidate, kind, reason))
        if len(items) >= limit:
            break

    return FolderRecommendationResponse(
        items=items,
        query=recommendation_query,
        kind=kind,
        reason=reason,
        excluded_existing=excluded_existing,
    )


@router.get("/{folder_id}/paper-ids")
async def list_folder_paper_ids(folder_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """返回分类论文 ID，用于研究方向种子论文导入。"""
    folder = await _owned_folder(db, folder_id, user)
    result = await db.execute(
        select(PaperFolderItem.paper_id)
        .where(PaperFolderItem.folder_id == folder.id, PaperFolderItem.user_id == user.id)
        .order_by(PaperFolderItem.created_at.desc())
    )
    return {"folder_id": str(folder.id), "paper_ids": [str(pid) for pid in result.scalars().all()]}


@router.post("/{folder_id}/papers")
async def add_papers_to_folder(folder_id: str, req: FolderPaperRequest, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """把论文加入用户分类。"""
    from uuid import UUID
    folder = await _owned_folder(db, folder_id, user)
    paper_ids = []
    for raw_id in req.paper_ids:
        try:
            paper_ids.append(UUID(raw_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid paper_id")
    if not paper_ids:
        return {"added": 0, "skipped": 0}

    paper_result = await db.execute(select(Paper.id).where(Paper.id.in_(paper_ids)))
    existing_paper_ids = set(paper_result.scalars().all())
    missing = [str(pid) for pid in paper_ids if pid not in existing_paper_ids]
    if missing:
        raise HTTPException(status_code=404, detail=f"论文不存在: {', '.join(missing[:3])}")

    existing_result = await db.execute(
        select(PaperFolderItem.paper_id).where(
            PaperFolderItem.folder_id == folder.id,
            PaperFolderItem.user_id == user.id,
            PaperFolderItem.paper_id.in_(paper_ids),
        )
    )
    existing_items = set(existing_result.scalars().all())
    added = 0
    for pid in paper_ids:
        user_paper = (await db.execute(
            select(UserPaper).where(UserPaper.user_id == user.id, UserPaper.paper_id == pid)
        )).scalar_one_or_none()
        if not user_paper:
            db.add(UserPaper(user_id=user.id, paper_id=pid, saved=True))
        else:
            user_paper.saved = True
        if pid not in existing_items:
            db.add(PaperFolderItem(folder_id=folder.id, paper_id=pid, user_id=user.id))
            added += 1
    await db.commit()
    return {"folder_id": str(folder.id), "added": added, "skipped": len(paper_ids) - added}


@router.delete("/{folder_id}/papers/{paper_id}")
async def remove_paper_from_folder(folder_id: str, paper_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """从分类中移除论文，不影响论文收藏状态。"""
    from uuid import UUID
    folder = await _owned_folder(db, folder_id, user)
    try:
        pid = UUID(paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid paper_id")
    item = (await db.execute(
        select(PaperFolderItem).where(
            PaperFolderItem.folder_id == folder.id,
            PaperFolderItem.paper_id == pid,
            PaperFolderItem.user_id == user.id,
        )
    )).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="分类论文未找到")
    await db.delete(item)
    await db.commit()
    return {"removed": True, "folder_id": str(folder.id), "paper_id": str(pid)}

@router.delete("/{folder_id}")
async def delete_folder(folder_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    from uuid import UUID
    try:
        fid = UUID(folder_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid folder_id")
    f = (await db.execute(
        select(Folder).where(Folder.id == fid, Folder.user_id == user.id)
    )).scalar_one_or_none()
    if not f: raise HTTPException(status_code=404, detail="文件夹未找到")
    await db.delete(f); await db.commit()
    return {"deleted": True, "folder_id": str(fid)}
