# PowerShell 脚本：并行启动 uvicorn、celery worker 和 streamlit（适用于开发环境）
# 在运行本脚本前请激活虚拟环境： .\.venv\Scripts\Activate.ps1

# 启动 uvicorn
Start-Process -NoNewWindow -FilePath "powershell" -ArgumentList "-NoExit -Command \"uvicorn backend.main:app --host 0.0.0.0 --port 8000\""
Write-Output "Started uvicorn on port 8000"

# 启动 celery worker
Start-Process -NoNewWindow -FilePath "powershell" -ArgumentList "-NoExit -Command \"celery -A backend.celery_app worker --loglevel=info\""
Write-Output "Started Celery worker"

# 启动 Streamlit
Start-Process -NoNewWindow -FilePath "powershell" -ArgumentList "-NoExit -Command \"streamlit run dashboard_app.py\""
Write-Output "Started Streamlit"

Write-Output "All services started. Use Docker or docker-compose for production-like runs."
