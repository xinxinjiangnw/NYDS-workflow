"""
Playwright 抓取模板（针对抖音/抖音商城的通用示例）

功能：
- 按关键词在抖音搜索页面抓取商品列表（使用通用链接过滤器，可能需根据实际站点微调）
- 支持时间窗口参数（用于分析时过滤；抓取阶段会记录 scrape_time）
- 支持代理（--proxy）和 cookies 登录文件（--cookies）以便抓取需要登录的页面
- 输出包含：url, title, price, origin, shop_name, scrape_time, raw_text_snippet

注意：抖音/电商页面结构会频繁变化，请根据实际页面使用开发者工具定位合适的 selector。若需登录，建议手动通过浏览器登录一次并导出 cookies 文件，然后使用 --cookies 加载。

示例运行：
python playwright_scraper.py "核桃" 2025-08-06 2025-09-05 out_playwright.json --proxy http://user:pass@host:port --cookies cookies.json

"""
import asyncio
import json
import re
import os
import time
from datetime import datetime
from typing import List, Optional
import argparse
from playwright.async_api import async_playwright, Browser, BrowserContext


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


async def load_cookies_to_context(context: BrowserContext, cookie_path: str, url: str):
    try:
        with open(cookie_path, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        # cookies should be a list of dicts suitable for Playwright add_cookies
        # ensure domain/path set
        for c in cookies:
            if 'url' not in c and 'domain' in c:
                # Playwright prefers url when adding cookies; fallback to target url
                c['url'] = url
        await context.add_cookies(cookies)
        print(f'Loaded {len(cookies)} cookies from {cookie_path}')
    except Exception as e:
        print('Failed to load cookies:', e)


def extract_origin_from_text(text: str) -> str:
    # 常见抓取产地的正则
    patterns = [r'产地[:：]\s*([^\n，。;；]+)', r'发货地[:：]\s*([^\n，。;；]+)', r'原产地[:：]\s*([^\n，。;；]+)']
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1).strip()
    # 简单关键词检测，例如包含省名
    if '新疆' in text:
        return '新疆'
    return ''


def extract_price_from_text(text: str) -> Optional[float]:
    # 寻找 ￥ 或 ¥ 或 数字价格
    m = re.search(r'[¥￥]\s*([0-9]+(?:\.[0-9]{1,2})?)', text)
    if m:
        try:
            return float(m.group(1))
        except:
            return None
    # 备用：找类似 12.5 元
    m2 = re.search(r'([0-9]+(?:\.[0-9]{1,2})?)\s*元', text)
    if m2:
        try:
            return float(m2.group(1))
        except:
            return None
    return None


async def fetch_detail(page, url: str):
    await page.goto(url, timeout=30000)
    # 给页面加载时间
    await page.wait_for_timeout(1000)
    # 尝试通过常见选择器获取结构化字段，若失败则回落到全文正则提取
    title = ''
    origin = ''
    shop_name = ''
    price = None

    try:
        # 常见标题选择器
        for sel in ['h1', 'h2', 'div.product-title', '.goods-title', '.detail-title']:
            try:
                el = await page.query_selector(sel)
                if el:
                    txt = (await el.inner_text()).strip()
                    if txt:
                        title = txt
                        break
            except:
                continue
    except Exception:
        pass

    if not title:
        try:
            title = await page.title()
        except:
            title = ''

    # shop name attempt
    try:
        for sel in ['.shop-name', '.seller-name', '.merchant-name', '.store-name']:
            el = await page.query_selector(sel)
            if el:
                shop_name = (await el.inner_text()).strip()
                if shop_name:
                    break
    except Exception:
        pass

    # price attempt
    try:
        for sel in ['.price', '.current-price', '.goods-price', '.p-price']:
            el = await page.query_selector(sel)
            if el:
                txt = (await el.inner_text()).strip()
                p = extract_price_from_text(txt)
                if p is not None:
                    price = p
                    break
    except Exception:
        pass

    # fallback: whole page text
    try:
        body = await page.inner_text('body')
    except Exception:
        body = ''

    if not origin:
        origin = extract_origin_from_text(body)

    if price is None:
        price = extract_price_from_text(body)

    snippet = body[:1000]

    return {
        'url': url,
        'title': title,
        'price': price,
        'origin': origin,
        'shop_name': shop_name,
        'scrape_time': datetime.utcnow().isoformat(),
        'raw_text_snippet': snippet
    }


async def scrape_keyword(keyword: str, start_date: str, end_date: str, max_pages: int = 5, proxy: Optional[str] = None, cookies: Optional[str] = None, headless: bool = True) -> List[dict]:
    results = []
    async with async_playwright() as p:
        launch_args = {}
        if proxy:
            # Playwright proxy config expects server string
            launch_args['proxy'] = { 'server': proxy }
        browser = await p.chromium.launch(headless=headless, **launch_args)
        context = await browser.new_context(user_agent=DEFAULT_HEADERS['User-Agent'])

        # load cookies if provided
        if cookies and os.path.exists(cookies):
            await load_cookies_to_context(context, cookies, 'https://www.douyin.com')

        page = await context.new_page()

        # 使用抖音搜索页面的通用 URL（可能需要根据实际站点调整）
        # 抖音移动/桌面结构差异大，实战中请定位实际搜索/店铺 URL
        search_url = f'https://www.douyin.com/search/{keyword}'
        try:
            await page.goto(search_url, timeout=30000)
        except Exception as e:
            print('Search page goto failed:', e)
            await browser.close()
            return results

        await page.wait_for_timeout(1500)

        # 尝试收集潜在商品链接（根据 href 过滤）
        anchors = await page.eval_on_selector_all('a', 'els => els.map(e=>e.href)')
        candidate_links = []
        for a in anchors:
            if not a:
                continue
            # 常见商品链接包含 keywords like 'goods', 'item', 'product', 'shop'
            if any(k in a for k in ['/goods/', '/item/', 'shop.douyin.com', '/product', '/goods']):
                candidate_links.append(a)
        # 去重并限制数量
        candidate_links = list(dict.fromkeys(candidate_links))[:max_pages*10]

        # 如果没有直接商品链接，尝试从页面中抽取 data-ecom 属性或脚本内链接
        if not candidate_links:
            # 简单尝试从脚本标签中提取 url-like strings
            scripts = await page.eval_on_selector_all('script', 'els=>els.map(e=>e.textContent)')
            for s in scripts:
                if not s:
                    continue
                found = re.findall(r'https?://[^\s"\']+', s)
                for f in found:
                    if any(k in f for k in ['/goods/', '/item/', 'shop.douyin.com', '/product']):
                        candidate_links.append(f)
            candidate_links = list(dict.fromkeys(candidate_links))[:max_pages*10]

        # 访问候选详情页并提取信息
        for link in candidate_links:
            try:
                detail = await fetch_detail(page, link)
                results.append(detail)
                # 轻微等待以避免短时间内请求过快
                await page.wait_for_timeout(300)
            except Exception as e:
                print('detail fetch failed for', link, e)

        await browser.close()
    return results


def run(keyword: str, start_date: str, end_date: str, out_path: str, max_pages: int = 5, proxy: Optional[str] = None, cookies: Optional[str] = None, headless: bool = True):
    loop = asyncio.get_event_loop()
    data = loop.run_until_complete(scrape_keyword(keyword, start_date, end_date, max_pages=max_pages, proxy=proxy, cookies=cookies, headless=headless))
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'Wrote {len(data)} items to {out_path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('keyword')
    parser.add_argument('start_date')
    parser.add_argument('end_date')
    parser.add_argument('out')
    parser.add_argument('--max-pages', type=int, default=5)
    parser.add_argument('--proxy', type=str, default=None, help='proxy server e.g. http://user:pass@host:port')
    parser.add_argument('--cookies', type=str, default=None, help='path to cookies json file')
    parser.add_argument('--headless', action='store_true', help='run headless')
    args = parser.parse_args()

    run(args.keyword, args.start_date, args.end_date, args.out, max_pages=args.max_pages, proxy=args.proxy, cookies=args.cookies, headless=args.headless)
