
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import OpenAI, APIConnectionError, AuthenticationError, RateLimitError
from pydantic import BaseModel

# 加载 backend 目录下的 .env 文件
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

# 读取 API Key
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

app = FastAPI(
    title="AI Interviewer",
    description="AI 面试官系统后端服务",
    version="0.3.0"
)

# ==============================
# 1. 数据模型
# ==============================

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


# ==============================
# 2. 系统提示词
# ==============================

SYSTEM_PROMPT = """
你是一名专业、客观、友好的AI技术面试官。

面试背景：
公司：无锡灵泛智能
岗位：技术实习生
面试对象：计算机相关专业的应届生或实习生。

面试要求：

1. 不要预设候选人的专业、技术能力、项目经历等背景。
2. 根据候选人实际提供的信息开展面试。
3. 每次只提出一个主要问题。
4. 根据候选人的回答进行有针对性的追问。
5. 问题应当具有专业性，但难度应结合候选人的实际水平。
6. 保持自然、客观、友好的交流风格。
7. 不要直接给出问题答案，应当通过提问考察候选人。
8. 不要在面试过程中随意中断面试流程。

请始终保持面试官身份。
"""


# ==============================
# 3. 会话存储
# ==============================

# 暂时使用内存字典保存会话
sessions = {}


# ==============================
# 4. 基础接口
# ==============================

@app.get("/")
def home():
    return {
        "message": "AI 面试官系统启动成功！",
        "version": "0.3.0"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# ==============================
# 5. 创建面试会话
# ==============================

@app.post("/session")
def create_session():

    session_id = str(uuid.uuid4())

    sessions[session_id] = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    return {
        "session_id": session_id,
        "message": "面试会话创建成功"
    }


# ==============================
# 6. 多轮对话接口
# ==============================

@app.post("/chat")
def chat(request: ChatRequest):

    if not DEEPSEEK_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="未配置 DEEPSEEK_API_KEY，请检查 .env"
        )

    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="输入内容不能为空"
        )

    # 如果没有提供 session_id，则自动创建新会话
    session_id = request.session_id

    if not session_id:
        session_id = str(uuid.uuid4())

        sessions[session_id] = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

    # 检查会话是否存在
    if session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail="面试会话不存在，请重新创建"
        )

    # 获取当前会话历史
    history = sessions[session_id]

    # 暂存本轮用户消息
    user_message = {
        "role": "user",
        "content": request.message
    }

    # 构建本次请求消息
    messages = history + [user_message]

    try:
        client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )

        response = client.chat.completions.create(
            model="deepseek-flash",
            messages=messages,
            stream=False
        )

        answer = response.choices[0].message.content

        if not answer:
            raise HTTPException(
                status_code=502,
                detail="模型未返回有效内容"
            )

        # 只有模型调用成功后才保存本轮对话
        history.append(user_message)

        history.append({
            "role": "assistant",
            "content": answer
        })

        return {
            "session_id": session_id,
            "question": request.message,
            "answer": answer,
            "history_count": len(history) - 1
        }

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

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"模型调用失败：{str(e)}"
        )


# ==============================
# 7. 删除面试会话
# ==============================

@app.delete("/session/{session_id}")
def delete_session(session_id: str):

    if session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail="面试会话不存在"
        )

    del sessions[session_id]

    return {
        "message": "面试会话已删除",
        "session_id": session_id
    }
