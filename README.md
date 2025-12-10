# M3U8 视频批量下载器

本项目是一个全自动 M3U8 视频下载工具，专为从特定网站批量下载电视剧集而设计。它能够自动解析网页、抓取播放列表、提取 m3u8 地址，并使用 `yt-dlp` 完整处理下载和转换过程。

## 🎯 主要特性

- ✔ 自动解析网页播放页
- ✔ 自动抓取播放列表（`ul#playlist`）
- ✔ 自动提取每集 m3u8 地址
- ✔ 使用 `yt-dlp` 完整处理：m3u8 → ts → mp4
- ✔ 多进程加速下载
- ✔ 断点续传（跳过已下载的 mp4）
- ✔ 支持代理池绕过反爬机制
- ✔ 可一键打包成 Windows EXE
- ✔ 适用于 Python 3.7+

## 📁 项目结构

```
.
├── main.py                     # 基础版本下载器
├── multiprocessing_main.py     # 多进程版本下载器
├── multiprocessing_main_2.0.py # 增强版多进程下载器
├── tv_spider_enhanced.py       # 带代理池的增强版下载器
├── sc/                         # 模块化版本
│   ├── downloads.py
│   ├── findhtml.py
│   ├── get_m3u8.py
│   └── sc_main.py
└── README.md                   # 项目说明文档
```

## 🚀 功能详解

### 🔍 自动解析网页播放列表

程序可以自动解析指定网站的播放页面，例如：

```
https://xiaoxintv.cc/index.php/vod/play/id/205584/sid/1/nid/1.html
```

脚本会自动抓取：

- XPath：`//*[@id="playlist"]/li/a`
- 获取所有剧集的链接
- 自动补全为绝对 URL

### 🎬 自动处理 M3U8

使用强大的 `yt-dlp` 工具全流程处理下载：

- 自动抓取 m3u8 地址
- 自动下载 ts 分片
- 自动合并为 mp4 格式
- 自动断点续传
- 已下载过的剧集自动跳过

### ⚡ 多进程加速下载

使用 `multiprocessing.Pool` 实现全 CPU 并行下载，大幅提升下载效率。

### 🌐 代理池支持

增强版实现包含代理池功能，可以从多个免费代理源获取代理，帮助绕过网站的反爬虫机制。

## 🛠️ 安装依赖

```
pip install requests lxml yt-dlp playwright
```

如需打包为 EXE，还需要安装：

```
pip install pyinstaller
```

## ▶️ 运行方式

根据不同需求选择不同的脚本运行：

1. 基础版本：
   ```
   python main.py
   ```

2. 多进程版本：
   ```
   python multiprocessing_main.py
   ```

3. 增强版多进程（含反爬措施）：
   ```
   python multiprocessing_main_2.0.py
   ```

4. 带代理池的增强版：
   ```
   python tv_spider_enhanced.py
   ```

5. 模块化版本：
   ```
   python sc/sc_main.py
   ```

## 📦 打包为 EXE（Windows）

```
pyinstaller -F multiprocessing_main_2.0.py
```

生成的可执行文件位于：

```
dist/multiprocessing_main_2.0.exe
```

## ❤️ 贡献与建议

欢迎提交 Issue 或 PR，我可以协助您进一步扩展功能：

- [ ] 进度条（实时速度 MB/s）
- [ ] 更完善的代理支持
- [ ] 自动下载整部剧所有剧集
- [ ] 失败重试机制
- [ ] 文件名自动获取视频标题
- [ ] 任务队列管理 + 暂停/继续功能
- [ ] 图形界面版本

## 📧 联系方式

如需定制功能或其他问题，请随时联系。