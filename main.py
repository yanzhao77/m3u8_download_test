import sys
import os
import requests
from lxml import etree
from multiprocessing import Pool, cpu_count
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QTextEdit, QLineEdit, QLabel
)
from PyQt5.QtCore import Qt
import yt_dlp


# -----------------------------
# 页面解析：获取 m3u8 链接
# -----------------------------
def fetch_m3u8_from_page(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    html = requests.get(url, headers=headers).text
    tree = etree.HTML(html)

    # 你自己给的 playlist xpath
    lis = tree.xpath('//*[@id="playlist"]/li/a')

    result = []
    for a in lis:
        href = a.get("href")
        if href:
            if not href.startswith("http"):
                href = "https://xiaoxintv.cc" + href
            result.append(href)

    return result


# -----------------------------
# yt-dlp 下载一个 m3u8
# -----------------------------
def download_m3u8(m3u8_url):
    out_dir = "downloads"
    os.makedirs(out_dir, exist_ok=True)

    ydl_opts = {
        "outtmpl": out_dir + "/%(title)s.%(ext)s",
        "merge_output_format": "mp4",
        "concurrent_fragment_downloads": 10,
        "continue": True,     # 断点续传
        "n_threads": 4,
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([m3u8_url])

    return f"完成：{m3u8_url}"


# -----------------------------
# GUI 主窗口
# -----------------------------
class MainGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("M3U8 批量下载器（多进程 + 断点续传）")
        self.resize(600, 400)

        layout = QVBoxLayout()

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("输入播放页面地址，例如：https://xiaoxintv.cc/index.php/vod/play/id/205584/sid/1/nid/1.html")
        layout.addWidget(self.url_input)

        self.btn_start = QPushButton("抓取并下载")
        self.btn_start.clicked.connect(self.start_task)
        layout.addWidget(self.btn_start)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def log(self, text):
        self.log_output.append(text)
        self.log_output.ensureCursorVisible()

    def start_task(self):
        url = self.url_input.text().strip()
        if not url:
            self.log("❌ 请输入地址！")
            return

        self.log("🔍 正在解析页面...")
        try:
            m3u8_list = fetch_m3u8_from_page(url)
        except Exception as e:
            self.log("❌ 页面解析失败：" + str(e))
            return

        self.log(f"🔗 共解析到 {len(m3u8_list)} 个播放链接")

        if not m3u8_list:
            self.log("❌ 没有找到任何 m3u8 链接")
            return

        self.log("🚀 开始多进程下载...")

        pool = Pool(cpu_count())
        for m3u8_url in m3u8_list:
            pool.apply_async(download_m3u8, args=(m3u8_url,), callback=self.log)

        pool.close()
        pool.join()

        self.log("🎉 全部下载完成！")


# -----------------------------
# 入口
# -----------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = MainGUI()
    gui.show()
    sys.exit(app.exec_())
