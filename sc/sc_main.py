from sc.downloads import download_m3u8
from sc.findhtml import find_page
from sc.get_m3u8 import get_m3u8, get_m3u8_print

import json
import os

if __name__ == '__main__':
    url = "https://xiaoxintv.cc/index.php/vod/play/id/205584/sid/1/nid/1.html"
    file_name = "生活大爆炸_第五季_"
    file_path = r"E:\\video\\生活大爆炸 第五季\\"

    # 自动创建目录
    os.makedirs(file_path, exist_ok=True)

    # 获取所有集数的播放页
    video_href_map = find_page(url)

    # 保存所有 m3u8 的字典
    all_results = {}
    base_url = "https://xiaoxintv.cc/"
    for page_name, page_url in video_href_map.items():
        page_url = base_url + page_url
        print(f"\n====== 正在处理 {page_name} ======")
        print(f"页面：{page_url}")

        # 1. 抓取 m3u8 链接
        m3u8_links = get_m3u8(page_url)

        if not m3u8_links:
            print(f"❌ 未找到 m3u8：{page_url}")
            continue

        # 只拿第一个链接（视频主文件）
        m3u8_url = m3u8_links[1]

        # 写入总记录
        all_results[page_name] = m3u8_url

        # 输出调试
        print(f"🎯 {page_name} → {m3u8_url}")

        # 2. 自动下载
        output_filename = os.path.join(file_path, page_name)
        download_m3u8(m3u8_url, output_filename)

    # 保存 m3u8 列表到 json
    m3u8_json_path = os.path.join(file_path, file_name + "m3u8.json")
    json.dump(all_results, open(m3u8_json_path, "w", encoding="utf-8"), ensure_ascii=False, indent=4)

    print("\n================ ALL DONE! ================")
    get_m3u8_print(all_results)
