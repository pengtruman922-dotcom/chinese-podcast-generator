# 中文播客生成系统

将英文播客音频自动转换为中文播客的完整系统，支持ASR识别、AI翻译和TTS合成。

## 功能特点

- 🎙️ **自动识别**：支持英文音频ASR识别（火山引擎BigASR）
- 🌐 **智能翻译**：使用AI大模型翻译为自然流畅的中文对话（阿里通义千问）
- 🔊 **语音合成**：生成高质量中文播客音频（火山引擎TTS 2.0）
- 📊 **任务管理**：Web界面管理所有任务，查看处理进度
- 🔄 **断点续传**：任务失败支持从失败阶段继续处理
- 📝 **长文本支持**：自动分段处理超长文本，避免翻译超时

## 系统架构

### 后端
- FastAPI：异步API服务
- Python 3.8+
- 火山引擎 TOS/ASR/TTS 服务
- 阿里云灵积 DashScope（通义千问）

### 前端
- React + TypeScript
- Vite
- Tailwind CSS

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-username/chinese-podcast-generator.git
cd chinese-podcast-generator
```

### 2. 配置后端

#### 安装依赖

```bash
pip install -r requirements.txt
```

#### 配置密钥

```bash
# 复制配置示例文件
cp config.example.py config.py

# 编辑 config.py，填入真实的密钥信息
```

需要配置的服务：
- **火山引擎 TOS**：对象存储服务（存储音频文件）
- **火山引擎 BigASR**：语音识别服务（识别英文）
- **阿里云灵积 DashScope**：AI翻译服务（通义千问）
- **火山引擎 TTS**：语音合成服务（合成中文语音）

#### 创建必要目录

```bash
mkdir uploads output temp
```

#### 启动后端服务

```bash
python api_server.py
```

后端服务运行在 `http://localhost:8000`

### 3. 配置前端

```bash
cd frontend-demo/transtube-main

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务运行在 `http://localhost:5173`

## 使用说明

1. 打开浏览器访问 `http://localhost:5173`
2. 点击"上传文件"按钮，选择英文音频文件（支持 mp3, wav, mp4, m4a, flac）
3. 系统自动处理：
   - 上传到对象存储
   - ASR语音识别
   - AI翻译为中文对话
   - TTS合成中文音频
4. 处理完成后点击"下载"获取中文播客音频

### 任务管理

- **查看任务**：点击任务卡片查看详细信息（ASR结果、翻译内容）
- **继续处理**：失败任务可点击"继续"按钮断点续传
- **删除任务**：点击删除图标移除任务及相关文件

### 系统设置

点击"设置"按钮可配置：
- ASR/TTS/翻译服务参数
- TTS音色选择（支持多种音色）
- 系统提示词自定义

## API 接口

后端提供以下REST API：

- `POST /api/upload` - 上传音频文件
- `GET /api/tasks` - 获取任务列表
- `GET /api/tasks/{task_id}` - 查询任务状态
- `GET /api/tasks/{task_id}/details` - 获取任务详情
- `POST /api/tasks/{task_id}/resume` - 续传失败任务
- `DELETE /api/tasks/{task_id}` - 删除任务
- `GET /api/download/{filename}` - 下载生成的音频
- `GET /api/config` - 获取系统配置
- `POST /api/config` - 更新系统配置

详细API文档请参考 `api-specs/` 目录。

## 项目结构

```
.
├── api_server.py              # FastAPI后端服务
├── utils.py                   # 工具类（TOS/ASR/TTS/翻译客户端）
├── config.py                  # 配置文件（需自行创建）
├── config.example.py          # 配置示例
├── requirements.txt           # Python依赖
├── tasks_db.json             # 任务持久化存储
├── uploads/                   # 上传文件目录
├── output/                    # 生成的音频文件
├── temp/                      # 临时文件（ASR/翻译结果）
└── frontend-demo/
    └── transtube-main/        # React前端项目
```

## 注意事项

1. **密钥安全**：请勿将 `config.py` 提交到git仓库
2. **文件大小**：大文件（>100M）处理时间较长，建议使用较快的翻译模型
3. **成本控制**：ASR/TTS/翻译服务按量计费，注意控制使用量
4. **音频格式**：建议使用 mp3 或 wav 格式
5. **长文本**：超过1万字符的文本会自动分段翻译（每段10000±1000字符）

## 技术特性

### 智能分段翻译
- 检测文本长度，超过10000字符自动分段
- 按说话人边界分割，避免切断完整对话
- 分段范围：10000±1000字符
- 自动按原顺序合并翻译结果

### 断点续传机制
- 记录处理阶段（upload/asr/translate/tts）
- 保存中间结果到临时文件
- 失败后可从断点继续，无需重新处理

### 任务持久化
- JSON文件存储任务状态
- 重启服务后任务不丢失
- 支持查看历史任务

## 常见问题

**Q: 翻译失败提示504超时？**  
A: 音频过长导致翻译文本过多，系统已支持自动分段翻译。

**Q: 任务失败后如何恢复？**  
A: 点击失败任务的"继续"按钮，系统会从失败阶段继续处理。

**Q: 如何更换TTS音色？**  
A: 进入"设置"页面，在TTS配置中选择不同的音色。

**Q: 前端页面刷新后任务消失？**  
A: 已修复，任务存储在 `tasks_db.json` 中，刷新不会丢失。

## License

MIT

## 联系方式

如有问题或建议，欢迎提Issue。
