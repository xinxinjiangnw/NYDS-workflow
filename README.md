MVP for AgentScope-like multi-agent demo (Python)

步骤:
1. 打开终端到 d:\Workflow\agentscope_mvp
2. 运行 `python mvp_scraper.py analysis_input.json <url1> <url2>` 抓取页面
3. 运行 `python analysis_agent.py analysis_input.json analysis_output.json` 进行简单分析
4. 运行 `streamlit run dashboard_app.py` 并在 Dashboard 上传 analysis_output.json 进行展示

也可在 VSCode 运行任务 "agentscope:mvp:install-and-run" 来一键安装依赖并启动 Streamlit。

更新说明:
- 使用 Playwright 作为首选爬虫：运行 `python playwright_scraper.py "核桃" 2025-08-06 2025-09-05 out_playwright.json`
- 运行分析：`python analysis_agent.py out_playwright.json analysis_output.json`（默认 30 天时间窗口，可通过参数修改）
- 启动 Dashboard：`streamlit run dashboard_app.py` 并上传 `analysis_output.json`。

后续功能扩展说明（A/B/C）

A) 定位并微调为抖音商城的实际选择器
- 我可以帮助你把 `playwright_scraper.py` 中的选择器替换为抖音商城的具体 selector，包括商品列表选择器、详情页中标题/价格/产地/店铺选择器。为此我需要：
  - 目标商品或商品列表页的 HTML 示例（可通过保存页面后上传），或者
  - 允许我对一个示例页面进行一次抓取（你确认允许使用登录/代理时请说明）。
- 完成后我会把选择器写死在脚本中并提供示例运行命令。

B) 代理池示例
- 文件 `proxy_pool.py` 已新增，示例文件 `proxies.txt`（每行一个代理）可用于管理代理。示例用法：
  - 在 `playwright_scraper.py` 中导入 `ProxyPool`，在每次浏览器实例创建时调用 `pool.get_proxy()` 并把返回值传入 playwright 的 launch proxy 配置。
  - 本地 Windows PowerShell 运行示例（假设已填 proxies.txt）：
    python playwright_scraper.py "核桃" 2025-08-06 2025-09-05 out_playwright.json --proxy http://user:pass@host:port

C) 集成数据库（SQLite/Postgres）
- 我可以把爬虫输出自动写入 SQLite（无需额外依赖）或 Postgres（配置 connection string）。
- 推荐流程：
  1. 小规模测试使用 SQLite：脚本会在项目目录创建 `data.db` 并写入 `products` 表。
  2. 生产环境使用 Postgres：我会生成 CREATE TABLE 语句和插入/更新逻辑。
- 是否选择 SQLite 还是 Postgres？（测试阶段建议 SQLite）

请确认是否开始执行 A、B、C 中的全部实现（我将修改脚本以自动使用代理池、将爬虫结果写入 SQLite 并尝试基于一个示例页面微调选择器），或告诉我你想先做哪个。

新增：后端与异步任务

- FastAPI 后端 `app.py`：提供 /scrape 接口触发抓取并返回 Celery task id；/status/{celery_id} 查询任务状态；/result/{task_file} 获取结果文件。
- Celery 任务 `tasks.py`：定义 `scrape_and_analyze` 任务，调用 `playwright_scraper` 与 `analysis_agent` 生成分析结果并写入 data 目录。
- 简化 AgentScope 示例 `agentscope_agent.py`：提供 `ScraperAgent` 与 `AnalysisAgent` 的仿实现供后续扩展。

运行说明（开发环境）：
1. 启动 Redis (本地或远程)。例如 Windows 上可使用 Docker:
   docker run -p 6379:6379 -d redis
2. 启动 Celery worker:
   celery -A tasks.celery_app worker --loglevel=info
3. 启动 FastAPI:
   uvicorn app:app --reload --port 8000
4. 调用接口触发任务：
   POST http://localhost:8000/scrape
   body JSON: {"keyword":"核桃","start_date":"2025-08-06","end_date":"2025-09-05"}

返回示例：{ "task_id": "...", "celery_id": "..." }

查询任务状态：
GET http://localhost:8000/status/<celery_id>

获取结果示例：
GET http://localhost:8000/result/<taskfile>.json

注意事项：
- Celery 的 broker/result backend 默认配置为 redis://localhost:6379/0 和 redis://localhost:6379/1，可通过环境变量覆盖。
- 生产环境建议使用 supervisord/systemd 或 Docker Compose/Kubernetes 部署 Redis、Celery、FastAPI 与 Worker。
