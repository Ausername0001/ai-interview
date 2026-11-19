
# backend/interview_manager.py

from prompt import STAGE_PROMPTS


# ==========================================
# 1. 定义面试阶段
# ==========================================

STAGE_ORDER = [
    "introduction",
    "basic_knowledge",
    "project",
    "scenario",
    "ability",
    "candidate_questions",
    "completed"
]


STAGE_NAMES = {
    "introduction": "开场与自我介绍",
    "basic_knowledge": "计算机与编程基础",
    "project": "项目经历深挖",
    "scenario": "岗位相关技术与场景分析",
    "ability": "学习能力、沟通协作与实习安排",
    "candidate_questions": "候选人反问",
    "completed": "面试结束"
}


# ==========================================
# 2. 获取阶段名称
# ==========================================

def get_stage_name(stage: str) -> str:

    return STAGE_NAMES.get(stage, "未知阶段")


# ==========================================
# 3. 获取阶段提示词
# ==========================================

def get_stage_prompt(stage: str) -> str:

    return STAGE_PROMPTS.get(
        stage,
        STAGE_PROMPTS["completed"]
    )


# ==========================================
# 4. 获取下一个阶段
# ==========================================

def get_next_stage(stage: str) -> str:

    if stage not in STAGE_ORDER:
        return "completed"

    index = STAGE_ORDER.index(stage)

    if index >= len(STAGE_ORDER) - 1:
        return "completed"

    return STAGE_ORDER[index + 1]


# ==========================================
# 5. 判断阶段转换是否合法
# ==========================================

def can_advance(stage: str) -> bool:

    return (
        stage in STAGE_ORDER
        and stage != "completed"
    )


# ==========================================
# 6. 创建会话
# ==========================================

def create_interview_session(
    session_id: str,
    resume_text: str
):

    return {

        "session_id": session_id,

        # 候选人简历
        "resume_text": resume_text,

        # 当前面试阶段
        "stage": "introduction",

        # 完整对话记录
        "history": [],

        # 面试是否结束
        "completed": False,

        # 面试总回答轮数
        "total_turns": 0,

        # 面试报告
        "summary": None

    }


# ==========================================
# 7. 构建当前轮次的系统提示词
# ==========================================

def build_system_prompt(
    session,
    system_prompt: str
):

    stage = session["stage"]

    stage_prompt = get_stage_prompt(stage)

    next_stage = get_next_stage(stage)

    return f"""
{system_prompt}

====================================

【本次候选人简历】

{session["resume_text"]}

====================================

【当前面试状态】

当前阶段：{get_stage_name(stage)}

当前阶段标识：{stage}

下一阶段：{get_stage_name(next_stage)}

当前阶段具体要求：

{stage_prompt}

====================================

【面试历史】

请结合已经发生的全部对话进行判断。

不要重复已经充分考察的问题。
不要脱离简历随机提问。
根据候选人的实际回答决定是否追问。

====================================

【阶段控制规则】

你需要判断当前阶段是否已经充分考察。

如果还需要了解当前阶段内容：
action = continue

如果当前阶段已经充分考察：
action = advance

如果候选人明确要求结束面试：
action = finish

如果候选人已经完成反问，并明确表示没有其他问题：
action = finish

如果当前阶段考察充分，但后续阶段尚未完成：
action = advance

不得跳过中间阶段。
不得擅自改变面试阶段顺序。

只有在候选人明确表达结束意愿，
或者所有面试环节完成后，才允许 finish。

如果候选人暂时不会回答：
可以询问其初步思路，或者自然进入下一个问题。
不能因为一次回答不会就直接结束整个面试。

如果当前处于候选人反问阶段：
候选人提出具体问题时，应先回答问题并继续交流；
只有候选人明确表示没有其他问题时才结束面试。

====================================


【输出要求】

【输出要求】

必须只输出一个合法的JSON对象。
不得输出Markdown代码块、解释文字或其他内容。

严格按照以下结构输出：

{{
    "action": "continue",
    "reply": "面试官对候选人说的话"
}}

字段要求：

1. action：只能是以下三个字符串之一：
   - continue：继续当前面试阶段。
   - advance：当前阶段考察充分，进入下一阶段。
   - finish：结束整个面试。

2. reply：
   - 必须是非空字符串。
   - 使用自然、专业、友好的中文。
   - 每轮只提出一个主要问题。
   - 必须与当前面试阶段和候选人回答相关。

注意：

- 上述JSON仅为结构示例，action应根据实际面试情况动态判断。
- 必须同时包含action和reply。
- 不得添加其他字段。
- 不得遗漏字段。
- 确保JSON符合标准语法。

"""
