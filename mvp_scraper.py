"""
最小爬虫示例：使用 requests + BeautifulSoup 抓取指定页面的标题和部分文本（用于演示）。
真实环境下建议用 Playwright 并处理反爬措施。
"""
import requests
from bs4 import BeautifulSoup
import json


def fetch_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.text


def parse_service_page(html, url):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("title").get_text(strip=True) if soup.find("title") else ""
    # 抽取description或服务概述段落
    description = ""
    desc_selector = soup.select_one(".service-desc, .description, .wsos-description, #service_description")
    if desc_selector:
        description = desc_selector.get_text(strip=True)
    else:
        # fallback: first p
        p = soup.find("p")
        if p:
            description = p.get_text(strip=True)

    return {
        "url": url,
        "title": title,
        "description": description
    }


def run(urls, out_path):
    results = []
    for u in urls:
        try:
            html = fetch_page(u)
            data = parse_service_page(html, u)
            results.append(data)
        except Exception as e:
            print(f"Failed to fetch {u}: {e}")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python mvp_scraper.py <out.json> <url1> [url2 ...]")
    else:
        out = sys.argv[1]
        urls = sys.argv[2:]
        run(urls, out)
