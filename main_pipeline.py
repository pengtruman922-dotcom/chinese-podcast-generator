"""
主流程脚本 - 串联ASR、翻译、TTS三个阶段
使用方法：
    python main_pipeline.py <音频文件路径或URL>
    
示例：
    python main_pipeline.py https://example.com/audio.mp3
    python main_pipeline.py uploads/test.mp3
"""

import sys
import os
import asyncio
import json
from datetime import datetime
from pathlib import Path

from config import ASR_CONFIG, TRANSLATE_CONFIG, TTS_CONFIG, STORAGE_CONFIG, TOS_CONFIG
from utils import ASRClient, TranslateClient, TTSClient, TOSUploader


def ensure_dirs():
    """确保必要的目录存在"""
    for dir_path in [STORAGE_CONFIG["upload_dir"], 
                     STORAGE_CONFIG["output_dir"], 
                     STORAGE_CONFIG["temp_dir"]]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)


def validate_config():
    """验证配置是否完整"""
    errors = []
    
    if not ASR_CONFIG.get("appid") or not ASR_CONFIG.get("access_token"):
        errors.append("ASR配置缺失: 请在config.py中填写appid和access_token，或设置环境变量VOLC_ASR_APPID和VOLC_ASR_TOKEN")
    
    if not TRANSLATE_CONFIG.get("api_key"):
        errors.append("翻译配置缺失: 请在config.py中填写api_key，或设置环境变量DASHSCOPE_API_KEY")
    
    if not TTS_CONFIG.get("appid") or not TTS_CONFIG.get("access_token"):
        errors.append("TTS配置缺失: 请在config.py中填写appid和access_token，或设置环境变量VOLC_TTS_APPID和VOLC_TTS_TOKEN")
    
    if errors:
        print("❌ 配置错误:")
        for err in errors:
            print(f"  - {err}")
        return False
    
    return True


def save_intermediate_result(data: dict, filename: str):
    """保存中间结果到temp目录"""
    temp_dir = STORAGE_CONFIG["temp_dir"]
    filepath = os.path.join(temp_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[保存] 中间结果已保存: {filepath}")


def run_pipeline(audio_path: str):
    """
    运行完整流程
    
    Args:
        audio_path: 音频文件路径或URL
    """
    print("=" * 60)
    print("中文播客生成流程启动")
    print("=" * 60)
    print(f"输入文件: {audio_path}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    tos_object_key = None  # 记录TOS上传的对象键，用于清理
    
    try:
        # 处理本地文件：上传到TOS
        if not audio_path.startswith(('http://', 'https://')):
            print("\n" + "=" * 60)
            print("阶段 0/3: 本地文件上传到TOS")
            print("=" * 60)
            
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"文件不存在: {audio_path}")
            
            # 验证TOS配置
            if not TOS_CONFIG.get("access_key") or not TOS_CONFIG.get("secret_key"):
                raise Exception("未配置TOS凭证，请在config.py中填写access_key和secret_key，或设置环境变量VOLC_TOS_ACCESS_KEY和VOLC_TOS_SECRET_KEY")
            
            if not TOS_CONFIG.get("bucket_name"):
                raise Exception("未配置TOS Bucket，请在config.py的TOS_CONFIG中填写bucket_name")
            
            # 上传文件
            uploader = TOSUploader(TOS_CONFIG)
            audio_url = uploader.upload_file(audio_path)
            
            # 提取对象键用于后续清理
            tos_object_key = audio_url.split('/')[-1]
        else:
            audio_url = audio_path
            print(f"\n[信息] 使用公网URL: {audio_url}")
        # ==========================================
        # 阶段1: ASR识别
        # ==========================================
        print("\n" + "=" * 60)
        print("阶段 1/3: ASR英文识别")
        print("=" * 60)
        
        asr_client = ASRClient(
            appid=ASR_CONFIG["appid"],
            access_token=ASR_CONFIG["access_token"],
            config=ASR_CONFIG
        )
        
        asr_result = asr_client.run_task(audio_url)
        
        # 保存ASR结果
        save_intermediate_result(asr_result, "asr_result.json")
        
        # 显示识别摘要
        if "result" in asr_result and "utterances" in asr_result["result"]:
            utterances = asr_result["result"]["utterances"]
            print(f"\n[ASR] 识别到 {len(utterances)} 段对话")
            for i, u in enumerate(utterances[:3]):  # 显示前3段
                speaker = u.get("speaker", "unknown")
                text = u.get("text", "")[:50]  # 截取前50字符
                print(f"  {i+1}. [Speaker {speaker}] {text}...")
            if len(utterances) > 3:
                print(f"  ... 共 {len(utterances)} 段")
        
        # ==========================================
        # 阶段2: 翻译与格式化
        # ==========================================
        print("\n" + "=" * 60)
        print("阶段 2/3: 翻译与格式化")
        print("=" * 60)
        
        translate_client = TranslateClient(
            api_key=TRANSLATE_CONFIG["api_key"],
            config=TRANSLATE_CONFIG
        )
        
        dialogues = translate_client.translate(asr_result)
        
        # 保存翻译结果
        save_intermediate_result(dialogues, "dialogues.json")
        
        # 显示翻译摘要
        print(f"\n[翻译] 生成 {len(dialogues)} 段中文对话")
        for i, d in enumerate(dialogues[:3]):  # 显示前3段
            speaker = d.get("speaker", "")
            text = d.get("text", "")[:50]
            print(f"  {i+1}. [{speaker}] {text}...")
        if len(dialogues) > 3:
            print(f"  ... 共 {len(dialogues)} 段")
        
        # ==========================================
        # 阶段3: TTS合成
        # ==========================================
        print("\n" + "=" * 60)
        print("阶段 3/3: TTS中文合成")
        print("=" * 60)
        
        tts_client = TTSClient(
            appid=TTS_CONFIG["appid"],
            access_token=TTS_CONFIG["access_token"],
            config=TTS_CONFIG
        )
        
        # 生成输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"podcast_{timestamp}.wav"
        output_path = os.path.join(STORAGE_CONFIG["output_dir"], output_filename)
        
        # 异步合成
        result_path = asyncio.run(tts_client.synthesize(dialogues, output_path))
        
        # ==========================================
        # 完成
        # ==========================================
        print("\n" + "=" * 60)
        print("✅ 流程完成!")
        print("=" * 60)
        print(f"输出文件: {result_path}")
        print(f"文件大小: {os.path.getsize(result_path) / 1024 / 1024:.2f} MB")
        print(f"\n中间结果保存在: {STORAGE_CONFIG['temp_dir']}/")
        print("  - asr_result.json (ASR识别结果)")
        print("  - dialogues.json (翻译后的对话)")
        
        return result_path
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ 流程失败")
        print("=" * 60)
        print(f"错误信息:\n{str(e)}")
        return None
    
    finally:
        # 清理TOS临时文件（可选）
        # 如果需要保留TOS上的文件，注释以下代码
        if tos_object_key and TOS_CONFIG.get("access_key"):
            try:
                uploader = TOSUploader(TOS_CONFIG)
                full_key = f"{TOS_CONFIG.get('upload_prefix', '')}{tos_object_key}"
                # uploader.delete_file(full_key)  # 可选：删除TOS上的临时文件
                print(f"\n[提示] TOS文件保留，如需删除请手动处理: {full_key}")
            except:
                pass


def main():
    """主入口"""
    # 确保目录存在
    ensure_dirs()
    
    # 验证配置
    if not validate_config():
        sys.exit(1)
    
    # 检查参数
    if len(sys.argv) < 2:
        print("使用方法: python main_pipeline.py <音频文件路径或URL>")
        print("\n示例:")
        print("  python main_pipeline.py https://example.com/audio.mp3")
        print("  python main_pipeline.py uploads/test.mp3")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    
    # 运行流程
    result = run_pipeline(audio_path)
    
    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
