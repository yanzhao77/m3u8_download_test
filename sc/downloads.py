import subprocess

# ========== 2. 调用 yt-dlp 下载 ==========
def download_m3u8(m3u8_url, output_name):
    """
    使用 yt-dlp 调用系统命令下载 m3u8，并自动转换成 mp4
    """
    output_file = f"{output_name}.mp4"

    cmd = [
        "yt-dlp",
        "-N", "16",                   # 16线程下载
        "-o", output_file,           # 输出文件
        m3u8_url
    ]

    print(f"⬇️ 正在下载 {output_name} ...")
    subprocess.run(cmd)
    print(f"✅ 下载完成：{output_file}\n")

