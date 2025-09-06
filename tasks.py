"""
Celery tasks: 包含 scrape_and_analyze 异步任务，调用 playwright_scraper.py 的 run 接口与 analysis_agent。
Redis 必须运行，并且环境变量 CELERY_BROKER_URL/CELERY_RESULT_BACKEND 应配置为 redis URL（示例 redis://localhost:6379/0）。
"""
import os
from celery import Celery
from playwright_scraper import run as pw_run
from analysis_agent import SimpleAnalysisAgent

CELERY_BROKER = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')

celery_app = Celery('agentscope_tasks', broker=CELERY_BROKER, backend=CELERY_BACKEND)


@celery_app.task(bind=True)
def scrape_and_analyze(self, keyword, start_date, end_date, out_file, analysis_out, max_pages=5, proxy=None, cookies=None):
    # 调用 playwright scraper
    pw_run(keyword, start_date, end_date, out_file, max_pages=max_pages, proxy=proxy, cookies=cookies, headless=True)
    # 分析
    agent = SimpleAnalysisAgent(out_file)
    agent.load()
    agent.filter_time_window(days=30)
    agent.extract_features()
    agent.competitor_match()
    agent.score()
    agent.to_json(analysis_out)
    return {'analysis': analysis_out}
