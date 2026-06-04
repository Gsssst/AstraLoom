"""申请书助手服务 — 参考 eseckel/ai-for-grant-writing + NSFC 模板。"""

import logging
from app.services.llm import llm_service
from app.services.rag_service import RAGService
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# 国自然申请书标准章节
NSFC_SECTIONS = {
    "立项依据": "包括研究意义、国内外研究现状分析，附主要参考文献",
    "研究内容": "本项目的研究内容、研究目标，以及拟解决的关键科学问题",
    "研究方案": "拟采取的研究方案及可行性分析",
    "特色创新": "本项目的特色与创新之处",
    "预期成果": "预期研究成果及考核指标",
    "研究基础": "申请人的研究基础与工作条件",
}


class GrantService:
    """基金申请书辅助写作服务。"""

    def __init__(self, session: AsyncSession = None):
        self.session = session

    async def write_section(
        self,
        section: str,
        topic: str,
        background: str = "",
        previous_content: str = "",
    ) -> str:
        """撰写申请书的一个章节（参考 eseckel prompt 模板）。"""

        section_guide = NSFC_SECTIONS.get(section, "")

        prompt = f"""## 角色
你是一位具有丰富国家自然科学基金申请和评审经验的资深教授，曾多次获得 NSFC 面上/重点项目资助，担任过 NSFC 评审专家。

## 任务
撰写 NSFC 申请书的 **{section}** 部分。

## 项目基本信息
**项目主题**: {topic}
**项目背景**: {background or '待补充'}

{f"**前文已写内容**: {previous_content[:500]}" if previous_content else ""}

## 该章节要求
{section_guide}

{self._get_section_specific_guide(section)}

## 写作原则（参考 NSF/NIH 基金写作十大原则）
1. 清晰具体：避免模糊表述，用具体数据和事实支撑论点
2. 逻辑严密：从问题→方法→预期结果形成完整逻辑链
3. 突出创新：明确指出与现有工作的本质区别
4. 可行可信：技术路线具体可操作，不能空泛
5. 语言规范：使用学术书面语，避免口语化

## 输出格式
直接输出该章节的完整内容，不要加「第X章」等编号，不要输出解释性文字。
字数控制在 800-1500 字的学术写作范围。
"""
        response = await llm_service.chat(
            messages=[
                {"role": "system", "content": "你是一位 NSFC 资深评审专家和申请者，擅长撰写高质量基金申请书。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=3072,
        )
        return response

    def _get_section_specific_guide(self, section: str) -> str:
        """各章节的具体写作指导。"""
        guides = {
            "立项依据": """## 写作结构
1. **研究意义**（200-300字）：说明本研究对学科发展/国家需求的重大意义
2. **国内外研究现状**（400-600字）：分主题梳理，不是简单罗列，要指出现有工作的不足
3. **本项目切入点**（100-200字）：基于以上分析，明确本项目要解决的科学问题""",

            "研究内容": """## 写作结构
1. **总体研究目标**（100-150字）：一句话概括
2. **研究内容1/2/3**（每项200-300字）：每项内容说明做什么、为什么做、怎么做
3. **拟解决的关键科学问题**（200-300字）：列出2-3个关键科学问题，说明为什么是"关键"的""",

            "研究方案": """## 写作结构
1. **总体技术路线**（150-200字）：概括性描述
2. **具体研究方案**（400-600字）：按研究内容分点描述具体方法、实验设计
3. **可行性分析**（200-300字）：从理论基础、技术积累、前期工作等方面论证""",

            "特色创新": """## 写作结构
列出 3-4 个创新点，每个创新点：
1. **创新点标题**（10-15字）
2. **创新内容**（80-120字）：与现有方法的本质区别
3. **预期贡献**（30-50字）：该创新带来的价值""",

            "预期成果": """## 写作结构
1. 学术成果（论文、专利等）
2. 人才培养（研究生培养等）
3. 社会/经济效益（如有）
每项成果量化具体指标""",

            "研究基础": """## 写作结构
1. 申请人前期相关工作积累
2. 已取得的相关成果（论文、专利、项目）
3. 实验条件和工作环境""",
        }
        return guides.get(section, "")

    async def review_section(
        self,
        section: str,
        content: str,
        topic: str = "",
    ) -> str:
        """模拟 NSFC 评审专家审阅申请书章节（参考 NSFC 评审模拟 Prompt）。"""
        prompt = f"""## 角色
你是一位经验丰富的 NSFC 评审专家，正在审阅一份申请书。

## 任务
对以下「{section}」章节进行详细审阅，指出优点、问题和改进建议。

## 项目主题
{topic}

## 申请书内容
{content}

## 评审维度
1. **科学性**: 研究问题是否有科学价值？论证是否充分？
2. **创新性**: 是否有真正的创新？与现有工作的区别是否明确？
3. **可行性**: 技术路线是否具体可操作？资源条件是否满足？
4. **表达质量**: 语言是否清晰？逻辑是否连贯？

## 输出格式
按以下结构输出：
### ✅ 优点
- （逐条列出，每条 1-2 句）

### ⚠️ 问题与不足
- （逐条列出，指出具体哪句话/哪个论点有问题，并说明原因）

### 📝 改进建议
- （给出具体可操作的修改建议，不要空泛的"建议补充"）

### 📊 综合评分
- 科学性: X/10
- 创新性: X/10
- 可行性: X/10
- 表达质量: X/10
"""
        response = await llm_service.chat(
            messages=[
                {"role": "system", "content": "你是一位严格但公正的 NSFC 评审专家。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2048,
        )
        return response

    async def extract_innovation_points(
        self,
        topic: str,
        background: str,
        methods: str,
    ) -> str:
        """从项目描述中提炼核心创新点（参考 NSFC 创新点提炼模板）。"""
        prompt = f"""## 角色
你是一位擅长提炼科学问题创新点的 NSFC 评审专家。

## 任务
基于以下项目信息，提炼出 3 个核心创新点。

## 项目主题
{topic}

## 研究背景与问题
{background or '无'}

## 拟采用方法
{methods or '无'}

## 要求
每个创新点按以下格式（不超过 300 字/点）：
- **创新点 X**: [10-15字标题]
  - **与现有工作区别**: [明确指出不同之处]
  - **创新本质**: [为什么这是新的一一理论突破？方法创新？问题新定义？]
  - **预期价值**: [该创新能带来什么学术/应用价值]

请直接输出 3 个创新点，不要其他内容。
"""
        response = await llm_service.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=2048,
        )
        return response

    async def polish_grant_text(self, text: str) -> str:
        """润色申请书文本（参考 gpt_academic 润色 + eseckel clarity prompt）。"""
        prompt = f"""## 角色
你是 NSFC 申请书的语言编辑专家，专门帮助非母语写作者提升学术表达质量。

## 任务
润色以下申请书文本，提升其学术性和说服力。

## 规则
1. 修正语法错误和不自然的表达
2. 将口语化/模糊表达改为精确的学术语言
3. 增强说服力（但要基于事实，不夸大）
4. 保持原意和技术术语不变
5. 改善句子间的逻辑衔接

## 原文
{text}

## 输出
直接输出润色后的文本，不要解释。
"""
        response = await llm_service.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=2048,
        )
        return response
