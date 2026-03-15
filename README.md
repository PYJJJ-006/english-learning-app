# 英语背诵学习软件

通过背诵B站视频中的英文内容来提升英语能力的学习工具。

## 功能特点

- 📥 **视频导入**：粘贴B站视频链接，自动下载并处理
- 🎵 **音频转录**：使用 faster-whisper 将音频转录为英文文本
- 🌐 **智能翻译**：调用火山引擎大模型，生成中英双语对照
- ✍️ **默写练习**：看中文句子，默写英文句子
- 📊 **答案对比**：提交后查看正确答案，对比学习
- 📱 **移动端阅读**：手机浏览器阅读模式，支持查看/隐藏答案

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

如需使用「视频导入/转录/翻译」完整流程，请额外安装：

```bash
pip install yt-dlp faster-whisper volcenginesdkarkruntime
```

### 2. 启动应用

**方式一：双击启动脚本**
```bash
双击 start.sh 文件
```

**方式二：命令行启动**
```bash
python3 app.py
```

### 3. 访问应用

打开浏览器访问：http://127.0.0.1:5000

## 部署（Vercel）

1. 在 Vercel 创建新项目并导入该仓库
2. 项目根目录已包含 `vercel.json`，无需额外构建命令
3. 在 Vercel 配置环境变量（至少包含）：
   - `ARK_API_KEY`
   - `ARK_ENDPOINT_ID`
   - `ARK_BASE_URL`（可选，默认 https://ark.cn-beijing.volces.com/api/v3）
4. 部署完成后直接访问 Vercel 提供的域名
5. 由于云端限制，Vercel 仅保留「粘贴材料/练习/移动端阅读」，导入 B 站视频会提示不可用

## 手机访问（局域网）

1. 确保电脑与手机处于同一 Wi‑Fi
2. 用以下命令启动并监听所有网卡：

```bash
FLASK_APP=app.py flask run --host 0.0.0.0 --port 5000
```

3. 在手机浏览器打开 `http://<电脑局域网IP>:5000`

## 桌面版（Tauri）

桌面版会自动启动本地 Flask 服务，并用桌面窗口加载 `http://127.0.0.1:5000`，实现“像 App 一样点开即用”。

### 前置依赖

1. 安装 Node.js 18+ 与 Rust 工具链
2. 安装 Python 依赖（完整导入流程需要额外依赖）

```bash
pip install -r requirements.txt
pip install yt-dlp faster-whisper volcenginesdkarkruntime
```

### 开发模式运行

```bash
cd desktop
npm install
npm run dev
```

### 打包与使用

```bash
cd desktop
npm run build
```

打包完成后，在以下目录找到桌面应用并双击运行：

- `desktop/src-tauri/target/release/bundle/macos/BackIt.app`

如果提示找不到 `cargo`，请先执行：

```bash
source "$HOME/.cargo/env"
```

如果提示找不到 `python3`，可以在启动前设置：

```bash
export PYTHON_BIN="/usr/bin/python3"
```

### 桌面版数据与密钥位置（macOS）

桌面版会将数据与配置写入用户目录，避免写入应用包：

- 数据目录：`~/Library/Application Support/BackIt/data`
- 密钥文件：`~/Library/Application Support/BackIt/ARK_API_KEY.env`
- Cookie 文件：`~/Library/Application Support/BackIt/data/cookies.txt`

你可以在上述目录创建 `ARK_API_KEY.env`，内容与本地开发一致：

```
export ARK_API_KEY="your-api-key"
export ARK_ENDPOINT_ID="your-endpoint-id"
export ARK_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
```

## 使用说明

### 导入视频

1. 点击「导入视频」或访问 http://127.0.0.1:5000/import
2. 粘贴B站视频链接（如 `https://www.bilibili.com/video/BV1NubkzEE3w`）
3. 点击「开始导入」，等待处理完成
4. 自动跳转到练习页面

### 练习模式

1. 页面显示中文句子
2. 在输入框中写出对应的英文句子
3. 点击「提交答案」查看对比
4. 使用「上一句」「下一句」翻页

### 移动端阅读模式

1. 列表页点击「阅读模式」进入手机阅读页
2. 通过「查看答案/隐藏答案」按钮切换显示
3. 点击「下一句」继续阅读

## 配置说明

### API 密钥配置

复制 `ARK_API_KEY.env.example` 为 `ARK_API_KEY.env`，并在其中配置火山引擎 API（该文件已加入 .gitignore，不会提交）：

```bash
cp ARK_API_KEY.env.example ARK_API_KEY.env
```

编辑 `ARK_API_KEY.env` 文件：

```
export ARK_API_KEY="your-api-key"
export ARK_ENDPOINT_ID="your-endpoint-id"
export ARK_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
```

### Cookie 配置

如果 B站视频需要登录才能观看，需要更新 `cookies.txt` 文件（该文件已加入 .gitignore，不会提交）：

1. 安装 Chrome 扩展 [EditThisCookie](https://chromewebstore.google.com/detail/editthiscookie/)
2. 登录 B站
3. 使用扩展导出 Cookie 为 Netscape 格式
4. 替换项目中的 `cookies.txt` 文件

## 项目结构

```
mobileversion v1/
├── app.py                 # Flask 主应用
├── config.py              # 配置管理
├── start.sh               # 启动脚本
├── requirements.txt       # 依赖包
├── ARK_API_KEY.env        # API 密钥配置（本地文件，已忽略）
├── cookies.txt            # B站 Cookie（本地文件，已忽略）
├── data/                  # 数据目录（运行时生成，已忽略）
│   ├── videos/           # 视频练习集
│   └── app.db            # SQLite 数据库
├── services/              # 业务逻辑
│   ├── video_downloader.py
│   ├── transcriber.py
│   ├── translator.py
│   └── video_processor.py
├── templates/             # HTML 模板
│   ├── mobile_reading.html
└── static/                # 静态文件
```

## 技术栈

- **后端**: Flask
- **视频下载**: yt-dlp
- **音频转录**: faster-whisper（默认 medium，可配置）
- **大模型**: 火山引擎 ARK API (doubao-seed-2-0-mini)
- **数据库**: SQLite

## 常见问题

### Cookie 过期怎么办？

重新从浏览器导出 Cookie 并替换 `cookies.txt` 文件。

### 导入时报 HTTP 412（Precondition Failed）怎么办？

这通常是 B 站风控/反爬触发导致（常见原因：Cookie 未生效或已过期、网络环境异常、短时间请求过频）。

建议按顺序排查：
1. 重新登录 B 站后导出最新 `cookies.txt`（Netscape 格式，需包含 `SESSDATA` 等）。
2. 更换网络环境或关闭代理/VPN，稍后重试。
3. 如仍不稳定，可通过环境变量覆盖请求头（可选）：

```bash
export BILIBILI_USER_AGENT="你的浏览器 UA"
export BILIBILI_REFERER="https://www.bilibili.com/"
export BILIBILI_ORIGIN="https://www.bilibili.com"
```

### 转录速度慢？

首次使用 faster-whisper 会下载模型，请耐心等待。转录耗时主要取决于模型大小与设备性能，可通过环境变量提速（推荐先用小模型跑通流程）：

```bash
export WHISPER_MODEL_SIZE="small"     # tiny / base / small / medium / large-v3
export WHISPER_DEVICE="cpu"          # 有 CUDA 环境可设为 cuda
export WHISPER_COMPUTE_TYPE="auto"   # 自动选择更快/更省内存的计算类型
export WHISPER_BEAM_SIZE="1"         # 越小越快
export WHISPER_BEST_OF="1"           # 越小越快
export WHISPER_TEMPERATURE="0.0"     # 固定温度更快更稳定
export WHISPER_CHUNK_LENGTH="30"     # 分段处理，通常更稳
export WHISPER_VAD_FILTER="true"     # 过滤静音段，通常更快
export WHISPER_MIN_SILENCE_DURATION_MS="500"
```

如果页面提示“处理超时”，通常是转录阶段长时间没有进度更新导致；已改为保持连接不断开并在转录过程中持续推送进度。

### 支持哪些视频？

目前仅支持 B站视频，视频内容应为英文（如英文博客、演讲等）。
