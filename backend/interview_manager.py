
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

如果候选人明确要求结束面试，或者已经完成反问：
action = finish

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

必须输出一个JSON对象，不能使用Markdown代码块。

格式：

{{
    "action": "continue",
    "reply": "面试官回复内容"
}}

action只能是以下三种：

continue：留在当前阶段，继续提问或交流。
advance：当前阶段完成，进入下一阶段。
finish：结束面试。

reply必须是自然、简洁的中文。

每次回复只能包含一个主要问题。

如果action为advance：
reply应当自然衔接下一阶段，并提出下一阶段的第一个问题。

如果action为finish：
reply使用面试结束话术，不再提出任何问题。

不要在reply中输出评分、评价、排名或录用建议。
"""
