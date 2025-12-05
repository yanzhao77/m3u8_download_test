# single_script.py
# 全自动：抓集数 → 抓 m3u8 → 下载 ts → 合成 mp4

from playwright.sync_api import sync_playwright
import json
import os
import subprocess
import time


# ============================================================
# 1) 获取当前剧集下所有集数的播放链接
# ============================================================
def find_all_episodes(url: str):
    print(f"\n⏳ 正在获取集数列表：{url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)

        page.wait_for_selector("#playlist")

        li_elements = page.query_selector_all('//*[@id="playlist"]/li')

        episode_map = {}

        for li in li_elements:
            a = li.query_selector("a")
            if a:
                name = a.inner_text().strip()
                href = a.get_attribute("href")
                episode_map[name] = href

        print(f"📌 找到 {len(episode_map)} 集")
        browser.close()
        return episode_map


# ============================================================
# 2) 自动监听网络请求，获取 m3u8 链接
# ============================================================
def fetch_m3u8(url: str):
    print(f"\n🎬 正在抓取 m3u8：{url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        m3u8_links = []

        def on_request(req):
            req_url = req.url
            if ".m3u8" in req_url:
                print("🎯 捕获到 M3U8：", req_url)
                m3u8_links.append(req_url)

        page.on("request", on_request)
        page.goto(url, timeout=30000)
        time.sleep(5)

        browser.close()

    if m3u8_links:
        return list(set(m3u8_links))

    print("❌ 未找到 m3u8")
    return []


# ============================================================
# 3) 调用 yt-dlp 下载并转 MP4
# ============================================================
def download_m3u8(m3u8_url, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    mp4_file = out_path + ".mp4"

    print(f"\n⬇️ 下载中：{mp4_file}")

    cmd = [
        "yt-dlp",
        "-N", "16",
        "-o", mp4_file,
        m3u8_url
    ]

    subprocess.run(cmd)
    print(f"✅ 下载完成：{mp4_file}")


# ============================================================
# 4) 主流程：一键自动化
# ============================================================
def main():
    # ------------------------------
    # 配置区
    # ------------------------------
    start_url = "https://xiaoxintv.cc/index.php/vod/play/id/205584/sid/1/nid/1.html"
    base = "https://xiaoxintv.cc/"
    save_dir = r"E:\video\生活大爆炸 第五季\\"
    json_name = "生活大爆炸_第五季_m3u8.json"
    # ------------------------------

    os.makedirs(save_dir, exist_ok=True)

    # ① 获取所有集
    episode_map = find_all_episodes(start_url)

    all_m3u8 = {}

    # ② 循环处理每一集
    for ep_name, ep_href in episode_map.items():
        play_url = base + ep_href
        print(f"\n=========== 正在处理 {ep_name} ===========")
        print("播放地址：", play_url)

        # 抓 m3u8
        m3u8_list = fetch_m3u8(play_url)
        if not m3u8_list:
            print("⚠️ 跳过本集（无 m3u8）")
            continue

        # 一般是第二个，但以第一个为主文件
        m3u8_url = m3u8_list[0]
        all_m3u8[ep_name] = m3u8_url

        # 下载
        out_path = os.path.join(save_dir, ep_name)
        download_m3u8(m3u8_url, out_path)

    # ③ 保存 m3u8 汇总
    json_path = os.path.join(save_dir, json_name)
    json.dump(all_m3u8, open(json_path, "w", encoding="utf-8"), ensure_ascii=False, indent=4)

    print("\n================ DONE! 所有任务完成！ ================")
    print("m3u8 文件记录：", json_path)


if __name__ == "__main__":
    main()
