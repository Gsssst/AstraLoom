"""飞书文档写入服务。"""

import logging
import httpx
import re
from app.core.config import settings

logger = logging.getLogger(__name__)

FEISHU_API_BASE = "https://open.feishu.cn/open-apis"


class FeishuService:
    """飞书文档写入。"""

    def __init__(self):
        self.app_id = getattr(settings, "FEISHU_APP_ID", "")
        self.app_secret = getattr(settings, "FEISHU_APP_SECRET", "")
        self.client = httpx.AsyncClient(timeout=30.0)
        self._token: str | None = None

    @property
    def configured(self) -> bool:
        return bool(self.app_id and self.app_secret)

    async def _get_token(self) -> str:
        """获取 tenant_access_token。"""
        if self._token:
            return self._token
        try:
            resp = await self.client.post(
                f"{FEISHU_API_BASE}/auth/v3/tenant_access_token/internal",
                json={"app_id": self.app_id, "app_secret": self.app_secret},
            )
            data = resp.json()
            self._token = data.get("tenant_access_token", "")
            return self._token
        except Exception as e:
            logger.error(f"飞书认证失败: {e}")
            raise

    @staticmethod
    def parse_doc_id(url: str) -> str:
        """从飞书链接中提取文档 ID。"""
        patterns = [
            r"feishu\.cn/docx/([A-Za-z0-9]+)",
            r"feishu\.cn/wiki/([A-Za-z0-9]+)",
            r"larkoffice\.com/docx/([A-Za-z0-9]+)",
        ]
        for p in patterns:
            m = re.search(p, url)
            if m:
                return m.group(1)
        raise ValueError("无法从链接中提取文档 ID，请确保是飞书文档链接")

    async def get_document(self, doc_id: str) -> dict:
        """获取文档基本信息。"""
        token = await self._get_token()
        resp = await self.client.get(
            f"{FEISHU_API_BASE}/docx/v1/documents/{doc_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        return resp.json()

    async def append_blocks(self, doc_id: str, markdown_content: str) -> dict:
        """将 Markdown 内容追加到飞书文档末尾。"""
        token = await self._get_token()

        # 先获取文档根 block ID
        doc_info = await self.get_document(doc_id)
        doc_data = doc_info.get("data", {}).get("document", {})
        root_block_id = doc_data.get("block_id", doc_id)

        # 将 Markdown 转换为飞书 block 格式
        blocks = self._markdown_to_blocks(markdown_content)

        resp = await self.client.post(
            f"{FEISHU_API_BASE}/docx/v1/documents/{doc_id}/blocks/{root_block_id}/children",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "children": blocks,
                "index": -1,  # -1 表示追加到末尾
            },
        )
        result = resp.json()
        if result.get("code") != 0:
            logger.error(f"飞书写入失败: {result}")
            raise Exception(f"飞书写入失败: {result.get('msg', '未知错误')}")
        return result

    def _markdown_to_blocks(self, md: str) -> list:
        """将 Markdown 转换为飞书文档 block 格式。"""
        blocks = []
        lines = md.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # 一级标题
            if line.startswith("# ") and not line.startswith("## "):
                blocks.append({
                    "block_type": 3,  # 一级标题
                    "heading1": {
                        "elements": [{"text_run": {"content": line[2:]}}],
                        "style": {},
                    },
                })
                i += 1
                continue

            # 二级标题
            if line.startswith("## "):
                blocks.append({
                    "block_type": 4,  # 二级标题
                    "heading2": {
                        "elements": [{"text_run": {"content": line[3:]}}],
                        "style": {},
                    },
                })
                i += 1
                continue

            # 三级标题
            if line.startswith("### "):
                blocks.append({
                    "block_type": 5,  # 三级标题
                    "heading3": {
                        "elements": [{"text_run": {"content": line[4:]}}],
                        "style": {},
                    },
                })
                i += 1
                continue

            # 分隔线
            if line.startswith("---"):
                blocks.append({"block_type": 22})  # 分隔线
                i += 1
                continue

            # 列表项
            if line.startswith("- "):
                blocks.append({
                    "block_type": 12,  # 无序列表
                    "bullet": {
                        "elements": [{"text_run": {"content": line[2:]}}],
                        "style": {},
                    },
                })
                i += 1
                continue

            # 粗体文本（**xxx**）
            if line.startswith("**") and ":**" not in line:
                content = line.replace("**", "")
                blocks.append({
                    "block_type": 2,  # 普通文本
                    "text": {
                        "elements": [{"text_run": {"content": content, "text_element_style": {"bold": True}}}],
                        "style": {},
                    },
                })
                i += 1
                continue

            # 普通段落
            blocks.append({
                "block_type": 2,  # 普通文本
                "text": {
                    "elements": [{"text_run": {"content": line}}],
                    "style": {},
                },
            })
            i += 1

        return blocks

    async def close(self):
        await self.client.aclose()
