"""
测试新增的API接口
"""
import requests

API_BASE = "http://localhost:8000"

print("=" * 60)
print("测试新增API")
print("=" * 60)

# 1. 测试获取配置
print("\n1. 测试获取配置接口...")
try:
    response = requests.get(f"{API_BASE}/api/config")
    if response.status_code == 200:
        config = response.json()
        print("✅ 配置获取成功")
        print(f"  ASR AppID: {config['asr']['appid']}")
        print(f"  TTS语速: {config['tts']['speech_rate']}")
    else:
        print(f"❌ 失败: {response.status_code}")
except Exception as e:
    print(f"❌ 错误: {e}")

# 2. 测试获取任务列表（查看是否有任务）
print("\n2. 获取任务列表...")
try:
    response = requests.get(f"{API_BASE}/api/tasks")
    if response.status_code == 200:
        tasks = response.json()
        print(f"✅ 当前有 {len(tasks)} 个任务")
        if tasks:
            task_id = tasks[0]['task_id']
            print(f"  第一个任务ID: {task_id}")
            
            # 3. 测试获取任务详情
            print("\n3. 测试获取任务详情...")
            detail_response = requests.get(f"{API_BASE}/api/tasks/{task_id}/details")
            if detail_response.status_code == 200:
                details = detail_response.json()
                print("✅ 任务详情获取成功")
                if details.get('asr_result'):
                    print("  ✓ 包含ASR结果")
                if details.get('dialogues'):
                    print(f"  ✓ 包含翻译结果（{len(details['dialogues'])}段对话）")
            else:
                print(f"❌ 失败: {detail_response.status_code}")
except Exception as e:
    print(f"❌ 错误: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
