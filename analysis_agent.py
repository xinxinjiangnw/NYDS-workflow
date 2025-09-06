"""
最小分析 Agent（仿 AgentScope 风格）：读取爬虫产出的 JSON，进行简单特征提取并输出候选清单。
"""
import json
import pandas as pd
from datetime import datetime
from rapidfuzz import fuzz
from dateutil import parser


class SimpleAnalysisAgent:
    def __init__(self, json_path):
        self.json_path = json_path
        self.df = None

    def load(self):
        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.df = pd.DataFrame(data)
        # ensure timestamp column
        if 'scrape_time' not in self.df.columns:
            self.df['scrape_time'] = pd.Timestamp.now()
        else:
            self.df['scrape_time'] = pd.to_datetime(self.df['scrape_time'])

    def filter_time_window(self, days=30):
        if self.df is None:
            self.load()
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
        self.df = self.df[self.df['scrape_time'] >= cutoff]

    def extract_features(self):
        # 演示：计算描述长度、关键词计数
        if self.df is None:
            self.load()
        self.df["desc_len"] = self.df["description"].fillna("").apply(len)
        keywords = ["核桃", "产地", "新疆", "手剥"]
        for kw in keywords:
            self.df[f"kw_{kw}"] = self.df["description"].fillna("").str.contains(kw).astype(int)
        # 产地标准化
        if 'origin' in self.df.columns:
            self.df['origin'] = self.df['origin'].fillna('').str.strip()
        else:
            self.df['origin'] = self.df['description'].fillna('').apply(lambda x: '新疆' if '新疆' in x else '')

    def competitor_match(self):
        # 基于标题相似度进行简单分组
        titles = self.df['title'].fillna('').tolist()
        groups = [-1]*len(titles)
        gid = 0
        for i, t in enumerate(titles):
            if groups[i] != -1:
                continue
            groups[i] = gid
            for j in range(i+1, len(titles)):
                if groups[j] == -1:
                    score = fuzz.token_sort_ratio(t, titles[j])
                    if score > 80:
                        groups[j] = gid
            gid += 1
        self.df['comp_group'] = groups

    def score(self):
        # 简单打分：描述长度 + 包含关键词数 + 产地加分
        self.df["score"] = self.df["desc_len"] + sum(self.df[f"kw_{kw}"]*50 for kw in ["核桃", "产地", "新疆", "手剥"])
        # 产地为新疆加分
        self.df.loc[self.df['origin'].str.contains('新疆'), 'score'] += 200
        self.df = self.df.sort_values("score", ascending=False)

    def origin_stats(self):
        return self.df['origin'].value_counts()

    def to_json(self, out_path):
        self.df.to_json(out_path, force_ascii=False, orient="records", date_format="iso")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python analysis_agent.py <input.json> <out.json>")
    else:
        a = SimpleAnalysisAgent(sys.argv[1])
        a.load()
        a.filter_time_window(days=30)
        a.extract_features()
        a.competitor_match()
        a.score()
        print('Origin stats:', a.origin_stats())
        a.to_json(sys.argv[2])
        print("Analysis done.")
