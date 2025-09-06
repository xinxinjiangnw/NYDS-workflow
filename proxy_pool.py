"""
简单代理池示例：从文本文件加载代理（每行一个），支持循环分发。
在真实部署中应替换为带健康检查、并发限制与认证刷新逻辑的生产级代理池。

文件 proxies.txt 示例行：
http://host:port
http://user:pass@host:port
socks5://user:pass@host:port

用法示例：
from proxy_pool import ProxyPool
pool = ProxyPool('proxies.txt')
proxy = pool.get_proxy()
# 将 proxy 作为 playwright launch 的 proxy server: e.g. {'server': proxy}

"""
from itertools import cycle
from typing import Optional


class ProxyPool:
    def __init__(self, path: str):
        self.path = path
        self._proxies = self._load_proxies()
        self._cycle = cycle(self._proxies) if self._proxies else cycle([None])

    def _load_proxies(self):
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                lines = [l.strip() for l in f if l.strip()]
            return lines
        except Exception:
            return []

    def get_proxy(self) -> Optional[str]:
        try:
            return next(self._cycle)
        except Exception:
            return None


if __name__ == '__main__':
    p = ProxyPool('proxies.txt')
    for _ in range(5):
        print(p.get_proxy())
