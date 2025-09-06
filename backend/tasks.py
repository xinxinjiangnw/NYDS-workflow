from backend.celery_app import celery
from playwright_scraper import run as run_scrape
import os

@celery.task(name='backend.tasks.run_scrape')
def run_scrape_task(keyword, start_date, end_date, proxy=None, cookies=None):
    out = f'scrape_output_{keyword}_{start_date}_{end_date}.json'
    # 直接调用之前的 run 函数
    run_scrape(keyword, start_date, end_date, out, proxy=proxy, cookies=cookies, headless=True)
    return {'out': out}
