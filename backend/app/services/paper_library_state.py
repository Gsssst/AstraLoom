"""Helpers for marking remote paper previews that already exist locally."""

from __future__ import annotations

import re
from typing import Any, Iterable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.paper import Paper
from app.services.paper_search import PaperResult


def normalize_title_key(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def strip_arxiv_version(arxiv_id: str | None) -> str:
    return re.sub(r"v\d+$", "", (arxiv_id or "").lower())


def normalize_doi(value: str | None) -> str:
    return (value or "").lower().removeprefix("https://doi.org/").removeprefix("http://doi.org/").strip()


def paper_existing_keys(paper: Paper) -> set[str]:
    keys: set[str] = set()
    if getattr(paper, "arxiv_id", None):
        keys.add(f"arxiv:{strip_arxiv_version(paper.arxiv_id)}")
    if getattr(paper, "doi", None):
        keys.add(f"doi:{normalize_doi(paper.doi)}")
    metadata = getattr(paper, "metadata_json", None) or {}
    if isinstance(metadata, dict):
        remote_id = metadata.get("remote_id") or metadata.get("external_id")
        if remote_id:
            keys.add(f"{paper.source}:{remote_id}")
    if getattr(paper, "title", None):
        keys.add(f"title:{normalize_title_key(paper.title)}")
    return {key for key in keys if not key.endswith(":")}


def remote_existing_keys(paper: PaperResult | dict[str, Any]) -> set[str]:
    if isinstance(paper, dict):
        arxiv_id = paper.get("arxiv_id")
        doi = paper.get("doi")
        source = paper.get("source") or "remote"
        metadata = paper.get("metadata") if isinstance(paper.get("metadata"), dict) else {}
        remote_id = paper.get("remote_id") or metadata.get("remote_id") or metadata.get("external_id")
        title = paper.get("title")
    else:
        arxiv_id = paper.arxiv_id
        doi = paper.doi
        source = paper.source
        metadata = paper.metadata or {}
        remote_id = metadata.get("remote_id") or metadata.get("external_id")
        title = paper.title

    keys: set[str] = set()
    if arxiv_id:
        keys.add(f"arxiv:{strip_arxiv_version(str(arxiv_id))}")
    if doi:
        keys.add(f"doi:{normalize_doi(str(doi))}")
    if remote_id:
        keys.add(f"{source}:{remote_id}")
    if title:
        keys.add(f"title:{normalize_title_key(str(title))}")
    return {key for key in keys if not key.endswith(":")}


async def local_paper_lookup_for_remote_previews(
    db: AsyncSession,
    previews: Iterable[PaperResult | dict[str, Any]],
) -> dict[str, Paper]:
    """Return a key -> Paper lookup for local papers matching bounded remote previews."""

    preview_list = list(previews)
    if not preview_list:
        return {}

    arxiv_ids: set[str] = set()
    dois: set[str] = set()
    titles: set[str] = set()
    remote_ids: set[str] = set()
    for preview in preview_list:
        if isinstance(preview, dict):
            arxiv_id = preview.get("arxiv_id")
            doi = preview.get("doi")
            title = preview.get("title")
            metadata = preview.get("metadata") if isinstance(preview.get("metadata"), dict) else {}
            remote_id = preview.get("remote_id") or metadata.get("remote_id") or metadata.get("external_id")
        else:
            arxiv_id = preview.arxiv_id
            doi = preview.doi
            title = preview.title
            metadata = preview.metadata or {}
            remote_id = metadata.get("remote_id") or metadata.get("external_id")
        if arxiv_id:
            arxiv_ids.add(strip_arxiv_version(str(arxiv_id)))
        if doi:
            dois.add(normalize_doi(str(doi)))
        if title:
            titles.add(normalize_title_key(str(title)))
        if remote_id:
            remote_ids.add(str(remote_id))
    if not (arxiv_ids or dois or titles or remote_ids):
        return {}

    result = await db.execute(select(Paper))
    lookup: dict[str, Paper] = {}
    for paper in result.scalars().all():
        metadata = getattr(paper, "metadata_json", None) or {}
        paper_remote_id: Optional[str] = None
        if isinstance(metadata, dict):
            remote_value = metadata.get("remote_id") or metadata.get("external_id")
            paper_remote_id = str(remote_value) if remote_value else None
        paper_keys = paper_existing_keys(paper)
        matching_keys = paper_keys & {
            *(f"arxiv:{value}" for value in arxiv_ids),
            *(f"doi:{value}" for value in dois),
            *(f"title:{value}" for value in titles),
            *(f"{paper.source}:{value}" for value in remote_ids),
        }
        for key in matching_keys:
            lookup.setdefault(key, paper)
    return lookup


def existing_state_for_preview(
    preview: PaperResult | dict[str, Any],
    lookup: dict[str, Paper],
) -> dict[str, Any]:
    for key in remote_existing_keys(preview):
        paper = lookup.get(key)
        if paper:
            return {
                "in_library": True,
                "local_paper_id": str(paper.id),
                "local_match_key": key,
            }
    return {"in_library": False, "local_paper_id": None, "local_match_key": None}
