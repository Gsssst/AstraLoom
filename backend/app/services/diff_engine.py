"""Diff 引擎 — 参考 TexGuardian 的 AI diff 补丁机制。

基于 difflib.SequenceMatcher 的句子级 diff，
支持 LaTeX 感知（保护公式/引用块）、
生成 unified diff hunks、
逐条 accept/reject、
多版本管理。
"""

import difflib
import logging
import re
from typing import List, Dict, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class DiffEngine:
    """文本 Diff 引擎 — 句子级对比与 hunks 管理。"""

    def __init__(self):
        self._sentence_pattern = re.compile(r'([^.!?。！？\n]+[.!?。！？]?)')

    def split_sentences(self, text: str) -> List[str]:
        """将文本按句子分割。"""
        sentences = []
        for match in self._sentence_pattern.finditer(text):
            s = match.group().strip()
            if s:
                sentences.append(s)
        # 处理尾部无标点的内容
        remaining = self._sentence_pattern.sub('', text).strip()
        if remaining:
            sentences.append(remaining)
        return sentences if sentences else [text]

    def compute_diff(self, original: str, polished: str,
                     latex_blocks: Optional[List[dict]] = None) -> dict:
        """计算两个文本之间的句子级 diff。

        Args:
            original: 原始文本
            polished: 润色后文本
            latex_blocks: 受保护的 LaTeX 块列表（不被 diff）

        Returns:
            {
                "hunks": [
                    {
                        "index": 0,
                        "type": "equal" | "add" | "delete" | "replace",
                        "original": "原句",
                        "polished": "新句",
                        "position": 5  # 在原文本中的大致位置（字符偏移）
                    },
                    ...
                ],
                "stats": {"additions": 5, "deletions": 3, "equal": 10, "replacements": 2}
            }
        """
        if latex_blocks:
            # LaTeX 感知模式：将 LaTeX 块替换为占位符
            from app.services.latex_processor import latex_processor
            clean_original, block_map = latex_processor.protect(original)
            clean_polished, _ = latex_processor.protect(polished)
        else:
            clean_original, clean_polished = original, polished

        orig_sents = self.split_sentences(clean_original)
        pol_sents = self.split_sentences(clean_polished)

        matcher = difflib.SequenceMatcher(None, orig_sents, pol_sents)
        hunks = []
        stats = {"additions": 0, "deletions": 0, "equal": 0, "replacements": 0}

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            orig_segment = " ".join(orig_sents[i1:i2])
            pol_segment = " ".join(pol_sents[j1:j2])

            if tag == "equal":
                hunks.append({
                    "type": "equal",
                    "original": orig_segment,
                    "polished": orig_segment,
                    "position": sum(len(s) for s in orig_sents[:i1]),
                    "accepted": None,
                })
                stats["equal"] += 1
            elif tag == "delete":
                hunks.append({
                    "type": "delete",
                    "original": orig_segment,
                    "polished": "",
                    "position": sum(len(s) for s in orig_sents[:i1]),
                    "accepted": None,
                })
                stats["deletions"] += 1
            elif tag == "insert":
                hunks.append({
                    "type": "add",
                    "original": "",
                    "polished": pol_segment,
                    "position": sum(len(s) for s in orig_sents[:i1]),
                    "accepted": None,
                })
                stats["additions"] += 1
            elif tag == "replace":
                hunks.append({
                    "type": "replace",
                    "original": orig_segment,
                    "polished": pol_segment,
                    "position": sum(len(s) for s in orig_sents[:i1]),
                    "accepted": None,
                })
                stats["replacements"] += 1

        # 给每个 hunk 分配索引
        for i, hunk in enumerate(hunks):
            hunk["index"] = i

        return {"hunks": hunks, "stats": stats}

    def to_unified_diff(self, original: str, polished: str) -> str:
        """生成 unified diff 格式的文本。"""
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            polished.splitlines(keepends=True),
            fromfile="original",
            tofile="polished",
            lineterm="",
        )
        return "".join(diff)

    def apply_hunks(self, hunks: List[dict], accept_indices: set) -> str:
        """应用指定的 hunks（接受）并保留其他为原始内容。

        Args:
            hunks: diff hunks 列表
            accept_indices: 要接受的 hunk 索引集合

        Returns:
            应用选定 hunks 后的文本
        """
        parts = []
        for hunk in sorted(hunks, key=lambda h: h.get("position", 0)):
            hunk_idx = hunk.get("index", -1)
            if hunk_idx in accept_indices:
                # 接受：使用润色版本
                if hunk["type"] in ("add", "replace"):
                    parts.append(hunk["polished"])
                elif hunk["type"] == "delete":
                    # 接受删除 → 不添加任何内容
                    pass
                elif hunk["type"] == "equal":
                    parts.append(hunk["original"])
            else:
                # 拒绝：保留原文
                if hunk["type"] in ("equal", "delete", "replace"):
                    parts.append(hunk["original"])
                elif hunk["type"] == "add":
                    # 拒绝新增 → 不添加
                    pass

        return " ".join(parts)

    def reject_hunks(self, hunks: List[dict], reject_indices: set) -> str:
        """拒绝指定的 hunks，保留原文。"""
        all_indices = set(range(len(hunks)))
        accept_indices = all_indices - reject_indices
        return self.apply_hunks(hunks, accept_indices)


class PolishVersionManager:
    """润色版本管理器。"""

    MAX_VERSIONS = 10

    def __init__(self, db_session_factory=None):
        self.db_factory = db_session_factory

    async def create_version(
        self, section_id: str, original: str, polished: str,
        diff_data: dict, user_actions: Optional[dict] = None,
    ) -> dict:
        """创建新版本记录。"""
        if not self.db_factory:
            return {"version_number": -1, "stored": False}
        try:
            sid = UUID(str(section_id))
        except (TypeError, ValueError):
            return {"version_number": -1, "stored": False, "error": "invalid_section_id"}

        from app.db.session import AsyncSessionLocal
        from app.db.models.writing import PolishVersion
        from sqlalchemy import select, func

        async with AsyncSessionLocal() as session:
            # 获取当前最大版本号
            result = await session.execute(
                select(func.max(PolishVersion.version_number))
                .where(PolishVersion.section_id == sid)
            )
            max_version = result.scalar() or 0

            # 清理超出上限的旧版本
            if max_version >= self.MAX_VERSIONS:
                oldest = await session.execute(
                    select(PolishVersion)
                    .where(PolishVersion.section_id == sid)
                    .order_by(PolishVersion.version_number)
                    .limit(max_version - self.MAX_VERSIONS + 1)
                )
                for old in oldest.scalars().all():
                    await session.delete(old)

            version = PolishVersion(
                section_id=sid,
                original_text=original,
                polished_text=polished,
                diff_json=diff_data,
                version_number=max_version + 1,
                user_actions=user_actions or {},
            )
            session.add(version)
            await session.commit()
            return {
                "version_number": max_version + 1,
                "stored": True,
                "id": str(version.id),
            }

    async def get_versions(self, section_id: str) -> list:
        """获取某章节的所有版本。"""
        if not self.db_factory:
            return []
        try:
            sid = UUID(str(section_id))
        except (TypeError, ValueError):
            return []

        from app.db.session import AsyncSessionLocal
        from app.db.models.writing import PolishVersion
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(PolishVersion)
                .where(PolishVersion.section_id == sid)
                .order_by(PolishVersion.version_number.desc())
            )
            return [
                {
                    "id": str(v.id),
                    "version_number": v.version_number,
                    "polished_text": v.polished_text,
                    "diff_summary": f"{len(v.diff_json.get('hunks', [])) if v.diff_json else 0} changes",
                    "created_at": v.created_at.isoformat() if v.created_at else "",
                }
                for v in result.scalars().all()
            ]


# 全局单例
diff_engine = DiffEngine()
