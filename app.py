"""
FastAPI 后端：提供接口触发抓取任务、查看任务状态与获取分析结果。
- POST /scrape 触发抓取（参数：keyword, start_date, end_date, proxy, cookies）
- GET /status/{task_id} 获取任务状态
- GET /result/{task_id} 获取分析结果 JSON

Celery 用于异步执行爬虫与分析任务，Redis 作为 broker 与结果后端。
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from celery.result import AsyncResult
from tasks import scrape_and_analyze
import uuid
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# mount static frontend directory
app.mount('/static', StaticFiles(directory='frontend'), name='static')


@app.get('/')
async def root():
    index_path = os.path.join('frontend', 'index.html')
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type='text/html')
    return {'message': 'Frontend not found. Place files in /frontend'}


class ScrapeRequest(BaseModel):
    keyword: str
    start_date: str
    end_date: str
    max_pages: int = 5
    proxy: str = None
    cookies: str = None


@app.post('/scrape')
async def trigger_scrape(req: ScrapeRequest):
    task_id = str(uuid.uuid4())
    out_file = f'data/{task_id}_scrape.json'
    analysis_out = f'data/{task_id}_analysis.json'
    # 确保 data 目录
    os.makedirs('data', exist_ok=True)
    celery_task = scrape_and_analyze.delay(req.keyword, req.start_date, req.end_date, out_file, analysis_out, req.max_pages, req.proxy, req.cookies)
    return {'task_id': task_id, 'celery_id': celery_task.id}


@app.get('/status/{celery_id}')
async def get_status(celery_id: str):
    res = AsyncResult(celery_id)
    return {'id': celery_id, 'status': res.status, 'info': str(res.info)}


@app.get('/result/{task_file}')
async def get_result(task_file: str):
    path = os.path.join('data', task_file)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail='result not found')
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()
