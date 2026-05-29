"""AI 写作提示词 — 从独立文件加载，方便单独修改"""
import os

_PROMPTS_DIR = os.path.dirname(__file__)

def _read(name):
    with open(os.path.join(_PROMPTS_DIR, name), encoding='utf-8') as f:
        return f.read()

# 文章主体（人设 + 结构 + 规则）+ 标题部分
ENRICH_PROMPT = _read('article.txt') + '\n\n' + _read('title.txt')
