from playwright.sync_api import sync_playwright

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

        print(f"\n⏳ 正在加载页面：{url}")
        page.goto(url, timeout=30000)

        # 等播放器加载
        page.wait_for_timeout(6000)

        browser.close()

        return list(set(m3u8_list))   # 去重！




def get_m3u8_print(all_results):
    # 输出结果
    print("\n================ 所有结果输出 ================")
    for page, links in all_results.items():
        print(f"\n📌 页面: {page}")
        for link in links:
            print(f"   👉 M3U8: {link}")
