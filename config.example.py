# 中文播客生成系统 - 配置示例
# 使用前请将此文件复制为 config.py 并填入真实的配置信息

# TOS 对象存储配置
TOS_CONFIG = {
    "access_key": "your_tos_access_key",
    "secret_key": "your_tos_secret_key",
    "endpoint": "tos-cn-beijing.volces.com",
    "region": "cn-beijing",
    "bucket_name": "your-bucket-name",
    "folder_prefix": "asr-audio/"
}

# ASR 语音识别配置（火山引擎BigASR）
ASR_CONFIG = {
    "appid": "your_asr_appid",
    "access_token": "your_asr_access_token",
    "cluster": "volcengine_big_asr_common",
    "model_version": "400"
}

# 翻译配置（阿里灵积DashScope）
TRANSLATE_CONFIG = {
    "api_key": "your_dashscope_api_key",
    "model": "qwen-max",
    "system_prompt": """你是一个专业的播客内容翻译和改写专家。请将以下英文播客内容翻译并改写成中文。

要求：
1. 保持对话的自然流畅性，使用口语化表达
2. 适当精简冗余内容，但保留关键信息
3. 使用中文播客的语言风格
4. 输出格式为JSON数组，每个对象包含speaker（说话人，如A、B）和text（对话内容）字段"""
}

# TTS 语音合成配置（火山引擎TTS）
TTS_CONFIG = {
    "appid": "your_tts_appid",
    "access_token": "your_tts_access_token",
    "resource_id": "seed-tts-2.0",  # 或 "volc-tts-1.0"
    "speed_ratio": 1.0,
    "volume_ratio": 1.0,
    "pitch_ratio": 1.0,
    "speaker_map": {
        "A": "zh_female_shuangkuaisisi_moon_bigtts",
        "B": "zh_male_wennuanahu_moon_bigtts"
    }
}

# 存储配置
STORAGE_CONFIG = {
    "upload_dir": "uploads",
    "output_dir": "output",
    "temp_dir": "temp"
}
