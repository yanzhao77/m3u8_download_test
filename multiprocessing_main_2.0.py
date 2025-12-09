import os
import json
import subprocess
import time
from multiprocessing import Pool, cpu_count
import random

from playwright.sync_api import sync_playwright


# ============================================
# 1. 获取剧集播放页（抓 playlist）
# ============================================
def find_page(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print(f"⏳ 打开剧集页：{url}")
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
# 2. 获取 m3u8（监听 request → 找 .m3u8）
# ============================================
import time
from playwright.sync_api import sync_playwright

def get_m3u8(url):
    with sync_playwright() as p:
        # 启动浏览器（关键：添加 args 隐藏特征）
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
            ]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            permissions=["notifications"],
            bypass_csp=True,
            # 关键：注入 JS 隐藏 webdriver
            java_script_enabled=True,
        )

        page = context.new_page()

        # === 关键：注入反检测脚本 ===
        page.add_init_script("""
            // 隐藏 webdriver 标志
            delete navigator.__proto__.webdriver;
            // Mock 浏览器特征
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh']
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)

        m3u8_list = []

        def on_request(request):
            if ".m3u8" in request.url and request.url not in m3u8_list:
                print("🎯 捕获到 M3U8:", request.url)
                m3u8_list.append(request.url)

        page.on("request", on_request)

        print(f"⏳ 加载播放页：{url}")

        try:
            # 不等 load，只等 DOM 加载
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print("❌ 导航失败:", e)
            browser.close()
            return []

        # 等待 Cloudflare 验证完成（最多 30 秒）
        print("🕒 等待 Cloudflare 验证和视频加载...")
        start = time.time()
        while time.time() - start < 30:
            if m3u8_list:
                break
            # 检查是否还在 Cloudflare 页面
            try:
                content = page.content()
                if "cf-challenge" not in content and "Checking if" not in content:
                    # 可能已通过，再等几秒让视频加载
                    page.wait_for_timeout(3000)
                    break
            except:
                pass
            page.wait_for_timeout(1000)

        browser.close()
        return m3u8_list


# ============================================
# 3. 多进程 + yt-dlp 下载
# ============================================
def download_one(args):
    ep_name, m3u8_url, save_dir = args
    output_path = os.path.join(save_dir, ep_name + ".mp4")

    cmd = [
        "yt-dlp",
        "-N", "16",
        "-o", output_path,
        m3u8_url
    ]

    print(f"\n⬇️ 下载开始：{ep_name}")
    subprocess.run(cmd)
    print(f"✅ 完成：{output_path}")
    return True


def parallel_download(m3u8_map, save_dir):
    tasks = [(ep, url, save_dir) for ep, url in m3u8_map.items()]
    workers = min(len(tasks), cpu_count())

    print(f"\n🔥 多进程下载：{workers} workers\n")

    with Pool(workers) as pool:
        pool.map(download_one, tasks)


# ============================================
# 4. 下载一整季
# ============================================
def download_main(save_dir, base_url, root_page, base_name):
    save_season = os.path.join(save_dir, base_name)
    os.makedirs(save_season, exist_ok=True)

    print(f"\n================ {base_name} =================")
    print("🔍 获取剧集列表...")

    ep_map = find_page(root_page)
    all_m3u8 = {}

    for ep_name, ep_path in ep_map.items():
        time.sleep(random.uniform(2, 5))
        play_url = base_url + ep_path
        print(f"\n====== 处理 {ep_name} ======")
        print(f"播放页：{play_url}")
        m3u8 = ""
        try:
            m3u8_list = get_m3u8(play_url)
            if not m3u8_list:
                print("❌ 没有找到 m3u8")
                continue
            for m3u8_str in m3u8_list:
                if m3u8_str.endswith(".m3u8"):
                    m3u8 = m3u8_str
        except Exception as e:
            print(f"[ERROR] 抓取失败: {ep_name} , {e}")
            continue

        all_m3u8[ep_name] = m3u8
        print(f"🎯{ep_name} 最终 m3u8：{m3u8}")

    # 保存 m3u8 列表
    json_path = os.path.join(save_season, "m3u8_list.json")
    json.dump(all_m3u8, open(json_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=4)
    print("\n📄 已写入：", json_path)

    # 下载全部
    parallel_download(all_m3u8, save_season)
    print("\n================ 全部完成！ ================")


# ============================================
# 5. 主程序（支持多季）
# ============================================
if __name__ == "__main__":
    base_url = "https://xiaoxintv.cc/"
    base_name = "生活大爆炸"
    save_dir = "E:\\video\\"
    os.makedirs(save_dir, exist_ok=True)
    save_dir = save_dir + base_name + "\\"
    os.makedirs(save_dir, exist_ok=True)

    total_season = 12
    num = 205588
    root_tpl = "https://xiaoxintv.cc/index.php/vod/play/id/{num}/sid/1/nid/1.html"

    # 构造所有季
    all_pages = {
        f"{base_name} 第{idx}季": root_tpl.format(num=num - (idx - 1))
        for idx in range(3, total_season + 1)
    }

    # 下载全部季
    for season_name, url in all_pages.items():
        print("Season:", season_name, "\tURL:", url)
        download_main(save_dir, base_url, url, season_name)
