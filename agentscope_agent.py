"""
简化版 AgentScope 智能体示例：实现一个 ScraperAgent 与 AnalysisAgent 的接口，基于消息调用。
真实 AgentScope 框架有自己的 Agent/Message API，这里先提供仿实现供集成与扩展。
"""
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def handle(self, message: dict):
        pass


class ScraperAgent(BaseAgent):
    def __init__(self, name='scraper'):
        super().__init__(name)

    def handle(self, message: dict):
        # message expected: { 'keyword', 'start_date', 'end_date', 'out_file' }
        from playwright_scraper import run as pw_run
        pw_run(message['keyword'], message['start_date'], message['end_date'], message['out_file'], max_pages=message.get('max_pages',5), proxy=message.get('proxy'), cookies=message.get('cookies'))
        return {'status': 'done', 'out_file': message['out_file']}


class AnalysisAgent(BaseAgent):
    def __init__(self, name='analysis'):
        super().__init__(name)

    def handle(self, message: dict):
        # message expected: { 'in_file', 'out_file' }
        agent = __import__('analysis_agent').SimpleAnalysisAgent(message['in_file'])
        agent.load()
        agent.filter_time_window(days=message.get('days',30))
        agent.extract_features()
        agent.competitor_match()
        agent.score()
        agent.to_json(message['out_file'])
        return {'status': 'done', 'out_file': message['out_file']}
