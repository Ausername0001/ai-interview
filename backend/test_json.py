
import json

from main import get_client


def test_deepseek_json():

    client = get_client()

    messages = [
        {
            "role": "system",
            "content": """
                       你是一名专业的AI技术面试官。

你正在进行一场计算机专业技术实习生面试。

请根据候选人的回答判断是否需要继续当前阶段，
或者进入下一个面试阶段。

你必须严格输出JSON对象，包含两个字段：
action：只能是continue、advance、finish之一。
reply：面试官对候选人说的话。

不要输出Markdown代码块，不要输出JSON以外的内容。
                       """
        },
        {
            "role": "user",
            "content": """
                候选人回答：
我主要学习过Python和Java，了解面向对象编程，
并且完成过一个简单的Web开发项目。

请生成下一轮面试官回复。
            """
        }
    ]

    print("=" * 50)
    print("开始测试 DeepSeek JSON Mode")
    print("=" * 50)

    try:
        response = client.chat.completions.create(
            model="deepseek-flash",
            messages=messages,
            response_format={"type": "json_object"},
            stream=False,
            max_tokens=16384
        )

        choice = response.choices[0]

        print("\n1. API 请求成功")
        print("usage:", response.usage)
        print("finish_reason:", choice.finish_reason)

        content = choice.message.content

        print("\n2. 模型原始返回内容：")
        print(repr(content))

        if not content:
            print("\n测试结果：模型返回了空内容")
            return

        print("\n3. 开始解析 JSON")

        try:
            data = json.loads(content)

            print("JSON 解析成功！")
            print("解析结果：", data)

            print("\n4. 字段检查")
            print("action:", data.get("action"))
            print("reply:", data.get("reply"))
            print("score:", data.get("score"))

            print("\n最终结果：JSON 测试通过")

        except json.JSONDecodeError as e:
            print("\nJSON 解析失败！")
            print("错误信息：", e)
            print("最终结果：模型返回的内容不是合法 JSON")

    except Exception as e:
        print("\nAPI 请求失败！")
        print("异常类型：", type(e).__name__)
        print("错误信息：", str(e))


if __name__ == "__main__":
    test_deepseek_json()
