import requests
import json

# --- 配置 ---
# 警告：请使用您新生成的密钥，不要在代码中硬编码。
# 最好使用环境变量来存储您的密钥。
API_KEY = "sk-2df01e5ac46949ae8f7c97325c3ac995"  # 替换为您新生成的有效密钥
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_NAME = "deepseek-v3"

# --- API 端点 ---
# 兼容 OpenAI 的聊天补全接口
endpoint = f"{BASE_URL}/chat/completions"

# --- 请求头 ---
# 包含您的 API 密钥
headers = {
    "Content-Type": "application/json",
    "Authorization": f"{API_KEY}"
}

system_prompt = """你是一个专业的AI领域播客翻译和格式转换助手。请严格按照以下要求处理输入文本：

## 任务要求：

1. **翻译规则**：
   - 将英文内容翻译成流畅、专业的中文
   - AI领域的专业术语保持英文原文（如：multi-clouding, Cloud Code, API, token等）
   - 公司名称保持英文（如：Anthropic, OpenAI等）
   - 人名保持英文（如：Alex, Cat等）
   - 保持口语化风格，使其适合语音播报

2. **说话人合并规则**：
   - [Speaker 1] 保持为"发言者1"
   - [Speaker 2]、[Speaker 3]、[Speaker 4]等所有其他说话人统一转换为"发言者2"
   -  同一个说话人连续多段内容合并成一段。


3. **输出格式要求**：
输出为严格的JSON数组格式，每个对话段包含以下字段：
```json
[
  {
    "speaker": "发言者1",
    "text": "你好，很高兴认识你！"
  },
  {
    "speaker": "发言者2",
    "text": "你好，我也很高兴认识你！"
  }
]
```"""

# --- 请求体 (Payload) ---
# 包含模型名称和对话消息
data = {
    "model": MODEL_NAME,
    "messages": [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": "These developers tend to like to run multiple cloud sessions at once, and they've started calling this multi-clouding."
        }
    ],
    "stream": False  # 设置为 False 来接收完整的非流式响应
}

# --- 发送 POST 请求 ---
try:
    response = requests.post(endpoint, headers=headers, data=json.dumps(data))

    # 检查是否有 HTTP 错误
    response.raise_for_status()

    # 解析 JSON 响应
    response_json = response.json()

    # 打印完整的 JSON 响应（用于调试）
    print("--- 完整响应 ---")
    print(json.dumps(response_json, indent=2, ensure_ascii=False))

    # 提取并打印助手的回复
    if "choices" in response_json and len(response_json["choices"]) > 0:
        assistant_message = response_json["choices"][0]["message"]["content"]
        print("\n--- 助手回复 ---")
        print(assistant_message)

except requests.exceptions.HTTPError as http_err:
    print(f"HTTP 错误: {http_err}")
    # 打印来自 API 的错误详情
    print(f"响应内容: {response.text}")
except Exception as err:
    print(f"发生其他错误: {err}")