import gradio as gr
import asyncio
import aiohttp
import json
import base64
import wave
import os
import time
import sys
from datetime import datetime

# ==========================================
# 0. 消除 Windows asyncio 报错噪音
# ==========================================
# 这是一个针对 Windows ProactorEventLoop 的补丁，用于忽略无害的 ConnectionResetError
from functools import wraps
from asyncio.proactor_events import _ProactorBasePipeTransport


def silence_event_loop_closed(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except RuntimeError:
            pass

    return wrapper


if sys.platform == 'win32':
    _ProactorBasePipeTransport.__del__ = silence_event_loop_closed(_ProactorBasePipeTransport.__del__)

# ==========================================
# 1. 音色数据库
# ==========================================
RES_ID_2_0 = "seed-tts-2.0"
RES_ID_1_0 = "volc.service_type.10029"

VOICE_DATABASE = {
    RES_ID_2_0: {
        "通用/视频配音 (2.0)": [
            ("Vivi (中英)", "zh_female_vv_uranus_bigtts"),
            ("小何 (通用女)", "zh_female_xiaohe_uranus_bigtts"),
            ("云舟 (通用男)", "zh_male_m191_uranus_bigtts"),
            ("小天 (通用男)", "zh_male_taocheng_uranus_bigtts"),
            ("大壹 (视频配音)", "zh_male_dayi_saturn_bigtts"),
            ("魅力女友 (视频)", "zh_female_meilinvyou_saturn_bigtts"),
            ("儒雅逸辰 (视频)", "zh_male_ruyayichen_saturn_bigtts"),
        ],
        "角色扮演 (2.0)": [
            ("可爱女生", "saturn_zh_female_keainvsheng_tob"),
            ("调皮公主", "saturn_zh_female_tiaopigongzhu_tob"),
            ("爽朗少年", "saturn_zh_male_shuanglangshaonian_tob"),
            ("天才同桌", "saturn_zh_male_tiancaitongzhuo_tob"),
            ("知性灿灿", "saturn_zh_female_cancan_tob"),
        ],
        "端到端-O版本 (2.0)": [
            ("Vivi (O版)", "zh_female_vv_jupiter_bigtts"),
            ("小何 (O版)", "zh_female_xiaohe_jupiter_bigtts"),
            ("云舟 (O版)", "zh_male_yunzhou_jupiter_bigtts"),
        ]
    },
    RES_ID_1_0: {
        "多情感精品 (1.0)": [
            ("爽快思思 (多情感)", "zh_female_shuangkuaisisi_emo_v2_mars_bigtts"),
            ("灿灿 (多情感)", "zh_female_cancan_mars_bigtts"),
            ("温暖阿虎 (多情感)", "zh_male_wennuanahu_moon_bigtts"),
            ("儒雅男友 (多情感)", "zh_male_ruyayichen_emo_v2_mars_bigtts"),
            ("高冷御姐 (多情感)", "zh_female_gaolengyujie_emo_v2_mars_bigtts"),
            ("傲娇霸总 (多情感)", "zh_male_aojiaobazong_emo_v2_mars_bigtts"),
            ("京腔侃爷 (多情感)", "zh_male_jingqiangkanye_emo_mars_bigtts"),
        ],
        "方言/特色 (1.0)": [
            ("北京小爷 (北京话)", "zh_male_beijingxiaoye_moon_bigtts"),
            ("呆萌川妹 (四川话)", "zh_female_daimengchuanmei_moon_bigtts"),
            ("粤语小溏 (粤语)", "zh_female_yueyunv_mars_bigtts"),
            ("湾湾小何 (台湾话)", "zh_female_wanwanxiaohe_moon_bigtts"),
            ("东北老铁", "zh_male_dongbei_laotie_bigtts"),
            ("广西远舟", "zh_male_guangxiyuanzhou_moon_bigtts"),
        ],
        "IP仿音/趣味 (1.0)": [
            ("孙悟空", "zh_male_sunwukong_mars_bigtts"),
            ("猪八戒", "zh_male_zhubajie_mars_bigtts"),
            ("熊二", "zh_male_xionger_mars_bigtts"),
            ("佩奇猪", "zh_female_peiqi_mars_bigtts"),
            ("林潇 (杨幂风)", "zh_female_yangmi_mars_bigtts"),
            ("玲玲姐姐 (志玲风)", "zh_female_linzhiling_mars_bigtts"),
            ("周杰伦风", "zh_male_zhoujielun_emo_v2_mars_bigtts"),
        ],
        "英文专用 (1.0)": [
            ("Starry (通用)", "en_female_starry_moon_bigtts"),
            ("Candice (美式)", "en_female_candice_emo_v2_mars_bigtts"),
            ("Jackson (美式)", "en_male_jackson_mars_bigtts"),
            ("Emily (英式)", "en_female_emily_mars_bigtts"),
        ],
        "常用ICL角色 (1.0)": [
            ("温柔文雅", "ICL_zh_female_wenrouwenya_tob"),
            ("霸道总裁", "ICL_zh_male_badaozongcai_v1_tob"),
            ("病娇姐姐", "ICL_zh_female_bingjiaojiejie_tob"),
            ("奶气萌娃", "zh_male_naiqimengwa_mars_bigtts"),
            ("悬疑解说", "zh_male_changtianyi_mars_bigtts"),
        ]
    }
}


def get_flat_voices(res_id):
    if res_id not in VOICE_DATABASE: return []
    choices = []
    for category, voice_list in VOICE_DATABASE[res_id].items():
        for name, vid in voice_list:
            display_name = f"【{category}】{name}"
            choices.append((display_name, vid))
    return choices


# ==========================================
# 2. 后端逻辑 (已优化Session复用)
# ==========================================

DEFAULT_API_URL = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
SAMPLE_RATE = 24000


def generate_silence_pcm(duration_ms):
    if duration_ms <= 0: return b""
    num_bytes = int((SAMPLE_RATE * 2 * 1) * (duration_ms / 1000))
    if num_bytes % 2 != 0: num_bytes += 1
    return b'\x00' * num_bytes


# 注意：这里多接收了一个 session 参数
async def fetch_tts_pcm(session, text, speaker_id, app_id, token, cluster, req_id):
    headers = {
        "Authorization": f"Bearer; {token}",
        "X-Api-App-Id": app_id,
        "X-Api-Access-Key": token,
        "X-Api-Resource-Id": cluster,
        "X-Api-Request-Id": req_id
    }
    payload = {
        "req_params": {
            "text": text,
            "speaker": speaker_id,
            "audio_params": {"format": "pcm", "sample_rate": SAMPLE_RATE}
        }
    }

    full_pcm = bytearray()
    try:
        async with session.post(DEFAULT_API_URL, json=payload, headers=headers) as resp:
            if resp.status != 200:
                err_text = await resp.text()
                return None, f"HTTP {resp.status}: {err_text[:200]}"

            async for line in resp.content:
                if not line: continue
                try:
                    line_str = line.decode('utf-8').strip()
                    if not line_str: continue
                    data = json.loads(line_str)

                    if "code" in data and data["code"] != 0 and data["code"] != 20000000:
                        return None, f"API Error {data['code']}: {data['message']}"

                    if "data" in data and data["data"]:
                        full_pcm.extend(base64.b64decode(data["data"]))
                except Exception:
                    continue
        return full_pcm, None
    except Exception as e:
        return None, str(e)


async def run_pipeline(app_id, token, resource_id, dialogues, speaker_map, concurrency, p_same, p_diff, output_dir,
                       progress=gr.Progress()):
    if not app_id or not token: return None, "❌ 请填写 App ID 和 Token"
    os.makedirs(output_dir, exist_ok=True)

    results = [None] * len(dialogues)
    errors = []
    sem = asyncio.Semaphore(concurrency)

    # 【优化】在这里创建唯一的 Session，所有 workers 共享
    async with aiohttp.ClientSession() as session:
        async def worker(idx, item):
            spk_label = item.get("speaker")
            text = item.get("text")
            real_vid = speaker_map.get(spk_label)

            if not real_vid:
                real_vid = list(speaker_map.values())[0] if speaker_map else ""

            if not real_vid:
                errors.append(f"#{idx + 1} 未找到音色映射")
                return

            async with sem:
                # 传入共享的 session
                pcm, err = await fetch_tts_pcm(session, text, real_vid, app_id, token, resource_id, f"req_{idx}")
                if err:
                    errors.append(f"#{idx + 1} 失败: {err}")
                else:
                    results[idx] = {"pcm": pcm, "speaker": spk_label}
                    # 减少等待时间，因为复用连接更快
                    await asyncio.sleep(0.01)

        tasks = [worker(i, d) for i, d in enumerate(dialogues)]

        # 进度条
        done_count = 0
        progress(0, desc="🚀 初始化并发任务...")

        # 使用 asyncio.gather 并发执行，但为了进度条，我们需要稍微包装一下或者简单使用 gather
        # 为了兼容性，这里使用 gather 等待所有完成，如果需要实时进度条建议用 as_completed
        # 这里用 as_completed 逻辑
        running_tasks = [asyncio.create_task(worker(i, d)) for i, d in enumerate(dialogues)]
        for f in asyncio.as_completed(running_tasks):
            await f
            done_count += 1
            progress(done_count / len(dialogues), desc=f"合成中 {done_count}/{len(dialogues)}")

        if errors:
            return None, f"❌ 合成存在错误:\n" + "\n".join(errors[:5])

    # 拼接 (session 已自动关闭)
    progress(0.95, desc="✂️ 拼接音频...")
    final_pcm = bytearray()
    last_spk = None
    for res in results:
        if not res: continue
        pause = 0
        if last_spk:
            pause = p_same if res["speaker"] == last_spk else p_diff
        if pause > 0: final_pcm.extend(generate_silence_pcm(pause))

        final_pcm.extend(res["pcm"])
        last_spk = res["speaker"]

    # 保存
    ts = datetime.now().strftime("%H%M%S")
    outfile = os.path.join(output_dir, f"result_{ts}.wav")
    try:
        with wave.open(outfile, 'wb') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(SAMPLE_RATE)
            f.writeframes(final_pcm)
        # 返回文件路径
        return outfile, f"✅ 成功! 文件已保存: {outfile}"
    except Exception as e:
        return None, f"保存失败: {e}"


# ==========================================
# 3. 界面逻辑
# ==========================================

def handle_run(app_id, token, res_id, spk1_vid, spk2_vid, file, text, conc, p1, p2, out):
    content = ""
    if file:
        with open(file.name, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = text

    try:
        if content.strip().startswith("[") and "'" in content: content = content.replace("'", '"')
        data = json.loads(content)
        if isinstance(data, dict): data = data.get("dialogues", [])
    except:
        return None, None, "❌ JSON格式解析失败"  # 注意返回个数对应 outputs

    spk_map = {
        "发言者1": spk1_vid, "Speaker1": spk1_vid, "A": spk1_vid,
        "发言者2": spk2_vid, "Speaker2": spk2_vid, "B": spk2_vid
    }

    path, msg = asyncio.run(run_pipeline(app_id, token, res_id, data, spk_map, conc, p1, p2, out))

    # 返回 path 两次：一次给 Audio 播放，一次给 File 下载
    if path:
        return path, path, msg
    else:
        return None, None, msg


def update_voices(resource_id):
    new_choices = get_flat_voices(resource_id)
    val1 = new_choices[0][1] if len(new_choices) > 0 else None
    val2 = new_choices[1][1] if len(new_choices) > 1 else val1
    return gr.Dropdown(choices=new_choices, value=val1), gr.Dropdown(choices=new_choices, value=val2)


# ==========================================
# 4. Gradio 构建
# ==========================================
with gr.Blocks(title="VolcTTS Pro") as demo:
    gr.Markdown("## 🎙️ 火山引擎多人对话合成 (Pro版)")

    with gr.Row():
        with gr.Column():
            app_id = gr.Textbox(label="App ID")
            token = gr.Textbox(label="Access Token", type="password")
            res_id = gr.Dropdown(
                choices=[("TTS 1.0 标准版/方言/IP (10029)", RES_ID_1_0), ("TTS 2.0 最新版 (seed-tts-2.0)", RES_ID_2_0)],
                value=RES_ID_1_0,
                label="模型版本"
            )
            spk1 = gr.Dropdown(label="发言者1", interactive=True)
            spk2 = gr.Dropdown(label="发言者2", interactive=True)
            conc = gr.Slider(1, 10, 5, step=1, label="并发数")
            p_same = gr.Slider(0, 2000, 300, label="同人停顿(ms)")
            p_diff = gr.Slider(0, 2000, 600, label="换人停顿(ms)")

        with gr.Column():
            txt_in = gr.TextArea(label="JSON内容",
                                 value='[{"speaker":"发言者1","text":"你好"},{"speaker":"发言者2","text":"下载功能已经加上了"}]')
            file_in = gr.File(label="或上传文件")
            btn = gr.Button("🚀 开始合成", variant="primary")
            out_log = gr.Textbox(label="状态")

            # 【新增】专门的下载区域
            gr.Markdown("### 结果下载区")
            with gr.Row():
                out_audio = gr.Audio(label="在线试听", type="filepath")
                # 新增 File 组件，支持点击下载
                out_file = gr.File(label="下载wav文件", type="filepath")

    res_id.change(fn=update_voices, inputs=res_id, outputs=[spk1, spk2])
    demo.load(fn=update_voices, inputs=res_id, outputs=[spk1, spk2])

    # 注意 outputs 增加了 out_file
    btn.click(handle_run,
              [app_id, token, res_id, spk1, spk2, file_in, txt_in, conc, p_same, p_diff,
               gr.Textbox(value="output", visible=False)],
              [out_audio, out_file, out_log])

if __name__ == "__main__":
    demo.queue().launch(inbrowser=True)