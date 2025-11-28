"""
FastAPI后端服务 - 提供上传、任务处理、下载接口
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import os
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
import shutil
import json

from config import ASR_CONFIG, TRANSLATE_CONFIG, TTS_CONFIG, STORAGE_CONFIG, TOS_CONFIG, VOICE_DATABASE
from utils import ASRClient, TranslateClient, TTSClient, TOSUploader

app = FastAPI(title="中文播客生成API")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 任务存储（生产环境应使用数据库）
tasks_db: Dict[str, dict] = {}

# 任务数据持久化文件
TASKS_DB_FILE = "tasks_db.json"


def load_tasks_db():
    """从文件加载任务数据"""
    global tasks_db
    try:
        if os.path.exists(TASKS_DB_FILE):
            with open(TASKS_DB_FILE, 'r', encoding='utf-8') as f:
                tasks_db = json.load(f)
            print(f"[系统] 加载了 {len(tasks_db)} 个任务")
    except Exception as e:
        print(f"[系统] 加载任务失败: {e}")
        tasks_db = {}


def save_tasks_db():
    """保存任务数据到文件"""
    try:
        with open(TASKS_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(tasks_db, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[系统] 保存任务失败: {e}")


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str
    created_at: str
    file_name: Optional[str] = None
    result_file: Optional[str] = None
    error: Optional[str] = None


class ConfigUpdateRequest(BaseModel):
    config_data: Dict[str, Any]


def ensure_dirs():
    """确保必要的目录存在"""
    for dir_path in [STORAGE_CONFIG["upload_dir"], 
                     STORAGE_CONFIG["output_dir"], 
                     STORAGE_CONFIG["temp_dir"]]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)


async def process_task(task_id: str, file_path: str, resume_from: str = None):
    """后台任务处理流程，支持断点续传"""
    try:
        # 如果是续传，从指定阶段开始
        if not resume_from or resume_from == "upload":
            tasks_db[task_id]["status"] = "processing"
            tasks_db[task_id]["message"] = "正在上传到TOS..."
            tasks_db[task_id]["current_stage"] = "upload"
            save_tasks_db()
            
            # 上传到TOS
            if not file_path.startswith(('http://', 'https://')):
                uploader = TOSUploader(TOS_CONFIG)
                audio_url = uploader.upload_file(file_path)
                tasks_db[task_id]["audio_url"] = audio_url
            else:
                audio_url = file_path
                tasks_db[task_id]["audio_url"] = audio_url
        else:
            # 续传时，从任务中读取之前的audio_url
            audio_url = tasks_db[task_id].get("audio_url")
            if not audio_url and not file_path.startswith(('http://', 'https://')):
                raise Exception("续传时未找到音频URL")
        
        if not resume_from or resume_from in ["upload", "asr"]:
            # ASR识别
            tasks_db[task_id]["status"] = "processing"
            tasks_db[task_id]["message"] = "正在进行ASR识别..."
            tasks_db[task_id]["current_stage"] = "asr"
            save_tasks_db()
            
            asr_client = ASRClient(
                appid=ASR_CONFIG["appid"],
                access_token=ASR_CONFIG["access_token"],
                config=ASR_CONFIG
            )
            asr_result = asr_client.run_task(audio_url)
            
            # 保存ASR结果
            asr_file = os.path.join(STORAGE_CONFIG["temp_dir"], f"{task_id}_asr.json")
            with open(asr_file, 'w', encoding='utf-8') as f:
                json.dump(asr_result, f, ensure_ascii=False, indent=2)
            tasks_db[task_id]["asr_file"] = f"{task_id}_asr.json"
            save_tasks_db()
        else:
            # 续传时，从文件读取ASR结果
            asr_file = os.path.join(STORAGE_CONFIG["temp_dir"], tasks_db[task_id].get("asr_file", f"{task_id}_asr.json"))
            if not os.path.exists(asr_file):
                raise Exception("续传时未找到ASR结果文件")
            with open(asr_file, 'r', encoding='utf-8') as f:
                asr_result = json.load(f)
        
        if not resume_from or resume_from in ["upload", "asr", "translate"]:
            # 翻译
            tasks_db[task_id]["message"] = "正在翻译为中文..."
            tasks_db[task_id]["current_stage"] = "translate"
            save_tasks_db()
            
            translate_client = TranslateClient(
                api_key=TRANSLATE_CONFIG["api_key"],
                config=TRANSLATE_CONFIG
            )
            dialogues = translate_client.translate(asr_result)
            
            # 保存翻译结果
            translate_file = os.path.join(STORAGE_CONFIG["temp_dir"], f"{task_id}_dialogues.json")
            with open(translate_file, 'w', encoding='utf-8') as f:
                json.dump(dialogues, f, ensure_ascii=False, indent=2)
            tasks_db[task_id]["dialogues_file"] = f"{task_id}_dialogues.json"
            save_tasks_db()
        else:
            # 续传时，从文件读取翻译结果
            translate_file = os.path.join(STORAGE_CONFIG["temp_dir"], tasks_db[task_id].get("dialogues_file", f"{task_id}_dialogues.json"))
            if not os.path.exists(translate_file):
                raise Exception("续传时未找到翻译结果文件")
            with open(translate_file, 'r', encoding='utf-8') as f:
                dialogues = json.load(f)
        
        # TTS合成
        tasks_db[task_id]["message"] = "正在合成中文语音..."
        tasks_db[task_id]["current_stage"] = "tts"
        save_tasks_db()
        
        tts_client = TTSClient(
            appid=TTS_CONFIG["appid"],
            access_token=TTS_CONFIG["access_token"],
            config=TTS_CONFIG
        )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"podcast_{timestamp}.wav"
        output_path = os.path.join(STORAGE_CONFIG["output_dir"], output_filename)
        
        result_path = await tts_client.synthesize(dialogues, output_path)
        
        # 更新任务状态
        tasks_db[task_id]["status"] = "completed"
        tasks_db[task_id]["message"] = "处理完成"
        tasks_db[task_id]["result_file"] = output_filename
        tasks_db[task_id]["completed_at"] = datetime.now().isoformat()
        tasks_db[task_id]["current_stage"] = "completed"
        save_tasks_db()
        
    except Exception as e:
        tasks_db[task_id]["status"] = "failed"
        tasks_db[task_id]["error"] = str(e)
        tasks_db[task_id]["message"] = f"处理失败: {str(e)}"
        # 记录失败的阶段，方便续传
        if "current_stage" not in tasks_db[task_id]:
            tasks_db[task_id]["current_stage"] = "unknown"
        save_tasks_db()


@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    ensure_dirs()
    load_tasks_db()


@app.get("/")
async def root():
    """健康检查"""
    return {"status": "ok", "message": "中文播客生成API服务运行中"}


@app.post("/api/upload", response_model=TaskResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """上传音频文件并创建任务"""
    
    # 验证文件类型
    allowed_extensions = ['.mp3', '.wav', '.mp4', '.m4a', '.flac']
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件格式。支持的格式: {', '.join(allowed_extensions)}"
        )
    
    # 生成任务ID
    task_id = str(uuid.uuid4())
    
    # 保存上传的文件
    upload_path = os.path.join(STORAGE_CONFIG["upload_dir"], f"{task_id}{file_ext}")
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 创建任务记录
    tasks_db[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "message": "任务已创建",
        "file_name": file.filename,
        "file_path": upload_path,
        "created_at": datetime.now().isoformat(),
        "result_file": None,
        "error": None
    }
    save_tasks_db()
    
    # 添加后台任务
    background_tasks.add_task(process_task, task_id, upload_path)
    
    return TaskResponse(**tasks_db[task_id])


@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """查询任务状态"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return TaskResponse(**tasks_db[task_id])


@app.get("/api/tasks", response_model=List[TaskResponse])
async def list_tasks():
    """获取所有任务列表（按创建时间倒序）"""
    sorted_tasks = sorted(
        tasks_db.values(), 
        key=lambda x: x.get('created_at', ''), 
        reverse=True
    )
    return [TaskResponse(**task) for task in sorted_tasks]


@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """下载生成的音频文件"""
    file_path = os.path.join(STORAGE_CONFIG["output_dir"], filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="audio/wav"
    )


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks_db[task_id]
    
    # 删除相关文件
    if task.get("file_path") and os.path.exists(task["file_path"]):
        os.remove(task["file_path"])
    
    if task.get("result_file"):
        result_path = os.path.join(STORAGE_CONFIG["output_dir"], task["result_file"])
        if os.path.exists(result_path):
            os.remove(result_path)
    
    # 删除中间文件
    if task.get("asr_file"):
        asr_path = os.path.join(STORAGE_CONFIG["temp_dir"], task["asr_file"])
        if os.path.exists(asr_path):
            os.remove(asr_path)
    
    if task.get("dialogues_file"):
        dialogues_path = os.path.join(STORAGE_CONFIG["temp_dir"], task["dialogues_file"])
        if os.path.exists(dialogues_path):
            os.remove(dialogues_path)
    
    # 从数据库删除
    del tasks_db[task_id]
    save_tasks_db()
    
    return {"message": "任务已删除"}


@app.post("/api/tasks/{task_id}/resume")
async def resume_task(task_id: str, background_tasks: BackgroundTasks):
    """续传失败的任务，从失败的阶段继续"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks_db[task_id]
    
    # 只有失败的任务才能续传
    if task["status"] != "failed":
        raise HTTPException(status_code=400, detail="只有失败的任务才能续传")
    
    # 判断从哪个阶段续传
    current_stage = task.get("current_stage", "upload")
    
    # 检查各阶段的中间文件是否存在，决定从哪里开始
    has_audio_url = bool(task.get("audio_url"))
    has_asr_file = False
    has_dialogues_file = False
    
    if task.get("asr_file"):
        asr_path = os.path.join(STORAGE_CONFIG["temp_dir"], task["asr_file"])
        has_asr_file = os.path.exists(asr_path)
    
    if task.get("dialogues_file"):
        dialogues_path = os.path.join(STORAGE_CONFIG["temp_dir"], task["dialogues_file"])
        has_dialogues_file = os.path.exists(dialogues_path)
    
    # 根据已有的中间结果决定从哪个阶段开始
    if has_dialogues_file:
        resume_from = "tts"  # 有翻译结果，直接TTS
    elif has_asr_file:
        resume_from = "translate"  # 有ASR结果，从翻译开始
    elif has_audio_url:
        resume_from = "asr"  # 有音频URL，从ASR开始
    else:
        resume_from = "upload"  # 从头开始
    
    # 重置任务状态
    tasks_db[task_id]["status"] = "pending"
    tasks_db[task_id]["error"] = None
    tasks_db[task_id]["message"] = f"准备从 {resume_from} 阶段继续处理..."
    save_tasks_db()
    
    # 添加后台任务
    file_path = task.get("file_path", "")
    background_tasks.add_task(process_task, task_id, file_path, resume_from)
    
    return TaskResponse(**tasks_db[task_id])


@app.get("/api/tasks/{task_id}/details")
async def get_task_details(task_id: str):
    """获取任务详情（包括ASR和翻译结果）"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks_db[task_id]
    details = {"task": task, "asr_result": None, "dialogues": None}
    
    # 读取ASR结果
    if task.get("asr_file"):
        asr_path = os.path.join(STORAGE_CONFIG["temp_dir"], task["asr_file"])
        if os.path.exists(asr_path):
            with open(asr_path, 'r', encoding='utf-8') as f:
                details["asr_result"] = json.load(f)
    
    # 读取翻译结果
    if task.get("dialogues_file"):
        dialogues_path = os.path.join(STORAGE_CONFIG["temp_dir"], task["dialogues_file"])
        if os.path.exists(dialogues_path):
            with open(dialogues_path, 'r', encoding='utf-8') as f:
                details["dialogues"] = json.load(f)
    
    return details


@app.get("/api/config")
async def get_config():
    """获取配置（完整信息，不脱敏）"""
    config = {
        "asr": {
            "appid": str(ASR_CONFIG.get("appid", "")),
            "access_token": ASR_CONFIG.get("access_token", ""),
            "poll_interval": ASR_CONFIG.get("poll_interval", 10),
            "hotwords": ASR_CONFIG.get("hotwords", [])
        },
        "translate": {
            "api_key": TRANSLATE_CONFIG.get("api_key", ""),
            "base_url": TRANSLATE_CONFIG.get("base_url", ""),
            "model": TRANSLATE_CONFIG.get("model", ""),
            "system_prompt": TRANSLATE_CONFIG.get("system_prompt", "")
        },
        "tts": {
            "appid": str(TTS_CONFIG.get("appid", "")),
            "access_token": TTS_CONFIG.get("access_token", ""),
            "resource_id": TTS_CONFIG.get("resource_id", ""),
            "speaker_map": TTS_CONFIG.get("speaker_map", {}),
            "concurrency": TTS_CONFIG.get("concurrency", 5),
            "speech_rate": TTS_CONFIG.get("speech_rate", -90)
        },
        "tos": {
            "access_key": TOS_CONFIG.get("access_key", ""),
            "secret_key": TOS_CONFIG.get("secret_key", ""),
            "endpoint": TOS_CONFIG.get("endpoint", ""),
            "region": TOS_CONFIG.get("region", ""),
            "bucket_name": TOS_CONFIG.get("bucket_name", "")
        }
    }
    return config


@app.get("/api/voice-database")
async def get_voice_database():
    """获取TTS音色数据库"""
    return VOICE_DATABASE


@app.post("/api/config")
async def update_config(request: ConfigUpdateRequest):
    """更新配置"""
    try:
        config_data = request.config_data
        
        # 更新内存中的配置
        if "asr" in config_data:
            for key, value in config_data["asr"].items():
                ASR_CONFIG[key] = value
        
        if "translate" in config_data:
            for key, value in config_data["translate"].items():
                TRANSLATE_CONFIG[key] = value
        
        if "tts" in config_data:
            for key, value in config_data["tts"].items():
                TTS_CONFIG[key] = value
        
        if "tos" in config_data:
            for key, value in config_data["tos"].items():
                TOS_CONFIG[key] = value
        
        # 注意：配置只在内存中生效，不修改config.py文件
        # 如需永久保存，请手动编辑config.py文件
        
        return {"message": "配置已更新（仅在当前进程生效，重启后恢复）"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"配置更新失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
