# M3U8 批量下载器（Python + 多进程 + GUI + 断点续传）

本项目是一个 **全自动 M3U8 下载器**，支持：

- ✔ 自动解析网页播放页  
- ✔ 自动抓取播放列表（`ul#playlist`）  
- ✔ 自动提取每集 m3u8  
- ✔ 使用 `yt-dlp` 完整处理：m3u8 → ts → mp4  
- ✔ **多进程加速下载**  
- ✔ **断点续传（跳过已下载 mp4）**  
- ✔ **PyQt5 GUI 界面**  
- ✔ 可一键打包成 Windows EXE  
- ✔ 适用于 Python 3.14+

---

## 🚀 功能特点

### 🔍 自动解析网页
输入播放页面，例如：

https://xiaoxintv.cc/index.php/vod/play/id/205584/sid/1/nid/1.html


脚本会自动抓取：

- XPath：`//*[@id="playlist"]/li/a`
- 获取所有 ep 的链接
- 自动补全为绝对 URL

---

### 🎬 自动处理 M3U8（无需你手动下载 TS）
使用 **yt-dlp** 全流程下载：

- 自动抓取 m3u8
- 自动下载 ts 分片
- 自动合并为 mp4
- 自动断点续传  
- 已下载过则 **自动跳过**

---

### ⚡ 多进程加速
使用 `multiprocessing.Pool` 全 CPU 并行下载。

---

### 🖥️ GUI（PyQt5）
简单易用：

- 输入 URL
- 点击 “开始下载”
- 窗口中实时打印日志

---

### 📦 打包成 EXE
一键生成独立 `gui_downloader.exe`

```
pyinstaller -F -w gui_downloader.py 
```

📁 项目结构
```bash
├── gui_downloader.py   # 主程序（PyQt5 GUI + 解析 + 下载）
├── downloads/          # 下载目录（自动创建）
└── README.md           # 项目说明
```

🛠️ 安装依赖
```
pip install requests lxml yt-dlp PyQt5
```
▶ 运行
```
python gui_downloader.py
```
📦 打包 EXE（Windows）
```
pip install pyinstaller
pyinstaller -F -w gui_downloader.py
```

生成：
```
dist/gui_downloader.exe
```
❤️ 贡献 & 建议

欢迎提 Issue 或 PR，我可以协助你继续扩展：

 进度条（实时速度 MB/s）

 支持代理

 自动下载整部剧所有剧集

 失败重试

 文件名自动获取视频标题

 任务队列 + 暂停/继续

📧 联系

如需定制功能，可随时联系。