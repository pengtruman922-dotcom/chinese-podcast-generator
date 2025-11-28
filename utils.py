"""
工具模块 - 封装ASR、翻译、TTS的核心逻辑
基于demo代码重构，增加错误处理与日志
"""

import requests
import json
import uuid
import time
import asyncio
import aiohttp
import base64
import wave
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

try:
    import tos
    from tos import TosClientV2, TosClient
    from tos.enum import ACLType
    TOS_AVAILABLE = True
except ImportError:
    TOS_AVAILABLE = False
    print("[警告] TOS SDK未安装，本地文件上传功能不可用。请运行: pip install tos")


# ==========================================
# TOS上传模块 (火山引擎TOS)
# ==========================================
class TOSUploader:
    """火山引擎TOS对象存储上传工具"""
    
    def __init__(self, config: Dict):
        if not TOS_AVAILABLE:
            raise Exception("TOS SDK未安装，请运行: pip install tos")
        
        self.config = config
        self.client = TosClientV2(
            ak=config["access_key"],
            sk=config["secret_key"],
            endpoint=config["endpoint"],
            region=config["region"]
        )
        self.bucket_name = config["bucket_name"]
        self.upload_prefix = config.get("upload_prefix", "")
    
    def upload_file(self, local_path: str) -> str:
        """
        上传本地文件到TOS
        
        Args:
            local_path: 本地文件路径
            
        Returns:
            公网可访问的URL
        """
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"文件不存在: {local_path}")
        
        # 生成对象键：前缀 + 时间戳 + 原始文件名
        file_name = Path(local_path).name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        object_key = f"{self.upload_prefix}{timestamp}_{file_name}"
        
        print(f"[TOS] 上传文件: {local_path}")
        print(f"[TOS] 目标键: {object_key}")
        
        try:
            # 上传文件（设置为公共读权限）
            with open(local_path, 'rb') as f:
                result = self.client.put_object(
                    bucket=self.bucket_name,
                    key=object_key,
                    content=f,
                    acl=ACLType.ACL_Public_Read  # 设置为公共读
                )
            
            # 生成公网URL
            url = f"https://{self.bucket_name}.{self.config['endpoint']}/{object_key}"
            print(f"[TOS] 上传成功: {url}")
            return url
            
        except Exception as e:
            raise Exception(f"TOS上传失败: {str(e)}")
    
    def delete_file(self, object_key: str):
        """删除TOS上的文件"""
        try:
            self.client.delete_object(bucket=self.bucket_name, key=object_key)
            print(f"[TOS] 已删除: {object_key}")
        except Exception as e:
            print(f"[TOS] 删除失败: {e}")


# ==========================================
# ASR模块 (火山引擎 BigASR)
# ==========================================
class ASRClient:
    """ASR识别客户端"""
    
    def __init__(self, appid: str, access_token: str, config: Dict):
        self.appid = appid
        self.token = access_token
        self.config = config
        self.base_url = config["base_url"]
        self.resource_id = config["resource_id"]
    
    def run_task(self, audio_url: str) -> Dict:
        """
        提交ASR任务并轮询结果
        
        Args:
            audio_url: 音频文件URL或本地路径
            
        Returns:
            ASR识别结果（包含utterances）
        """
        print(f"[ASR] 提交任务... URL: {audio_url}")
        task_id = self._submit(audio_url)
        print(f"[ASR] 任务提交成功，TaskID: {task_id}")
        
        print(f"[ASR] 开始轮询查询结果 (间隔: {self.config['poll_interval']}s)...")
        result = self._poll_result(task_id)
        print(f"[ASR] 识别完成")
        return result
    
    def _submit(self, audio_url: str) -> str:
        """提交ASR任务"""
        submit_url = f"{self.base_url}/submit"
        req_id = str(uuid.uuid4())
        
        headers = {
            "X-Api-App-Key": self.appid,
            "X-Api-Access-Key": self.token,
            "X-Api-Resource-Id": self.resource_id,
            "X-Api-Request-Id": req_id,
            "Content-Type": "application/json"
        }
        
        # 组装请求配置
        request_config = {
            "model_name": self.config["model_name"],
            "model_version": self.config["model_version"],
            "enable_punc": self.config["enable_punc"],
            "enable_speaker_info": self.config["enable_speaker_info"],
            "enable_gender_detection": self.config["enable_gender_detection"],
            "show_utterances": self.config["enable_timestamps"]
        }
        
        # 如果开启了说话人或性别，强制开启分句信息
        if self.config["enable_speaker_info"] or self.config["enable_gender_detection"]:
            request_config["show_utterances"] = True
        
        # 热词处理
        hotwords = self.config.get("hotwords", [])
        if hotwords and len(hotwords) > 0:
            hotword_list = [{"word": w.strip()} for w in hotwords if w.strip()]
            if hotword_list:
                context_data = {"hotwords": hotword_list}
                request_config["context"] = json.dumps(context_data, ensure_ascii=False)
        
        payload = {
            "user": {"uid": "pipeline_user"},
            "audio": {"url": audio_url, "format": "mp3"},
            "request": request_config
        }
        
        try:
            resp = requests.post(submit_url, headers=headers, data=json.dumps(payload))
            if resp.status_code != 200:
                raise Exception(f"HTTP Error {resp.status_code}: {resp.text}")
            return req_id
        except Exception as e:
            raise Exception(f"ASR提交请求失败: {str(e)}")
    
    def _poll_result(self, task_id: str) -> Dict:
        """轮询查询ASR结果"""
        query_url = f"{self.base_url}/query"
        start_time = time.time()
        timeout = self.config["timeout"]
        interval = self.config["poll_interval"]
        
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"ASR查询超时 (>{timeout}s)")
            
            headers = {
                "X-Api-App-Key": self.appid,
                "X-Api-Access-Key": self.token,
                "X-Api-Resource-Id": self.resource_id,
                "X-Api-Request-Id": task_id
            }
            
            try:
                resp = requests.post(query_url, headers=headers, json={})
                status_code = resp.headers.get("X-Api-Status-Code")
                
                if status_code == "20000000":
                    return resp.json()
                elif status_code in ["20000001", "20000002"]:
                    print(f"[ASR] 任务处理中... (状态: {status_code})")
                    time.sleep(interval)
                    continue
                else:
                    err_msg = resp.headers.get('X-Api-Message', 'Unknown Error')
                    raise Exception(f"ASR服务端返回错误: {status_code} - {err_msg}\n完整响应: {resp.text}")
            except Exception as e:
                if "ASR服务端返回错误" in str(e):
                    raise e
                print(f"[ASR] 网络查询异常: {e}，将在 {interval}秒后重试...")
                time.sleep(interval)


# ==========================================
# 翻译模块 (阿里灵积 DashScope)
# ==========================================
class TranslateClient:
    """翻译客户端"""
    
    def __init__(self, api_key: str, config: Dict):
        self.api_key = api_key
        self.config = config
        self.endpoint = f"{config['base_url']}/chat/completions"
    
    def translate(self, asr_result: Dict) -> List[Dict]:
        """
        将ASR结果翻译为中文对话JSON
        
        Args:
            asr_result: ASR识别结果
            
        Returns:
            翻译后的对话列表 [{"speaker": "发言者1", "text": "..."}]
        """
        # 从ASR结果提取文本
        asr_text = self._format_asr_text(asr_result)
        print(f"[翻译] ASR文本长度: {len(asr_text)} 字符")
        
        # 如果文本超过10000字符，分段翻译
        max_chunk_size = 10000
        if len(asr_text) > max_chunk_size:
            print(f"[翻译] 文本过长，将分段翻译...")
            return self._translate_in_chunks(asr_text, max_chunk_size)
        
        # 普通翻译流程
        return self._translate_single(asr_text)
    
    def _translate_in_chunks(self, asr_text: str, chunk_size: int) -> List[Dict]:
        """分段翻译长文本，按说话人分割避免截断完整对话"""
        lines = asr_text.strip().split('\n')
        chunks = []
        current_chunk = []
        current_length = 0
        
        # 按行分组，确保每组在 chunk_size ± 1000 范围内
        # 并且不会切断同一个说话人的连续对话
        min_chunk = chunk_size - 1000
        max_chunk = chunk_size + 1000
        
        for i, line in enumerate(lines):
            line_length = len(line) + 1  # +1 for newline
            
            # 检查是否是新的说话人（通过 [Speaker X] 标记）
            is_new_speaker = line.strip().startswith('[Speaker')
            
            # 如果当前块已达到最小长度，且遇到新说话人，则分割
            if current_length >= min_chunk and is_new_speaker and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_length = line_length
            # 如果当前块超过最大长度，强制分割
            elif current_length + line_length > max_chunk and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_length = line_length
            else:
                current_chunk.append(line)
                current_length += line_length
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        print(f"[翻译] 分为 {len(chunks)} 段进行翻译")
        for i, chunk in enumerate(chunks, 1):
            print(f"[翻译]   第{i}段: {len(chunk)} 字符")
        
        all_dialogues = []
        for i, chunk in enumerate(chunks, 1):
            print(f"[翻译] 正在翻译第 {i}/{len(chunks)} 段...")
            try:
                dialogues = self._translate_single(chunk)
                all_dialogues.extend(dialogues)
                print(f"[翻译] 第 {i} 段完成，得到 {len(dialogues)} 段对话")
            except Exception as e:
                print(f"[翻译] 第 {i} 段失败: {e}，跳过...")
                continue
        
        print(f"[翻译] 分段翻译完成，总计 {len(all_dialogues)} 段对话")
        return all_dialogues
    
    def _translate_single(self, asr_text: str) -> List[Dict]:
        """翻译单段文本"""
        # 构建用户提示词
        user_prompt = self.config["user_prompt_template"].format(asr_text=asr_text)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"{self.api_key}"
        }
        
        payload = {
            "model": self.config["model"],
            "messages": [
                {
                    "role": "system",
                    "content": self.config["system_prompt"]
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "stream": False
        }
        
        try:
            print(f"[翻译] 调用API... 模型: {self.config['model']}")
            resp = requests.post(self.endpoint, headers=headers, data=json.dumps(payload), timeout=120)
            resp.raise_for_status()
            
            response_json = resp.json()
            
            # 提取助手回复
            if "choices" in response_json and len(response_json["choices"]) > 0:
                assistant_message = response_json["choices"][0]["message"]["content"]
                print(f"[翻译] 翻译完成，返回内容长度: {len(assistant_message)} 字符")
                
                # 解析JSON数组
                dialogues = self._parse_dialogues(assistant_message)
                print(f"[翻译] 解析出 {len(dialogues)} 段对话")
                return dialogues
            else:
                raise Exception(f"翻译API返回格式错误: {response_json}")
                
        except requests.exceptions.HTTPError as http_err:
            raise Exception(f"翻译HTTP错误: {http_err}\n完整响应: {resp.text}")
        except Exception as err:
            raise Exception(f"翻译失败: {err}")
    
    def _format_asr_text(self, asr_result: Dict) -> str:
        """将ASR结果格式化为文本，只保留speaker和text字段"""
        if "result" not in asr_result:
            raise Exception("ASR结果格式错误：缺少result字段")
        
        result = asr_result["result"]
        
        # 如果有utterances，使用分句结果，只保留speaker和text
        if "utterances" in result:
            lines = []
            for u in result["utterances"]:
                # 提取speaker
                speaker = u.get("speaker", "unknown")
                if "additions" in u and "speaker" in u["additions"]:
                    speaker = u["additions"]["speaker"]
                
                # 提取text
                text = u.get("text", "")
                
                # 只输出speaker和text
                lines.append(f"[Speaker {speaker}] {text}")
            return "\n".join(lines)
        
        # 否则使用全文
        return result.get("text", "")
    
    def _parse_dialogues(self, text: str) -> List[Dict]:
        """解析翻译结果为对话列表"""
        # 尝试提取JSON数组
        text = text.strip()
        
        # 移除可能的markdown代码块标记
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        # 解析JSON
        try:
            dialogues = json.loads(text)
            if not isinstance(dialogues, list):
                raise ValueError("翻译结果不是JSON数组")
            
            # 验证格式
            for d in dialogues:
                if not isinstance(d, dict) or "speaker" not in d or "text" not in d:
                    raise ValueError(f"对话格式错误: {d}")
            
            return dialogues
        except json.JSONDecodeError as e:
            raise Exception(f"翻译结果JSON解析失败: {e}\n原始内容:\n{text}")


# ==========================================
# TTS模块 (火山引擎 TTS)
# ==========================================
class TTSClient:
    """TTS合成客户端"""
    
    def __init__(self, appid: str, access_token: str, config: Dict):
        self.appid = appid
        self.token = access_token
        self.config = config
        self.api_url = config["api_url"]
        self.resource_id = config["resource_id"]
    
    async def synthesize(self, dialogues: List[Dict], output_path: str) -> str:
        """
        合成对话为音频文件
        
        Args:
            dialogues: 对话列表
            output_path: 输出文件路径
            
        Returns:
            输出文件路径
        """
        print(f"[TTS] 开始合成 {len(dialogues)} 段对话...")
        
        results = [None] * len(dialogues)
        errors = []
        concurrency = self.config["concurrency"]
        sem = asyncio.Semaphore(concurrency)
        
        async with aiohttp.ClientSession() as session:
            async def worker(idx: int, item: Dict):
                speaker_label = item.get("speaker")
                text = item.get("text")
                
                # 获取音色ID
                voice_id = self.config["speaker_map"].get(speaker_label)
                if not voice_id:
                    # 使用第一个音色作为默认
                    voice_id = list(self.config["speaker_map"].values())[0] if self.config["speaker_map"] else None
                
                if not voice_id:
                    errors.append(f"#{idx + 1} 未找到音色映射: {speaker_label}")
                    return
                
                async with sem:
                    pcm, err = await self._fetch_tts_pcm(session, text, voice_id, f"req_{idx}")
                    if err:
                        errors.append(f"#{idx + 1} TTS合成失败: {err}")
                    else:
                        results[idx] = {"pcm": pcm, "speaker": speaker_label}
                        print(f"[TTS] 完成 {idx + 1}/{len(dialogues)}")
                    await asyncio.sleep(0.01)
            
            # 并发执行
            tasks = [worker(i, d) for i, d in enumerate(dialogues)]
            await asyncio.gather(*tasks)
        
        if errors:
            raise Exception(f"TTS合成存在错误:\n" + "\n".join(errors))
        
        # 拼接音频
        print(f"[TTS] 拼接音频...")
        final_pcm = self._concat_audio(results)
        
        # 保存文件
        self._save_wav(final_pcm, output_path)
        print(f"[TTS] 合成完成: {output_path}")
        return output_path
    
    async def _fetch_tts_pcm(self, session: aiohttp.ClientSession, text: str, 
                            speaker_id: str, req_id: str) -> Tuple[Optional[bytearray], Optional[str]]:
        """调用TTS接口获取PCM音频"""
        headers = {
            "Authorization": f"Bearer; {self.token}",
            "X-Api-App-Id": self.appid,
            "X-Api-Access-Key": self.token,
            "X-Api-Resource-Id": self.resource_id,
            "X-Api-Request-Id": req_id
        }
        
        payload = {
            "req_params": {
                "text": text,
                "speaker": speaker_id,
                "audio_params": {
                    "format": self.config["audio_format"],
                    "sample_rate": self.config["sample_rate"],
                    "speech_rate": self.config["speech_rate"]  # 语速配置
                }
            }
        }
        
        full_pcm = bytearray()
        try:
            async with session.post(self.api_url, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    err_text = await resp.text()
                    return None, f"HTTP {resp.status}: {err_text[:200]}"
                
                async for line in resp.content:
                    if not line:
                        continue
                    try:
                        line_str = line.decode('utf-8').strip()
                        if not line_str:
                            continue
                        data = json.loads(line_str)
                        
                        if "code" in data and data["code"] != 0 and data["code"] != 20000000:
                            return None, f"API Error {data['code']}: {data.get('message', 'Unknown')}"
                        
                        if "data" in data and data["data"]:
                            full_pcm.extend(base64.b64decode(data["data"]))
                    except Exception:
                        continue
            
            return full_pcm, None
        except Exception as e:
            return None, str(e)
    
    def _concat_audio(self, results: List[Dict]) -> bytearray:
        """拼接音频片段，插入停顿"""
        final_pcm = bytearray()
        last_speaker = None
        
        for res in results:
            if not res:
                continue
            
            # 计算停顿
            pause_ms = 0
            if last_speaker:
                if res["speaker"] == last_speaker:
                    pause_ms = self.config["pause_same_speaker"]
                else:
                    pause_ms = self.config["pause_diff_speaker"]
            
            # 插入停顿
            if pause_ms > 0:
                silence = self._generate_silence_pcm(pause_ms)
                final_pcm.extend(silence)
            
            # 添加音频
            final_pcm.extend(res["pcm"])
            last_speaker = res["speaker"]
        
        return final_pcm
    
    def _generate_silence_pcm(self, duration_ms: int) -> bytes:
        """生成静音PCM数据"""
        if duration_ms <= 0:
            return b""
        
        sample_rate = self.config["sample_rate"]
        num_bytes = int((sample_rate * 2 * 1) * (duration_ms / 1000))
        if num_bytes % 2 != 0:
            num_bytes += 1
        
        return b'\x00' * num_bytes
    
    def _save_wav(self, pcm_data: bytearray, output_path: str):
        """保存PCM数据为WAV文件"""
        with wave.open(output_path, 'wb') as f:
            f.setnchannels(1)  # 单声道
            f.setsampwidth(2)  # 16bit
            f.setframerate(self.config["sample_rate"])
            f.writeframes(pcm_data)
