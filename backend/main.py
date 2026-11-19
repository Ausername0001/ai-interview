
# backend/main.py

import os
import uuid
import json
import re

from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File
)
from openai import (
    OpenAI,
    APIConnectionError,
    AuthenticationError,
    RateLimitError
)
from pydantic import BaseModel, Field

from prompt import SYSTEM_PROMPT, SUMMARY_PROMPT

from resume_parser import parse_resume

from interview_manager import (
    STAGE_ORDER,
    STAGE_NAMES,
    get_next_stage,
    build_system_prompt,
    create_interview_session
)

from database import (
    init_db,
    save_session,
    get_session_from_db,
    get_all_sessions,
    delete_session_from_db
)

# ==========================================
# 1. 初始化配置
# ==========================================

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

app = FastAPI(
    title="AI Interviewer",
    description="无锡灵泛智能 AI 技术面试官",
    version="1.0.0"
)

@app.on_event("startup")
def startup_event():
    init_db()
    print("SQLite 数据库初始化成功")

# ==========================================
# 2. 数据模型
# ==========================================

class SessionRequest(BaseModel):

    resume_text: str = Field(
        min_length=1,
        max_length=20000
    )


class ChatRequest(BaseModel):

    session_id: str

    message: str = Field(
        min_length=1,
        max_length=10000
    )


# ==========================================
# 3. 会话存储
# ==========================================

sessions = {}

def load_session(session_id):
    """
    优先从内存读取会话。
    内存不存在时，从 SQLite 数据库恢复。
    """

    session = sessions.get(session_id)

    if session is not None:
        return session

    session = get_session_from_db(session_id)

    if session is not None:
        sessions[session_id] = session

    return session

# ==========================================
# 4. 初始化 DeepSeek 客户端
# ==========================================

def get_client():

    if not DEEPSEEK_API_KEY:

        raise HTTPException(
            status_code=500,
            detail="未配置 DEEPSEEK_API_KEY，请检查 backend/.env"
        )

    return OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com"
    )


# ==========================================
# 5. 通用模型调用
# ==========================================


def call_deepseek(messages, json_mode=False):

    client = get_client()

    params = {
        "model": "deepseek-flash",
        "messages": messages,
        "stream": False,
        "max_tokens": 20480
    }

    # 启用 JSON 模式
    if json_mode:
        params["response_format"] = {
            "type": "json_object"
        }

    try:
        response = client.chat.completions.create(**params)

        choice = response.choices[0]
        answer = choice.message.content

        print("\n========== DeepSeek API 响应 ==========")
        print("JSON模式:", json_mode)
        print("Finish reason:", choice.finish_reason)
        print("Usage:", response.usage)
        print("返回内容:", repr(answer))
        print("=======================================\n")

        # 检查返回内容
        if answer is None or not answer.strip():
            raise HTTPException(
                status_code=502,
                detail="DeepSeek 模型返回内容为空，请重试"
            )

        # 如果输出达到 Token 上限，记录警告
        if choice.finish_reason == "length":
            print("警告：模型输出达到 Token 上限，内容可能不完整")

        return answer.strip()

    except AuthenticationError:
        raise HTTPException(
            status_code=401,
            detail="DeepSeek API Key 无效"
        )

    except RateLimitError:
        raise HTTPException(
            status_code=429,
            detail="API 请求频率受限，请稍后重试"
        )

    except APIConnectionError:
        raise HTTPException(
            status_code=503,
            detail="无法连接 DeepSeek API，请检查网络"
        )

# ==========================================
# 6. 生成面试回复
# ==========================================



def generate_interview_reply(session):

    system_prompt = build_system_prompt(
        session,
        SYSTEM_PROMPT
    )

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    messages.extend(session["history"])

    # 使用 JSON 模式调用模型
    result = call_deepseek(
        messages,
        json_mode=True
    )

    print("\n========== DeepSeek 原始响应 ==========")
    print("当前阶段:", session["stage"])
    print("返回内容:", repr(result))
    print("=======================================\n")

    # 解析 JSON
    try:
        data = json.loads(result)

    except json.JSONDecodeError as e:

        print("JSON 解析失败:", str(e))

        raise HTTPException(
            status_code=502,
            detail="模型返回的 JSON 格式异常，请重试本轮面试"
        )

    # 检查 JSON 数据类型
    if not isinstance(data, dict):

        raise HTTPException(
            status_code=502,
            detail="模型返回的数据不是 JSON 对象"
        )

    # 提取字段
    action = data.get("action")
    reply = data.get("reply")

    # 检查 action 是否合法
    allowed_actions = {
        "continue",
        "advance",
        "finish"
    }

    if action not in allowed_actions:

        raise HTTPException(
            status_code=502,
            detail="模型返回了无效的面试阶段指令"
        )

    # 检查 reply 是否有效
    if not isinstance(reply, str) or not reply.strip():

        raise HTTPException(
            status_code=502,
            detail="模型返回的面试回复为空或格式错误"
        )

    reply = reply.strip()

    print("解析后的 action:", action)
    print("解析后的 reply:", reply)

    return {
        "action": action,
        "reply": reply
    }



# ==========================================
# 7. 生成面试总结
# ==========================================


def generate_summary(session):

    conversation = "\n\n".join(
        [
            (
                "AI面试官："
                if item["role"] == "assistant"
                else "候选人："
            ) + item["content"]
            for item in session["history"]
        ]
    )

    messages = [
        {
            "role": "system",
            "content": SUMMARY_PROMPT
        },
        {
            "role": "user",
            "content": (
                "以下是候选人的原始简历：\n\n"
                + session["resume_text"]
                + "\n\n以下是完整面试记录：\n\n"
                + conversation
                + "\n\n"
                + "请严格按照系统提示词中的JSON结构生成报告。"
            )
        }
    ]

    result = call_deepseek(
        messages,
        json_mode=True
    )

    print("\n========== 面试报告原始响应 ==========")
    print(repr(result))
    print("=======================================\n")

    try:
        summary = json.loads(result)

        # 检查关键字段，避免不完整报告进入前端
        required_fields = [
            "candidate_info",
            "interview_overview",
            "content_summary",
            "scores",
            "strengths",
            "improvements",
            "job_match",
            "recommendation",
            "manual_review"
        ]

        for field in required_fields:
            if field not in summary:
                raise ValueError(f"报告缺少字段：{field}")

        print("面试报告JSON解析成功")

        return summary

    except (json.JSONDecodeError, ValueError, TypeError) as e:

        print("面试报告解析失败:", str(e))

        raise HTTPException(
            status_code=502,
            detail="面试报告生成失败，请重新生成"
        )



# ==========================================
# 8. 首页
# ==========================================

@app.get("/")
def home():

    return {
        "message": "AI 面试官系统启动成功",
        "version": "1.0.0"
    }


# ==========================================
# 9. 健康检查
# ==========================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy"
    }


# ==========================================
# 10. 上传并解析简历
# ==========================================

@app.post("/resume/parse")
async def upload_resume(file: UploadFile = File(...)):

    try:

        filename = file.filename or ""

        file_bytes = await file.read()

        resume_text = parse_resume(
            filename,
            file_bytes
        )

        return {
            "filename": filename,
            "resume_text": resume_text,
            "length": len(resume_text),
            "message": "简历解析成功"
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"简历解析失败：{str(e)}"
        )

    finally:

        await file.close()


# ==========================================
# 11. 创建面试会话
# ==========================================

@app.post("/session")
def create_session(request: SessionRequest):

    resume_text = request.resume_text.strip()

    if not resume_text:

        raise HTTPException(
            status_code=400,
            detail="请先提供候选人简历"
        )

    session_id = str(uuid.uuid4())

    session = create_interview_session(
        session_id,
        resume_text
    )

    # 记录创建时间
    session["started_at"] = datetime.now().isoformat()

    # 固定开场话术
    opening = (
        "你好，欢迎参加无锡灵泛智能技术实习生岗位的初步面试。"
        "我会结合你的简历，了解你的专业基础、技术实践和解决问题的思路。"
        "面试过程中我们会以交流为主，我会根据你的回答进一步提问。"
        "首先，请你用2到3分钟做一个自我介绍，"
        "可以重点介绍你的专业背景、熟悉的技术，"
        "以及一段你认为最能体现自己实践能力的经历。"
    )

    session["history"].append({
        "role": "assistant",
        "content": opening
    })

    sessions[session_id] = session

    save_session(session)

    return {
        "session_id": session_id,
        "stage": session["stage"],
        "stage_name": STAGE_NAMES[session["stage"]],
        "answer": opening,
        "message": "面试创建成功"
    }


# ==========================================
# 12. 面试对话接口
# ==========================================

@app.post("/chat")
def chat(request: ChatRequest):

    # 优先读取内存；如果没有，则从数据库恢复
    session = load_session(request.session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="面试会话不存在"
        )

    if session["completed"]:
        raise HTTPException(
            status_code=400,
            detail="本次面试已经结束"
        )

    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="输入内容不能为空"
        )

    # 保存本轮开始前的完整状态
    old_history_length = len(session["history"])
    old_stage = session["stage"]
    old_turns = session["total_turns"]
    old_completed = session["completed"]
    old_summary = session["summary"]
    old_summary_error = session.get("summary_error")

    try:

        # 保存候选人回答
        session["history"].append({
            "role": "user",
            "content": message
        })

        session["total_turns"] += 1

        # 调用模型生成面试回复
        result = generate_interview_reply(session)

        action = result["action"]
        answer = result["reply"]

        # 根据模型判断调整面试阶段
        if action == "advance":

            if session["stage"] == "candidate_questions":

                session["stage"] = "completed"
                session["completed"] = True

            else:

                session["stage"] = get_next_stage(
                    session["stage"]
                )

                if session["stage"] == "completed":
                    session["completed"] = True

        elif action == "finish":

            session["stage"] = "completed"
            session["completed"] = True

        # 保存 AI 回复
        session["history"].append({
            "role": "assistant",
            "content": answer
        })

        # 面试结束后生成报告
        if session["completed"]:

            try:
                session["summary"] = generate_summary(session)
                session.pop("summary_error", None)

            except Exception as e:
                print("面试报告生成失败:", str(e))
                session["summary_error"] = str(e)

        # 将最新会话状态写入数据库
        save_session(session)

        return {
            "session_id": request.session_id,
            "stage": session["stage"],
            "stage_name": STAGE_NAMES[session["stage"]],
            "action": action,
            "answer": answer,
            "total_turns": session["total_turns"],
            "completed": session["completed"],
            "summary": session["summary"]
        }

    except Exception:

        # 恢复到本轮开始前的状态
        session["history"] = session["history"][:old_history_length]

        session["stage"] = old_stage
        session["total_turns"] = old_turns
        session["completed"] = old_completed
        session["summary"] = old_summary

        if old_summary_error is None:
            session.pop("summary_error", None)
        else:
            session["summary_error"] = old_summary_error

        raise

# ==========================================
# 获取历史面试记录
# ==========================================

@app.get("/sessions")
def list_sessions():

    records = get_all_sessions()

    return {
        "total": len(records),
        "sessions": records
    }

# ==========================================
# 13. 查询面试状态
# ==========================================


@app.get("/session/{session_id}")
def get_session(session_id: str):

    session = load_session(session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="面试会话不存在"
        )

    return {
        "session_id": session_id,
        "resume_text": session["resume_text"],
        "history": session["history"],
        "stage": session["stage"],
        "stage_name": STAGE_NAMES[session["stage"]],
        "total_turns": session["total_turns"],
        "completed": session["completed"],
        "started_at": session["started_at"],
        "summary": session["summary"]
    }


# ==========================================
# 14. 获取面试总结
# ==========================================

@app.get("/session/{session_id}/summary")
def get_summary(session_id: str):

    session = load_session(session_id)

    if session is None:

        raise HTTPException(
            status_code=404,
            detail="面试会话不存在"
        )

    if not session["completed"]:

        raise HTTPException(
            status_code=409,
            detail="面试尚未结束，暂时无法生成总结"
        )

    if not session.get("summary"):

        raise HTTPException(
            status_code=503,
            detail="面试已结束，但总结生成失败，请稍后重试"
        )

    return {
        "session_id": session_id,
        "summary": session["summary"]
    }


# ==========================================
# 15. 删除面试会话
# ==========================================

@app.delete("/session/{session_id}")
def delete_session(session_id: str):

    # 先检查数据库和内存中是否存在记录
    session = load_session(session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="面试会话不存在"
        )

    # 删除数据库记录
    delete_session_from_db(session_id)

    # 删除内存缓存
    sessions.pop(session_id, None)

    return {
        "message": "面试会话删除成功"
    }