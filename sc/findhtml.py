from playwright.sync_api import sync_playwright

url = "https://xiaoxintv.cc/index.php/vod/play/id/205584/sid/1/nid/1.html"

def find_page(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # 如果要无头浏览器改成 True
        page = browser.new_page()
        page.goto(url)

        # 等待 #playlist 加载
        page.wait_for_selector('//*[@id="playlist"]')

        # 用 XPath 找到 ul 下的所有 li
        li_elements = page.query_selector_all('//*[@id="playlist"]/li')

        print(f"找到 {len(li_elements)} 个 li")

        href_map = {}
        for li in li_elements:
            a = li.query_selector("a")
            if a:
                href = a.get_attribute("href")
                href_map[a.inner_text()]=href

        print("所有 href：")
        for h in href_map:
            print(h)

        browser.close()

        return href_map