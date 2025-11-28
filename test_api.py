"""
测试API接口
"""
import requests
import time

API_BASE = "http://localhost:8000"

print("=" * 60)
print("测试中文播客生成API")
print("=" * 60)

# 1. 测试健康检查
print("\n1. 测试健康检查...")
response = requests.get(f"{API_BASE}/")
print(f"状态码: {response.status_code}")
print(f"响应: {response.json()}")

# 2. 测试获取任务列表
print("\n2. 测试获取任务列表...")
response = requests.get(f"{API_BASE}/api/tasks")
print(f"状态码: {response.status_code}")
tasks = response.json()
print(f"当前任务数: {len(tasks)}")
for task in tasks:
    print(f"  - {task['task_id']}: {task['status']} - {task['message']}")

print("\n" + "=" * 60)
print("API测试完成！")
print("=" * 60)
print("\n访问前端页面: http://localhost:5173")
print("在页面上上传音频文件测试完整流程\n")
