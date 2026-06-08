"""LaTeX 感知处理器 — 参考 GPT Academic 的 LaTeX 块保护机制。

润色/翻译时自动保留 LaTeX 命令、公式、引用、图表环境。
支持 .tex 文件导入导出和编译检查。
"""

import logging
import re
from typing import List, Tuple

logger = logging.getLogger(__name__)


class LatexProcessor:
    """LaTeX 感知文本处理器。

    核心机制（参考 GPT Academic）：
    1. 检测受保护的 LaTeX 块
    2. 替换为占位符
    3. LLM 处理纯文本
    4. 还原占位符
    """

    # 受保护的 LaTeX 模式
    PROTECTED_PATTERNS = [
        # 行内公式 $...$
        (r'\$[^$]+\$', 'inline_math'),
        # 行间公式 $$...$$
        (r'\$\$[^$]+\$\$', 'display_math'),
        # 公式环境
        (r'\\begin\{equation\*?\}.*?\\end\{equation\*?\}', 'equation_env'),
        (r'\\begin\{align\*?\}.*?\\end\{align\*?\}', 'align_env'),
        # 引用命令
        (r'\\cite\{[^}]*\}', 'cite_cmd'),
        (r'\\citep\{[^}]*\}', 'citep_cmd'),
        (r'\\citet\{[^}]*\}', 'citet_cmd'),
        # 交叉引用
        (r'\\ref\{[^}]*\}', 'ref_cmd'),
        (r'\\label\{[^}]*\}', 'label_cmd'),
        # 图表环境
        (r'\\begin\{figure\}.*?\\end\{figure\}', 'figure_env'),
        (r'\\begin\{table\}.*?\\end\{table\}', 'table_env'),
        # 列表环境
        (r'\\begin\{itemize\}.*?\\end\{itemize\}', 'itemize_env'),
        (r'\\begin\{enumerate\}.*?\\end\{enumerate\}', 'enumerate_env'),
    ]

    # 用于编译检查的标记
    MARKERS = {
        'inline_math': ('<<<MATH_INLINE_{}>>>', '<<<MATH_INLINE_{}>>>'),
        'display_math': ('<<<MATH_DISPLAY_{}>>>', '<<<MATH_DISPLAY_{}>>>'),
        'equation_env': ('<<<EQ_ENV_{}>>>', '<<<EQ_ENV_{}>>>'),
        'align_env': ('<<<ALIGN_ENV_{}>>>', '<<<ALIGN_ENV_{}>>>'),
        'cite_cmd': ('<<<CITE_{}>>>', '<<<CITE_{}>>>'),
        'citep_cmd': ('<<<CITEP_{}>>>', '<<<CITEP_{}>>>'),
        'citet_cmd': ('<<<CITET_{}>>>', '<<<CITET_{}>>>'),
        'ref_cmd': ('<<<REF_{}>>>', '<<<REF_{}>>>'),
        'label_cmd': ('<<<LABEL_{}>>>', '<<<LABEL_{}>>>'),
        'figure_env': ('<<<FIG_ENV_{}>>>', '<<<FIG_ENV_{}>>>'),
        'table_env': ('<<<TABLE_ENV_{}>>>', '<<<TABLE_ENV_{}>>>'),
        'itemize_env': ('<<<ITEMIZE_{}>>>', '<<<ITEMIZE_{}>>>'),
        'enumerate_env': ('<<<ENUM_{}>>>', '<<<ENUM_{}>>>'),
    }

    def __init__(self):
        self._compiled_patterns = [
            (re.compile(p, re.DOTALL), ptype)
            for p, ptype in self.PROTECTED_PATTERNS
        ]

    def find_protected_blocks(self, text: str) -> List[Tuple[str, str, int, int]]:
        """扫描文本，返回所有受保护的 LaTeX 块。

        Returns:
            List of (block_text, block_type, start_pos, end_pos)
        """
        blocks = []
        seen_ranges = set()

        for pattern, ptype in self._compiled_patterns:
            for match in pattern.finditer(text):
                start, end = match.start(), match.end()
                # 检查是否与已找到的块重叠
                if not any(s <= start < e or s < end <= e for s, e in seen_ranges):
                    blocks.append((match.group(), ptype, start, end))
                    seen_ranges.add((start, end))

        # 按位置排序
        blocks.sort(key=lambda x: x[2])
        return blocks

    def protect(self, text: str) -> Tuple[str, dict]:
        """将 LaTeX 块替换为占位符。

        Returns:
            (protected_text, block_map) — block_map 将占位符映射回原始块
        """
        blocks = self.find_protected_blocks(text)
        block_map = {}
        result = []
        pos = 0

        for block_text, block_type, start, end in blocks:
            # 添加前面的非 LaTeX 文本
            result.append(text[pos:start])
            # 生成占位符
            placeholder = f"<<<LATEX_BLOCK_{len(block_map)}>>>"
            block_map[placeholder] = {"text": block_text, "type": block_type}
            result.append(placeholder)
            pos = end

        # 添加剩余文本
        result.append(text[pos:])
        return "".join(result), block_map

    def restore(self, protected_text: str, block_map: dict) -> str:
        """将占位符还原为原始 LaTeX 块。"""
        result = protected_text
        for placeholder, info in block_map.items():
            result = result.replace(placeholder, info["text"])
        return result

    def extract_sections(self, tex_content: str) -> List[dict]:
        """从 .tex 文件中提取章节结构。

        Returns:
            List of {"title": str, "level": int, "content": str}
        """
        # 匹配 \section{...}、\subsection{...}、\subsubsection{...}
        section_pattern = re.compile(
            r'\\(section|subsection|subsubsection)\{([^}]+)\}',
            re.DOTALL,
        )

        sections = []
        for match in section_pattern.finditer(tex_content):
            level_name = match.group(1)
            title = match.group(2)
            level = {"section": 1, "subsection": 2, "subsubsection": 3}.get(level_name, 1)
            sections.append({
                "title": title,
                "level": level,
                "start": match.end(),
            })

        # 计算每节的内容范围
        for i, sec in enumerate(sections):
            start = sec["start"]
            end = sections[i + 1]["start"] if i + 1 < len(sections) else len(tex_content)
            sec["content"] = tex_content[start:end].strip()

        return sections

    def extract_bibliography(self, tex_content: str) -> str:
        """从 .tex 文件中提取 \\bibliography{...} 引用的 .bib 文件路径。"""
        match = re.search(r'\\bibliography\{([^}]+)\}', tex_content)
        return match.group(1) if match else ""

    def inspect_submission_template(self, filename: str, content: bytes) -> dict:
        """Inspect an uploaded LaTeX submission template or template bundle."""
        filename = filename or "template"
        lower = filename.lower()
        files = []
        warnings = []

        if lower.endswith(".zip"):
            files, zip_warnings = self._inspect_zip_files(content)
            warnings.extend(zip_warnings)
        else:
            text = self._decode_latex_text(content)
            files.append({
                "path": filename,
                "kind": self._latex_file_kind(filename),
                "size": len(content),
                "content": text,
            })

        tex_files = [item for item in files if item["kind"] == "tex"]
        cls_files = [item["path"] for item in files if item["kind"] == "cls"]
        sty_files = [item["path"] for item in files if item["kind"] == "sty"]
        main_tex = self._select_main_tex(tex_files)
        source_text = main_tex.get("content", "") if main_tex else "\n".join(item.get("content", "") for item in files[:8])
        document_class = self._extract_document_class(source_text)
        packages = self._extract_packages(source_text)
        bibliography = self.extract_bibliography(source_text)
        sections = self.extract_sections(source_text) if main_tex else []

        if lower.endswith(".zip") and not tex_files:
            warnings.append("模板包中没有找到 .tex 主文件。")
        if not document_class and not cls_files:
            warnings.append("没有检测到 \\documentclass 或 .cls 文件，请确认上传的是完整官方模板。")
        if not cls_files and not sty_files and lower.endswith(".zip"):
            warnings.append("模板包中没有检测到 .cls/.sty 样式文件，可能只是普通源码包。")

        venue_hints = self._guess_venue_hints(" ".join([filename, source_text[:3000], " ".join(cls_files + sty_files)]))
        status = "ready" if not warnings else "needs_review"
        return {
            "status": status,
            "status_label": "已识别模板" if status == "ready" else "需要人工确认",
            "source_filename": filename,
            "file_count": len(files),
            "main_tex": main_tex["path"] if main_tex else "",
            "document_class": document_class,
            "class_files": cls_files,
            "style_files": sty_files,
            "packages": packages[:20],
            "bibliography": bibliography,
            "section_titles": [section["title"] for section in sections[:12]],
            "venue_hints": venue_hints,
            "warnings": warnings,
        }

    def _inspect_zip_files(self, content: bytes) -> tuple[list[dict], list[str]]:
        import io
        import zipfile

        files = []
        warnings = []
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                names = [name for name in archive.namelist() if not name.endswith("/")][:80]
                for name in names:
                    kind = self._latex_file_kind(name)
                    if kind == "other":
                        continue
                    info = archive.getinfo(name)
                    if info.file_size > 512_000:
                        warnings.append(f"{name} 文件较大，已跳过内容解析。")
                        text = ""
                    else:
                        text = self._decode_latex_text(archive.read(name))
                    files.append({
                        "path": name,
                        "kind": kind,
                        "size": info.file_size,
                        "content": text,
                    })
        except zipfile.BadZipFile:
            warnings.append("无法解析 zip 模板包，请确认文件未损坏。")
        if not files:
            warnings.append("模板包中没有找到可解析的 .tex/.cls/.sty 文件。")
        return files, warnings

    def _latex_file_kind(self, filename: str) -> str:
        lower = (filename or "").lower()
        if lower.endswith(".tex"):
            return "tex"
        if lower.endswith(".cls"):
            return "cls"
        if lower.endswith(".sty"):
            return "sty"
        if lower.endswith(".bib"):
            return "bib"
        return "other"

    def _decode_latex_text(self, content: bytes) -> str:
        for encoding in ("utf-8", "latin-1"):
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        return content.decode("utf-8", errors="ignore")

    def _select_main_tex(self, tex_files: list[dict]) -> dict | None:
        if not tex_files:
            return None
        with_document = [item for item in tex_files if "\\documentclass" in item.get("content", "")]
        if with_document:
            return sorted(with_document, key=lambda item: (0 if "main" in item["path"].lower() else 1, len(item["path"])))[0]
        return sorted(tex_files, key=lambda item: (0 if "main" in item["path"].lower() else 1, len(item["path"])))[0]

    def _extract_document_class(self, tex_content: str) -> str:
        match = re.search(r'\\documentclass(?:\[[^\]]*\])?\{([^}]+)\}', tex_content or "")
        return match.group(1).strip() if match else ""

    def _extract_packages(self, tex_content: str) -> list[str]:
        packages = []
        for match in re.finditer(r'\\usepackage(?:\[[^\]]*\])?\{([^}]+)\}', tex_content or ""):
            for package in match.group(1).split(","):
                name = package.strip()
                if name and name not in packages:
                    packages.append(name)
        return packages

    def _guess_venue_hints(self, text: str) -> list[str]:
        hints = []
        candidates = ["ACL", "EMNLP", "NAACL", "CVPR", "ICCV", "ECCV", "NeurIPS", "ICML", "ICLR", "AAAI"]
        lowered = (text or "").lower()
        for candidate in candidates:
            if candidate.lower() in lowered and candidate not in hints:
                hints.append(candidate)
        return hints

    def render_to_tex(self, project_title: str, sections: List[dict],
                      template: str = "article") -> str:
        """将写作项目渲染为 .tex 文件。"""
        lines = [
            r"\documentclass{" + template + "}",
            r"\usepackage[utf8]{inputenc}",
            r"\usepackage{amsmath,amssymb}",
            r"\usepackage{graphicx}",
            r"\usepackage[colorlinks=true]{hyperref}",
            "",
            r"\title{" + project_title + "}",
            r"\author{Generated by Auto-Research-DS}",
            r"\date{\today}",
            "",
            r"\begin{document}",
            r"\maketitle",
            "",
        ]

        for sec in sections:
            level = sec.get("level", 1)
            cmd = {1: "section", 2: "subsection", 3: "subsubsection"}.get(level, "section")
            title = sec.get("title", "Untitled")
            content = sec.get("content", "")
            lines.append(f"\\{cmd}{{{title}}}")
            lines.append("")
            # 将 Markdown 内容转为纯文本（简化版）
            text = self._markdown_to_latex(content)
            lines.append(text)
            lines.append("")

        lines.append(r"\end{document}")
        return "\n".join(lines)

    def render_section_preview_tex(self, section_title: str, section_source: str,
                                   project_title: str = "Section Preview") -> str:
        """Wrap one section body in a minimal compilable LaTeX document."""
        return self.render_to_tex(
            project_title=project_title or "Section Preview",
            sections=[{
                "title": section_title or "Section",
                "level": 1,
                "content": section_source or "",
            }],
            template="article",
        )

    def _markdown_to_latex(self, md_text: str) -> str:
        """简化的 Markdown → LaTeX 转换。"""
        text = md_text
        # **bold** → \\textbf{bold}
        text = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', text)
        # *italic* → \\textit{italic}
        text = re.sub(r'\*(.+?)\*', r'\\textit{\1}', text)
        # [text](url) → \\href{url}{text}
        text = re.sub(r'\[(.+?)\]\((.+?)\)', r'\\href{\2}{\1}', text)
        return text

    async def compile_check(self, tex_content: str) -> dict:
        """在 sandbox 中运行 pdflatex 进行编译检查。

        Returns:
            {"success": bool, "errors": list, "warnings": list, "log": str}
        """
        import tempfile
        import subprocess
        import os

        # 创建临时目录
        with tempfile.TemporaryDirectory() as tmpdir:
            tex_path = os.path.join(tmpdir, "document.tex")
            with open(tex_path, "w") as f:
                f.write(tex_content)

            # 编译 (最多重试 3 次)
            errors = []
            warnings = []
            for attempt in range(3):
                try:
                    result = subprocess.run(
                        ["pdflatex", "-interaction=nonstopmode", "-output-directory", tmpdir, tex_path],
                        capture_output=True, text=True, timeout=30,
                    )
                    log = result.stdout + result.stderr

                    # 解析错误和警告
                    for line in log.split("\n"):
                        if line.startswith("!"):
                            errors.append(line.strip())
                        elif "Warning" in line:
                            warnings.append(line.strip())

                    if not errors or attempt == 2:
                        return {
                            "success": len(errors) == 0,
                            "compiler_available": True,
                            "diagnostic_mode": "compile",
                            "errors": errors,
                            "warnings": warnings,
                            "log": log[-2000:],  # 只返回最后 2000 字符
                        }

                    # 自动重试：处理常见问题（如未定义引用需要二次编译）
                    logger.info(f"LaTeX 编译第 {attempt + 1} 次失败，{len(errors)} 个错误，重试中...")

                except FileNotFoundError:
                    return self._fallback_source_check(tex_content)
                except subprocess.TimeoutExpired:
                    return {
                        "success": False,
                        "compiler_available": True,
                        "diagnostic_mode": "compile_timeout",
                        "errors": ["编译超时 (>30s)"],
                        "warnings": warnings,
                        "log": "",
                    }

        return {"success": False, "compiler_available": True, "diagnostic_mode": "compile", "errors": errors, "warnings": warnings, "log": ""}

    def _fallback_source_check(self, tex_content: str) -> dict:
        """Return useful source diagnostics when a TeX compiler is unavailable."""
        errors: list[str] = []
        warnings = ["pdflatex 未安装，已改用源码级检查；安装 TeX Live/MacTeX 后可进行完整编译。"]

        brace_balance = 0
        escaped = False
        for char in tex_content or "":
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == "{":
                brace_balance += 1
            elif char == "}":
                brace_balance -= 1
                if brace_balance < 0:
                    errors.append("检测到多余的右花括号 `}`。")
                    brace_balance = 0
        if brace_balance > 0:
            errors.append(f"检测到 {brace_balance} 个未闭合的左花括号 `{{`。")

        begin_envs = re.findall(r"\\begin\{([^}]+)\}", tex_content or "")
        end_envs = re.findall(r"\\end\{([^}]+)\}", tex_content or "")
        env_stack: list[str] = []
        for env in begin_envs:
            env_stack.append(env)
        for env in end_envs:
            if env in env_stack:
                env_stack.remove(env)
            else:
                errors.append(f"检测到没有对应 begin 的环境结束：\\end{{{env}}}。")
        for env in env_stack:
            errors.append(f"检测到未闭合的 LaTeX 环境：\\begin{{{env}}}。")

        if r"\begin{document}" not in (tex_content or "") or r"\end{document}" not in (tex_content or ""):
            warnings.append("源码级检查未发现完整 document 环境；章节预览会自动包裹最小文档。")

        return {
            "success": len(errors) == 0,
            "compiler_available": False,
            "diagnostic_mode": "source_fallback",
            "errors": errors,
            "warnings": warnings,
            "log": "pdflatex unavailable; source-level fallback checks were used.",
        }


# 全局单例
latex_processor = LatexProcessor()
