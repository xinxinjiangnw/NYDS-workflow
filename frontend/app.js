async function startScrape(){
  const kw = document.getElementById('kw').value
  const start = document.getElementById('start').value
  const end = document.getElementById('end').value
  const proxy = document.getElementById('proxy').value || null
  const cookies = document.getElementById('cookies').value || null
  const body = { keyword: kw, start_date: start, end_date: end, proxy: proxy, cookies: cookies }
  const res = await fetch('/scrape', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) })
  const j = await res.json()
  document.getElementById('status').innerText = 'Task queued: ' + j.celery_id
  pollStatus(j.celery_id)
}

async function pollStatus(id){
  const s = document.getElementById('status')
  const r = document.getElementById('result')
  const resp = await fetch('/status/' + id)
  const j = await resp.json()
  s.innerText = 'State: ' + j.status
  if(j.status === 'SUCCESS'){
    const resultInfo = j.info || ''
    r.innerText = 'Result: ' + JSON.stringify(j.result || j.info || {})
    return
  }
  setTimeout(()=>pollStatus(id), 2000)
}
