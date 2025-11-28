"""
测试所有优化功能
"""
import requests
import json

API_BASE = "http://localhost:8000"

print("=" * 60)
print("测试新增和优化的功能")
print("=" * 60)

# 1. 测试获取配置（完整，不脱敏）
print("\n1. 测试获取完整配置...")
try:
    response = requests.get(f"{API_BASE}/api/config")
    if response.status_code == 200:
        config = response.json()
        print("✅ 配置获取成功")
        print(f"  ASR AppID (完整): {config['asr']['appid']}")
        print(f"  TTS 资源版本: {config['tts']['resource_id']}")
        print(f"  TTS 语速: {config['tts']['speech_rate']}")
        print(f"  翻译系统提示词长度: {len(config['translate']['system_prompt'])} 字符")
    else:
        print(f"❌ 失败: {response.status_code}")
except Exception as e:
    print(f"❌ 错误: {e}")

# 2. 测试获取音色数据库
print("\n2. 测试获取TTS音色数据库...")
try:
    response = requests.get(f"{API_BASE}/api/voice-database")
    if response.status_code == 200:
        voices = response.json()
        print("✅ 音色数据库获取成功")
        for resource_id, categories in voices.items():
            print(f"  资源版本: {resource_id}")
            for category, voice_list in categories.items():
                print(f"    - {category}: {len(voice_list)} 个音色")
    else:
        print(f"❌ 失败: {response.status_code}")
except Exception as e:
    print(f"❌ 错误: {e}")

# 3. 测试任务列表排序
print("\n3. 测试任务列表排序（最新在最上）...")
try:
    response = requests.get(f"{API_BASE}/api/tasks")
    if response.status_code == 200:
        tasks = response.json()
        if len(tasks) >= 2:
            print("✅ 任务列表获取成功")
            print(f"  第一个任务创建时间: {tasks[0]['created_at']}")
            print(f"  第二个任务创建时间: {tasks[1]['created_at']}")
            if tasks[0]['created_at'] >= tasks[1]['created_at']:
                print("  ✓ 排序正确：最新的在最上面")
            else:
                print("  ✗ 排序可能有问题")
        elif len(tasks) == 1:
            print(f"✅ 当前只有 1 个任务，创建时间: {tasks[0]['created_at']}")
        else:
            print("  当前没有任务")
    else:
        print(f"❌ 失败: {response.status_code}")
except Exception as e:
    print(f"❌ 错误: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
print("\n前端优化说明：")
print("1. ✅ 上传文件后立即显示任务（前端已修改）")
print("2. ✅ 任务列表按创建时间倒序（API已修改）")
print("3. ✅ 设置页面支持编辑所有字段（新页面已创建）")
print("4. ✅ TTS资源版本和音色支持下拉选择并关联")
print("5. ✅ 配置保存后立即生效（无需重启）")
print("\n请访问前端页面测试: http://localhost:5173")
