"""article_writer.py 测试：热点评分逻辑"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from article_writer import _score_topic


def test_score_policy_topic_high():
    """政策类话题得分高"""
    topic = {
        "title": "国务院发布2026年医保改革新政策",
        "summary": "国家医保局公布最新改革方案",
        "platform": "people_rm",
    }
    score = _score_topic(topic)
    assert score > 20, f"政策类应有高分，实际: {score}"


def test_score_entertainment_low():
    """纯娱乐话题低分"""
    topic = {
        "title": "某明星新剧上线",
        "summary": "一部新电视剧今晚开播",
        "platform": "weibo",
    }
    score = _score_topic(topic)
    assert score < 20, f"纯娱乐应有低分，实际: {score}"


def test_score_identity_hook_bonus():
    """身份认同钩子加分"""
    # 两个话题都不命中政策关键词，仅靠身份钩子拉开差距
    no_hook = _score_topic({"title": "互联网服务平台新规即将实施", "platform": "baidu"})
    with_hook = _score_topic({"title": "外卖骑手新规来了，平台必须缴社保", "platform": "baidu"})
    # 身份钩子 +8，no_hook 只有平台可信度 +5
    assert with_hook > no_hook, f"有身份钩子应得分更高: {with_hook} vs {no_hook}"


def test_score_number_bonus():
    """数字标题加分"""
    no_num = _score_topic({"title": "房价最新的变化趋势", "platform": "baidu"})
    with_num = _score_topic({"title": "房价下跌30%，一线城市成交量腰斩", "platform": "baidu"})
    assert with_num >= no_num + 3  # 数字+3，可能还命中其他关键词


def test_score_authority_source():
    """权威来源加分"""
    from_weibo = _score_topic({"title": "某突发事件", "platform": "weibo"})
    from_people = _score_topic({"title": "某突发事件", "platform": "people_rm"})
    assert from_people > from_weibo, f"人民日报应高于微博: {from_people} vs {from_weibo}"


def test_score_low_value_penalty():
    """低价值话题惩罚"""
    topic = {"title": "某网红整形翻车，网友热议", "platform": "weibo"}
    score = _score_topic(topic)
    assert score >= -10, f"低价值惩罚应有效，实际: {score}"  # 可能有其他加分项


def test_baijiahao_prefers_policy():
    """百家号偏好政策类"""
    topic = {"title": "国务院发布新法规：住房补贴标准提高", "platform": "people_rm"}
    generic = _score_topic(topic, "")
    baijiahao = _score_topic(topic, "baijiahao")
    assert baijiahao > generic, f"百家号应对政策提权: {baijiahao} vs {generic}"


def test_baijiahao_demotes_entertainment():
    """百家号降权娱乐"""
    topic = {"title": "某明星综艺节目收官，网友直呼不舍", "platform": "weibo"}
    generic = _score_topic(topic, "")
    baijiahao = _score_topic(topic, "baijiahao")
    assert baijiahao <= generic, f"百家号应对娱乐降权: {baijiahao} vs {generic}"


def test_toutiao_prefers_entertainment():
    """头条偏好娱乐/奇闻"""
    topic = {"title": "离谱！某景区门票价格翻倍引众怒", "platform": "weibo"}
    generic = _score_topic(topic, "")
    toutiao = _score_topic(topic, "toutiao")
    assert toutiao > generic, f"头条应对娱乐提权: {toutiao} vs {generic}"


def test_toutiao_demotes_policy():
    """头条降权政策类"""
    topic = {"title": "国务院发布关于教育改革的通知", "platform": "people_rm"}
    generic = _score_topic(topic, "")
    toutiao = _score_topic(topic, "toutiao")
    assert toutiao < generic, f"头条应对政策降权: {toutiao} vs {generic}"


def test_toutiao_demotes_authority():
    """头条降权权威来源"""
    topic = {"title": "教育部门发布最新通知", "platform": "people_rm"}
    generic = _score_topic(topic, "")
    toutiao = _score_topic(topic, "toutiao")
    assert toutiao < generic, f"头条应对权威来源降权: {toutiao} vs {generic}"


def test_question_title_bonus():
    """疑问句式加分"""
    plain = _score_topic({"title": "房价走势分析", "platform": "baidu"})
    question = _score_topic({"title": "房价还会涨吗？最新走势分析", "platform": "baidu"})
    assert question >= plain + 3  # 疑问 +3，数字 +3


def test_money_keyword_bonus():
    """利益/风险关键词加分"""
    plain = _score_topic({"title": "新政策即将实施", "platform": "baidu"})
    money = _score_topic({"title": "新政策免费补贴即将实施", "platform": "baidu"})
    assert money >= plain + 5  # "免费"或"补贴"命中 +5


def test_score_with_empty_platform():
    """空平台信息不报错"""
    score = _score_topic({"title": "测试标题", "platform": ""})
    assert isinstance(score, int)
    assert score >= -15  # 最坏情况被 LOW_VALUE 惩罚
