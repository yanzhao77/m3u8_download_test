import os
import json
import subprocess
import time
import random
import requests
from lxml import html
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import Pool, cpu_count
from playwright.sync_api import sync_playwright

# ============================================
# 1. 增强版多源免费代理池（支持 HTTPS）
# ============================================

def test_proxy(proxy_url, timeout=3):
    try:
        resp = requests.get(
            "https://xiaoxintv.cc/",
            proxies={"http": proxy_url, "https": proxy_url},
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        return resp.status_code == 200
    except:
        return False

def scrape_free_proxy_list():
    proxies = []
    try:
        resp = requests.get("https://free-proxy-list.net/", timeout=10)
        tree = html.fromstring(resp.content)
        rows = tree.xpath('//table[contains(@class,"table")]//tbody/tr')
        for row in rows:
            ip = ''.join(row.xpath('./td[1]/text()')).strip()
            port = ''.join(row.xpath('./td[2]/text()')).strip()
            https = ''.join(row.xpath('./td[7]/text()')).strip()
            if ip and port and https == 'yes':
                proxies.append(f"http://{ip}:{port}")
    except Exception as e:
        print(f"[free-proxy-list.net] 抓取失败: {e}")
    return proxies

def scrape_geonode():
    proxies = []
    try:
        resp = requests.get(
            "https://proxylist.geonode.com/api/proxy-list?limit=200&sort_by=lastChecked&sort_type=desc",
            timeout=10
        )
        data = resp.json()
        for item in data.get('data', []):
            if item.get('protocols') and 'https' in item['protocols']:
                ip = item['ip']
                port = item['port']
                proxies.append(f"http://{ip}:{port}")
    except Exception as e:
        print(f"[geonode.com] 抓取失败: {e}")
    return proxies

def scrape_spys_one():
    proxies = []
    try:
        resp = requests.get("http://spys.me/proxy.txt", timeout=10)
        for line in resp.text.splitlines():
            if ":" in line and ("H" in line or "S" in line):
                parts = line.split()
                if len(parts) >= 2:
                    ip_port = parts[0]
                    if ip_port.replace('.', '').replace(':', '').isdigit():
                        proxies.append(f"http://{ip_port}")
    except Exception as e:
        print(f"[spys.me] 抓取失败: {e}")
    return proxies

def scrape_proxy_scrape():
    proxies = []
    try:
        resp = requests.get(
            "https://api.proxyscrape.com/v3/free-proxy-list/get?"
            "request=displayproxies&protocol=http&timeout=5000&country=CN,US,SG,HK&anonymity=elite&ssl=yes&format=text",
            timeout=10
        )
        for line in resp.text.strip().splitlines():
            if ':' in line:
                proxies.append(f"http://{line.strip()}")
    except Exception as e:
        print(f"[proxyscrape.com] 抓取失败: {e}")
    return proxies

def scrape_89ip():
    proxies = []
    try:
        resp = requests.get("http://www.89ip.cn/tqdl.html?num=30&address=&kill_address=&port=&kill_port=&isp=")
        for line in resp.text.split('<br>'):
            line = line.strip()
            if ':' in line and line.replace('.', '').replace(':', '').replace('\n', '').isdigit():
                proxies.append(f"http://{line}")
    except Exception as e:
        print(f"[89ip.cn] 抓取失败: {e}")
    return proxies

def fetch_enhanced_proxies(max_proxies=12, test_timeout=3):
    all_candidates = set()
    scrapers = [scrape_free_proxy_list, scrape_geonode, scrape_spys_one, scrape_proxy_scrape, scrape_89ip]

    print("🌐 正在从多个免费源并行抓取代理...")
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(scraper): scraper.__name__ for scraper in scrapers}
        for future in as_completed(futures):
            try:
                proxies = future.result()
                all_candidates.update(proxies)
            except:
                pass

    print(f"📥 共收集到 {len(all_candidates)} 个候选代理，正在测试可用性...")
    valid_proxies = []
    with ThreadPoolExecutor(max_workers=min(20, len(all_candidates))) as executor:
        future_to_proxy = {
            executor.submit(test_proxy, proxy, test_timeout): proxy
            for proxy in all_candidates
        }
        for future in as_completed(future_to_proxy):
            proxy = future_to_proxy[future]
            try:
                if future.result():
                    valid_proxies.append(proxy)
                    if len(valid_proxies) >= max_proxies:
                        pass
            except:
                continue

    valid_proxies = list(set(valid_proxies))
    random.shuffle(valid_proxies)
    result = valid_proxies[:max_proxies]
    print(f"✅ 最终获得 {len(result)} 个可用 HTTPS 代理")
    return result

def get_m3u8_with_retry(play_url, proxy_pool, max_retries=3):
    """
    尝试使用不同代理获取 m3u8，直到成功或重试耗尽
    """
    for attempt in range(max_retries + 1):
        if attempt == 0:
            # 第一次：优先用代理（如果有）
            proxy = random.choice(proxy_pool) if proxy_pool else None
        else:
            # 重试：如果还有其他代理，换一个；否则用本机 IP
            if proxy_pool and len(proxy_pool) > 1:
                # 排除上次用的（简单做法：重新随机选）
                proxy = random.choice(proxy_pool)
            else:
                proxy = None  # 改用本机 IP

        print(f"🔁 尝试第 {attempt + 1}/{max_retries + 1} 次（代理: {proxy}）")

        try:
            m3u8_list = get_m3u8(play_url, proxy=proxy)
            if m3u8_list:
                return m3u8_list
        except Exception as e:
            print(f"⚠️ 代理 {proxy} 失败: {e}")

        # 重试前等待（避免太快）
        if attempt < max_retries:
            wait = random.uniform(2, 5)
            print(f"⏳ 等待 {wait:.1f} 秒后重试...")
            time.sleep(wait)

    print("💀 所有代理尝试失败，放弃获取 m3u8")
    return []

def find_page_with_retry(root_page, proxy_pool, max_retries=2):
    for attempt in range(max_retries + 1):
        proxy = random.choice(proxy_pool) if proxy_pool and attempt == 0 else None
        if attempt > 0:
            proxy = None  # 重试时用本机
        try:
            print(f"📚 获取剧集列表 - 尝试 {attempt + 1}（代理: {proxy}）")
            return find_page(root_page, proxy=proxy)
        except Exception as e:
            print(f"⚠️ 剧集列表页失败 (代理 {proxy}): {e}")
            if attempt < max_retries:
                time.sleep(random.uniform(3, 6))
    raise Exception("剧集列表页所有尝试均失败")

# ============================================
# 2. 获取剧集播放页（带代理）
# ============================================
def find_page(url, proxy=None):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context_kwargs = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        if proxy:
            context_kwargs["proxy"] = {"server": proxy}
        context = browser.new_context(**context_kwargs)
        page = context.new_page()

        print(f"⏳ 打开剧集页（代理: {proxy}）：{url}")
        page.goto(url)
        page.wait_for_selector("#playlist", timeout=30000)

        li_list = page.query_selector_all('//*[@id="playlist"]/li')
        href_map = {}
        for li in li_list:
            a = li.query_selector("a")
            if a:
                name = " ".join(a.inner_text().strip().split())  # 合并多余空白
                href = a.get_attribute("href")
                href_map[name] = href

        browser.close()
        return href_map

# ============================================
# 3. 获取 m3u8（带代理 + 反检测）
# ============================================
def get_m3u8(url, proxy=None):
    with sync_playwright() as p:
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

        context_kwargs = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "viewport": {"width": 1920, "height": 1080},
            "locale": "zh-CN",
            "timezone_id": "Asia/Shanghai",
            "permissions": ["notifications"],
            "bypass_csp": True,
        }
        if proxy:
            context_kwargs["proxy"] = {"server": proxy}

        context = browser.new_context(**context_kwargs)
        page = context.new_page()

        page.add_init_script("""
            delete navigator.__proto__.webdriver;
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        """)

        m3u8_list = []

        def on_request(request):
            if ".m3u8" in request.url and request.url not in m3u8_list:
                print("🎯 捕获到 M3U8:", request.url)
                m3u8_list.append(request.url)

        page.on("request", on_request)

        print(f"⏳ 加载播放页（代理: {proxy}）：{url}")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print("❌ 导航失败:", e)
            browser.close()
            return []

        print("🕒 等待 Cloudflare 验证和视频加载...")
        start = time.time()
        while time.time() - start < 30:
            if m3u8_list:
                break
            try:
                content = page.content()
                if "cf-challenge" not in content and "Checking if" not in content:
                    page.wait_for_timeout(3000)
                    break
            except:
                pass
            page.wait_for_timeout(1000)

        browser.close()
        return m3u8_list

# ============================================
# 4. 多进程下载（yt-dlp）
# ============================================
def download_one(args):
    ep_name, m3u8_url, save_dir = args
    output_path = os.path.join(save_dir, ep_name + ".mp4")

    cmd = [
        "yt-dlp",
        "-N", "16",
        "-f", "bestvideo+bestaudio/best",
        "--no-check-certificate",
        "--retries", "3",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "-o", output_path,
        m3u8_url
    ]

    print(f"\n⬇️ 开始下载：{ep_name} → {output_path}")

    # ⚠️ 关键修改：不再 capture_output，而是让输出直接显示
    result = subprocess.run(cmd, stdout=None, stderr=None)  # 继承父进程的 stdout/stderr

    if result.returncode == 0:
        print(f"\n✅ 下载成功：{ep_name}")
    else:
        print(f"\n❌ 下载失败：{ep_name}（退出码: {result.returncode}）")
    return result.returncode == 0

def parallel_download(m3u8_map, save_dir):
    tasks = [(ep, url, save_dir) for ep, url in m3u8_map.items() if url]
    if not tasks:
        print("⚠️ 无有效 m3u8，跳过下载")
        return
    workers = min(len(tasks), cpu_count(), 4)  # 限制最多 4 进程防卡死

    print(f"\n🔥 多进程下载：{workers} workers\n")
    with Pool(workers) as pool:
        pool.map(download_one, tasks)

# ============================================
# 5. 下载一整季（主逻辑）
# ============================================
def download_main(save_dir, base_url, root_page, base_name, proxy_pool):
    save_season = os.path.join(save_dir, base_name)
    os.makedirs(save_season, exist_ok=True)

    print(f"\n================ {base_name} =================")

    # 🔍 步骤1: 检查已下载的集（通过 .mp4 文件名）
    existing_episodes = set()
    for file in os.listdir(save_season):
        if file.endswith(".mp4"):
            # 移除 .mp4 后缀，得到集名（如 "第1集"）
            ep_name = os.path.splitext(file)[0]
            existing_episodes.add(ep_name)
    print(f"📁 已存在 {len(existing_episodes)} 集，将跳过")

    # 🔍 步骤2: 获取剧集列表（带代理）
    # 获取剧集列表前也加延迟（尤其无代理时）
    list_delay = random.uniform(5, 10) if proxy_pool else random.uniform(10, 20)
    print(f"⏳ 等待 {list_delay:.1f} 秒后获取剧集列表（{'有代理' if proxy_pool else '无代理模式'}）...")
    time.sleep(list_delay)

    list_proxy = random.choice(proxy_pool) if proxy_pool else None
    try:
        ep_map = find_page_with_retry(root_page, proxy_pool)
    except Exception as e:
        print(f"❌ 获取剧集列表失败: {e}")
        return

    # 🗂️ 步骤3: 过滤未下载的集
    missing_episodes = {
        ep_name: ep_path
        for ep_name, ep_path in ep_map.items()
        if ep_name not in existing_episodes
    }

    if not missing_episodes:
        print("🎉 本季所有剧集已下载，跳过！")
        return

    print(f"📥 本季需下载 {len(missing_episodes)} 集：{list(missing_episodes.keys())}")

    all_m3u8 = {}

    # 🔄 只处理缺失的集
    for ep_name, ep_path in missing_episodes.items():
        # 根据是否有代理动态调整延迟
        if proxy_pool:
            delay = random.uniform(3, 8)  # 有代理：正常延迟
        else:
            delay = random.uniform(8, 15)  # 无代理：更长延迟，降低风控
        print(f"\n⏸️ 人工等待 {delay:.1f} 秒（{'有代理' if proxy_pool else '无代理模式'}）...")
        time.sleep(delay)

        play_url = base_url + ep_path
        print(f"\n====== 处理 {ep_name} ======")
        print(f"播放页：{play_url}")

        m3u8 = ""
        try:
            m3u8_list = get_m3u8_with_retry(play_url, proxy_pool, max_retries=2)
            if not m3u8_list:
                print("❌ 没有找到 m3u8")
                continue
            for url in m3u8_list:
                if url.endswith(".m3u8"):
                    m3u8 = url
                    break
            if not m3u8:
                m3u8 = m3u8_list[0]
        except Exception as e:
            print(f"[ERROR] 抓取失败: {ep_name}, {e}")
            continue

        all_m3u8[ep_name] = m3u8
        print(f"🎯 {ep_name} 最终 m3u8：{m3u8}")

    if not all_m3u8:
        print("⚠️ 无新 m3u8 可下载")
        return

    # 💾 保存 m3u8 列表（可选：追加或覆盖）
    json_path = os.path.join(save_season, "m3u8_list.json")
    combined = {}
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            combined = json.load(f)
    combined.update(all_m3u8)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=4)
    print("\n📄 m3u8 列表已更新：", json_path)

    # ▶️ 下载缺失集
    parallel_download(all_m3u8, save_season)

# ============================================
# 6. 主程序入口
# ============================================
if __name__ == "__main__":
    # 🔧 配置区
    base_url = "https://xiaoxintv.cc/"  # ✅ 已修正
    base_name = "生活大爆炸"
    save_dir = os.path.join("E:\\video", base_name)
    os.makedirs(save_dir, exist_ok=True)

    total_season = 12
    num = 205590
    root_tpl = "https://xiaoxintv.cc/index.php/vod/play/id/{num}/sid/1/nid/1.html"

    # 🌐 获取增强代理池
    proxy_pool = fetch_enhanced_proxies(max_proxies=12)
    if not proxy_pool:
        print("⚠️ 警告：未获取到可用代理！将使用本地 IP（高风险）")
        proxy_pool = []

    # 📺 构造所有季
    all_pages = {
        f"{base_name} 第{idx}季": root_tpl.format(num=num - (idx - 1))
        for idx in range(1, total_season + 1)
    }

    # ▶️ 开始下载
    for season_name, url in all_pages.items():
        print("\n" + "="*60)
        print(f"🎬 开始下载：{season_name}")
        print(f"🔗 URL: {url}")
        try:
            download_main(save_dir, base_url, url, season_name, proxy_pool)
        except Exception as e:
            print(f"💥 季 {season_name} 完全失败: {e}")
            continue

    print("\n🎉 所有任务完成！")