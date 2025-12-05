import os
import json
import subprocess
from multiprocessing import Pool, cpu_count
from playwright.sync_api import sync_playwright


# ============================================
# 1. 获取剧集播放页（从 playlist ul → li）
# ============================================
def find_page(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        page.wait_for_selector("#playlist")

        li_list = page.query_selector_all('//*[@id="playlist"]/li')

        href_map = {}
        for li in li_list:
            a = li.query_selector("a")
            if a:
                name = a.inner_text().strip()
                href = a.get_attribute("href")
                href_map[name] = href

        browser.close()
        return href_map


# ============================================
# 2. 获取 m3u8
# ============================================
def get_m3u8(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        m3u8_list = []

        def on_request(request):
            req_url = request.url
            if ".m3u8" in req_url:
                print("🎯 捕获到 M3U8:", req_url)
                m3u8_list.append(req_url)

        page.on("request", on_request)
        print(f"⏳ 加载页面：{url}")

        page.goto(url)
        page.wait_for_timeout(5000)

        browser.close()
        return list(set(m3u8_list))


# ============================================
# 3. 多进程 + yt-dlp 下载
# ============================================
def download_one(args):
    ep_name, m3u8_url, save_dir = args
    output_path = os.path.join(save_dir, ep_name + ".mp4")

    cmd = [
        "yt-dlp",
        "-N", "16",          # 16线程下载
        "-o", output_path,
        m3u8_url
    ]

    print(f"\n⬇️ 下载开始：{ep_name}")
    subprocess.run(cmd)
    print(f"✅ 完成：{output_path}")

    return True


def parallel_download(m3u8_map, save_dir):
    tasks = []
    for ep_name, m3u8_url in m3u8_map.items():
        tasks.append((ep_name, m3u8_url, save_dir))

    workers = min(len(tasks), cpu_count())
    print(f"\n🔥 多进程下载启动：{workers} workers\n")

    with Pool(workers) as pool:
        pool.map(download_one, tasks)


# ============================================
# 4. 主函数：全集自动化
# ============================================
if __name__ == "__main__":
    root_page = "https://xiaoxintv.cc/index.php/vod/play/id/205584/sid/1/nid/1.html"
    base_url = "https://xiaoxintv.cc/"
    save_dir = r"E:\video\生活大爆炸 第五季"

    os.makedirs(save_dir, exist_ok=True)

    print("🔍 获取剧集列表...")
    ep_map = find_page(root_page)

    all_m3u8 = {}

    # 遍历每一集
    for ep_name, ep_path in ep_map.items():
        play_url = base_url + ep_path
        print(f"\n====== 处理 {ep_name} ======")
        print(f"播放页：{play_url}")

        m3u8_list = get_m3u8(play_url)
        if not m3u8_list:
            print("❌ 没有找到 m3u8")
            continue

        # 只取第一个
        all_m3u8[ep_name] = m3u8_list[0]

        print(f"🎯 {ep_name} → {m3u8_list[0]}")

    # 保存 JSON
    json_path = os.path.join(save_dir, "m3u8_list.json")
    json.dump(all_m3u8, open(json_path, "w", encoding="utf-8"), ensure_ascii=False, indent=4)

    print("\n📄 已写入 m3u8 列表：", json_path)

    # ========= 开始多进程下载 =========
    parallel_download(all_m3u8, save_dir)

    print("\n================ 全部完成！ ================")
