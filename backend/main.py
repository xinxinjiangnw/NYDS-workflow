from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from celery.result import AsyncResult
import os
from backend.celery_app import celery

app = FastAPI()

class ScrapeRequest(BaseModel):
    keyword: str
    start_date: str
    end_date: str
    proxy: str = None
    cookies: str = None

@app.post('/scrape')
def scrape(req: ScrapeRequest):
    # 异步提交爬虫任务
    task = celery.send_task('backend.tasks.run_scrape', args=[req.keyword, req.start_date, req.end_date, req.proxy, req.cookies])
    return {'celery_id': task.id}

@app.get('/status/{task_id}')
def status(task_id: str):
    r = AsyncResult(task_id, app=celery)
    resp = {'status': r.status}
    try:
        resp['result'] = r.result if r.status == 'SUCCESS' else None
    except Exception:
        resp['result'] = None
    return resp
