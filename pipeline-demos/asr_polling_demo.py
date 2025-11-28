import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import requests
import json
import uuid
import time


# ==========================================
#  核心逻辑类
# ==========================================
class VolcAsrClient:
    def __init__(self, appid, access_token, log_func=print):
        self.appid = appid
        self.token = access_token
        self.log = log_func
        self.base_url = "https://openspeech.bytedance.com/api/v3/auc/bigmodel"
        self.resource_id = "volc.bigasr.auc"

    def run_task(self, audio_url, enable_speaker=False, enable_timestamps=False, enable_gender=False, hotwords=None,
                 poll_interval=2):
        self.log(f"[-] 正在提交任务...\n    URL: {audio_url}")
        task_id = self._submit(audio_url, enable_speaker, enable_timestamps, enable_gender, hotwords)
        self.log(f"[+] 任务提交成功，TaskID: {task_id}")

        self.log(f"[-] 开始轮询查询结果 (间隔: {poll_interval}s)...")
        result = self._poll_result(task_id, interval=poll_interval)
        return result

    def _submit(self, url, enable_speaker, enable_timestamps, enable_gender, hotwords):
        submit_url = f"{self.base_url}/submit"
        req_id = str(uuid.uuid4())

        headers = {
            "X-Api-App-Key": self.appid,
            "X-Api-Access-Key": self.token,
            "X-Api-Resource-Id": self.resource_id,
            "X-Api-Request-Id": req_id,
            "Content-Type": "application/json"
        }

        # --- 配置组装 ---
        request_config = {
            "model_name": "bigmodel",
            "model_version": "400",
            "enable_punc": True,
            # 动态配置项
            "enable_speaker_info": enable_speaker,
            "enable_gender_detection": enable_gender,
            "show_utterances": enable_timestamps
        }

        # 如果开启了说话人或性别，强制开启分句信息，否则拿不到标签
        if enable_speaker or enable_gender:
            request_config["show_utterances"] = True

        if hotwords and len(hotwords) > 0:
            hotword_list = [{"word": w.strip()} for w in hotwords if w.strip()]
            if hotword_list:
                context_data = {"hotwords": hotword_list}
                request_config["context"] = json.dumps(context_data, ensure_ascii=False)

        payload = {
            "user": {"uid": "gui_user_v3"},
            "audio": {"url": url, "format": "mp3"},
            "request": request_config
        }

        try:
            resp = requests.post(submit_url, headers=headers, data=json.dumps(payload))
            if resp.status_code != 200:
                raise Exception(f"HTTP Error {resp.status_code}: {resp.text}")
            return req_id
        except Exception as e:
            raise Exception(f"提交请求失败: {str(e)}")

    def _poll_result(self, task_id, timeout_seconds=600, interval=2):
        query_url = f"{self.base_url}/query"
        start_time = time.time()

        while True:
            if time.time() - start_time > timeout_seconds:
                raise TimeoutError("查询超时")

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
                    self.log(f"[*] 任务处理中... (状态: {status_code})")
                    time.sleep(interval)
                    continue
                else:
                    err_msg = resp.headers.get('X-Api-Message', 'Unknown Error')
                    raise Exception(f"服务端返回错误: {status_code} - {err_msg}")
            except Exception as e:
                if "服务端返回错误" in str(e):
                    raise e
                self.log(f"[!] 网络查询异常: {e}，将在 {interval}秒后重试...")
                time.sleep(interval)


# ==========================================
#  GUI 界面类
# ==========================================
class ASRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("火山引擎 ASR - 说话人与性别检测版")
        self.root.geometry("700x800")

        pad_x = 10
        pad_y = 5

        # --- 1. 必填区域 ---
        labelframe_req = ttk.LabelFrame(root, text="必填信息")
        labelframe_req.pack(fill="x", padx=pad_x, pady=pad_y)

        # AppID / Token / URL (预填方便测试)
        self._create_input(labelframe_req, 0, "App ID:", "")
        self._create_input(labelframe_req, 1, "Access Token:", "", show="*")

        self.entry_url = self._create_input(labelframe_req, 2, "Audio URL:",
                                            "https://my-asr-audio.tos-cn-beijing.volces.com/1min_test.mp3")

        # --- 2. 选填区域 (重点在这里) ---
        labelframe_opt = ttk.LabelFrame(root, text="高级功能配置")
        labelframe_opt.pack(fill="x", padx=pad_x, pady=pad_y)

        # Checkboxes
        self.var_speaker = tk.BooleanVar(value=True)  # 默认开启说话人
        self.chk_speaker = ttk.Checkbutton(labelframe_opt, text="说话人分离 (Speaker)", variable=self.var_speaker)
        self.chk_speaker.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.var_gender = tk.BooleanVar(value=True)  # 默认开启性别
        self.chk_gender = ttk.Checkbutton(labelframe_opt, text="性别检测 (Gender)", variable=self.var_gender)
        self.chk_gender.grid(row=0, column=1, sticky="w", padx=10, pady=5)

        self.var_timestamp = tk.BooleanVar(value=True)
        self.chk_timestamp = ttk.Checkbutton(labelframe_opt, text="分词详情 (Detail)", variable=self.var_timestamp)
        self.chk_timestamp.grid(row=0, column=2, sticky="w", padx=10, pady=5)

        # 轮询
        ttk.Label(labelframe_opt, text="轮询间隔(s):").grid(row=1, column=0, sticky="e", padx=5)
        self.entry_interval = ttk.Entry(labelframe_opt, width=10)
        self.entry_interval.insert(0, "2")
        self.entry_interval.grid(row=1, column=1, sticky="w", padx=5)

        # 热词
        ttk.Label(labelframe_opt, text="热词:").grid(row=2, column=0, sticky="e", padx=5)
        self.entry_hotwords = ttk.Entry(labelframe_opt, width=50)
        self.entry_hotwords.grid(row=2, column=1, columnspan=2, sticky="w", padx=5)

        # --- 3. 按钮 ---
        self.btn_run = ttk.Button(root, text="🚀 开始识别", command=self.on_start_click)
        self.btn_run.pack(pady=10)

        # --- 4. 日志 ---
        self.txt_log = scrolledtext.ScrolledText(root, height=25)
        self.txt_log.pack(fill="both", expand=True, padx=pad_x, pady=pad_y)
        self.txt_log.tag_config("speaker_a", foreground="blue")  # 说话人A颜色
        self.txt_log.tag_config("speaker_b", foreground="brown")  # 说话人B颜色
        self.txt_log.tag_config("meta", foreground="gray")

    def _create_input(self, parent, row, label, default_val, show=None):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="e", padx=5, pady=5)
        entry = ttk.Entry(parent, width=50, show=show)
        entry.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        entry.insert(0, default_val)
        # 把 entry 存起来以便后面获取，这里简化处理只返回实例
        if label == "App ID:":
            self.entry_appid = entry
        elif label == "Access Token:":
            self.entry_token = entry
        return entry

    def log_message(self, msg, level="info", tags=None):
        def _append():
            self.txt_log.insert(tk.END, msg + "\n", tags)
            self.txt_log.see(tk.END)

        self.root.after(0, _append)

    def on_start_click(self):
        appid = self.entry_appid.get().strip()
        token = self.entry_token.get().strip()
        url = self.entry_url.get().strip()

        if not appid or not token:
            messagebox.showerror("错误", "请填写 AppID 和 Token")
            return

        self.btn_run.config(state="disabled")
        self.txt_log.delete(1.0, tk.END)

        thread = threading.Thread(target=self.run_process, args=(appid, token, url))
        thread.daemon = True
        thread.start()

    def run_process(self, appid, token, url):
        try:
            hotwords = self.entry_hotwords.get().split(",")
            interval = float(self.entry_interval.get())

            client = VolcAsrClient(appid, token, log_func=self.log_message)

            result = client.run_task(
                audio_url=url,
                enable_speaker=self.var_speaker.get(),
                enable_gender=self.var_gender.get(),
                enable_timestamps=self.var_timestamp.get(),
                hotwords=hotwords,
                poll_interval=interval
            )

            self.log_message("\n" + "=" * 40)
            self.log_message("识别结果 (对话模式)", tags="meta")
            self.log_message("=" * 40 + "\n")

            if "result" in result and "utterances" in result['result']:
                utterances = result['result']['utterances']
                for u in utterances:
                    # 获取时间
                    start = u.get('start_time', 0)
                    end = u.get('end_time', 0)
                    text = u.get('text', '')

                    # 获取说话人 (默认 'unknown')
                    spk_id = u.get('speaker', 'unknown')
                    # 兼容不同接口返回格式，有时在additions里
                    if 'additions' in u and 'speaker' in u['additions']:
                        spk_id = u['additions']['speaker']

                    # 获取性别 (在additions里)
                    gender = ""
                    if 'additions' in u and 'gender' in u['additions']:
                        g_tag = u['additions']['gender']
                        gender = f"[{g_tag}] "  # e.g. [male]

                    # 构造标签字符串
                    tag_str = f"[{start}ms] [Speaker {spk_id}] {gender}"

                    # 打印：根据SpeakerID用不同颜色，方便区分
                    color_tag = "speaker_a" if str(spk_id) in ["0", "2", "4"] else "speaker_b"

                    self.log_message(tag_str, tags="meta")
                    self.log_message(f"   {text}\n", tags=color_tag)

            elif "result" in result:
                # 只有全文，没有分句
                self.log_message("【注意】未获取到说话人信息，显示全文：", tags="meta")
                self.log_message(result['result'].get('text', ''), tags="info")
            else:
                self.log_message(f"Raw: {result}")

        except Exception as e:
            self.log_message(f"\n[Error]: {str(e)}", "error")
        finally:
            self.root.after(0, lambda: self.btn_run.config(state="normal"))


if __name__ == "__main__":
    root = tk.Tk()
    app = ASRApp(root)
    root.mainloop()