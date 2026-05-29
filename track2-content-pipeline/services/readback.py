"""回读发布数据：从各平台后台抓取文章阅读量，输出 CSV"""
import csv
import json
import re
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

HERE = Path(__file__).parent.parent
DATA_DIR = HERE / "services" / "logs" / "analytics"
DATA_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR = DATA_DIR / "archive"
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 平台注册表 — 新增平台只需在此添加一个条目
# ============================================================

def _run(cmd: str, timeout: int = 90) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, shell=True, capture_output=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def _fetch_toutiao(pages: int) -> list[dict]:
    """今日头条：浏览器打开后台 + 点击分页翻页，绕过 adapter 4页限制"""
    import re as _re
    all_articles = []

    # 打开第 1 页
    base_url = "https://mp.toutiao.com/profile_v4/manage/content/all"
    print(f"  [头条] 打开后台...")
    r = _run(f'opencli browser pub open "{base_url}"', timeout=30)
    if r.returncode != 0:
        print(f"    [FAIL] 页面打开失败")
        return all_articles
    _run("sleep 5")

    for page in range(1, pages + 1):
        if page > 1:
            # 点击分页按钮
            print(f"  [头条] 翻到第 {page} 页...")
            click_js = (
                f"(function(){{"
                f"var items=document.querySelectorAll('.fake-pagination-item');"
                f"for(var i=0;i<items.length;i++){{"
                f"if(items[i].innerText.trim()==='{page}'){{items[i].click();return 'clicked_{page}';}}"
                f"}}"
                f"return 'not_found';"
                f"}})()"
            )
            r_click = _run(f'opencli browser pub eval "{click_js}"', timeout=10)
            if r_click.returncode != 0 or 'not_found' in (r_click.stdout or ''):
                # 可能没有更多页了
                break
            _run("sleep 3")

        r_text = _run(
            'opencli browser pub eval "(function(){return document.body.innerText;})()"',
            timeout=15
        )
        if r_text.returncode != 0 or not r_text.stdout:
            break

        text = r_text.stdout.strip()

        if _re.search(r'登录|请登录|账号登录|扫码登录|验证码|captcha', text, _re.IGNORECASE):
            print(f"    [FAIL] 需要重新登录")
            break

        articles = _parse_toutiao_text(text)
        if not articles:
            break

        all_articles.extend(articles)
        print(f"    第 {page} 页: {len(articles)} 条")

        if len(articles) < 10:
            break

    return all_articles


def _parse_toutiao_text(text: str) -> list[dict]:
    """解析头条后台页面文本，与 opencli utils.js parseToutiaoArticlesText 同逻辑"""
    import re as _re
    skip_titles = {'展现', '阅读', '点赞', '评论', '查看数据', '查看评论', '修改', '更多', '首发',
                   '已发布', '定时发布', '定时发布中', '由文章生成', '审核中'}
    stats_re = _re.compile(r'展现\s*([\d,]+)\s*阅读\s*([\d,]+)\s*点赞\s*([\d,]+)\s*评论\s*([\d,]*)')

    lines = [l.strip() for l in text.split('\n') if l.strip()]
    results = []

    for i, line in enumerate(lines):
        # 日期锚点: MM-DD HH:MM
        if not _re.match(r'^\d{2}-\d{2}\s+\d{2}:\d{2}$', line):
            continue

        date = line
        title = None
        status = None
        stats = None

        # 标题在前 1-3 行
        for back in range(3, 0, -1):
            if i - back < 0:
                continue
            prev = lines[i - back]
            if not prev or len(prev) >= 100 or prev.isdigit() or prev in skip_titles:
                continue
            title = prev
            break

        # 状态和统计在后续行
        for fwd in range(1, 8):
            if i + fwd >= len(lines):
                break
            fwd_line = lines[i + fwd]
            if fwd_line in ('已发布', '定时发布中', '审核中', '由文章生成'):
                status = fwd_line
            if '展现' in fwd_line and '阅读' in fwd_line:
                m = stats_re.match(fwd_line)
                if m:
                    stats = {
                        '展现': int(m.group(1).replace(',', '')),
                        '阅读': int(m.group(2).replace(',', '')),
                        '点赞': int(m.group(3).replace(',', '')),
                        '评论': int(m.group(4).replace(',', '') or '0'),
                    }

        if not title:
            continue

        row = {'title': title, 'date': date, 'status': status or ''}
        if stats:
            row.update(stats)
        else:
            row.update({'展现': 0, '阅读': 0, '点赞': 0, '评论': 0})
        results.append(row)

    return results


def _clean_toutiao(articles: list[dict]) -> list[dict]:
    """头条特有清洗：过滤「由文章生成」占位行、统计作标题的脏数据"""
    seen = set()
    result = []
    for a in articles:
        title = (a.get("title") or "").strip()
        if not title or title in ("~", "-"):
            continue
        if title.startswith("展现 ") or title.startswith("阅读 "):
            continue
        key = title[:30]
        if key in seen:
            continue
        seen.add(key)
        result.append(a)
    return result


def _fetch_baijiahao(pages: int) -> list[dict]:
    """百家号：无 adapter，打开页面后正则解析 body 文本"""
    all_articles = []
    content_url = "https://baijiahao.baidu.com/builder/rc/content"
    for page in range(1, pages + 1):
        print(f"  [百家号] 抓取第 {page} 页...")
        _run(f'opencli browser pub open "{content_url}?currentPage={page}&pageSize=10"', timeout=30)
        _run("sleep 3")
        r = _run('opencli browser pub eval "(function(){return document.body.innerText;})()"', timeout=15)
        if r.returncode != 0 or not r.stdout:
            print(f"    [FAIL] 无法读取页面")
            break
        articles = _parse_baijiahao_text(r.stdout.strip())
        if not articles:
            break
        all_articles.extend(articles)
        print(f"    获取 {len(articles)} 条")
    return all_articles


def _parse_baijiahao_text(text: str) -> list[dict]:
    articles = []
    pattern = re.compile(
        r'(.+?)\n'
        r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\n'
        r'(?:.*?(?:已发布|草稿|未通过|待发布|已撤回).*?\n)'
        r'(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)',
        re.MULTILINE
    )
    for m in pattern.finditer(text):
        title = m.group(1).strip()
        if len(title) < 2 or title in ('规则中心', '问题咨询', '发布作品', '作品管理', '切换'):
            continue
        articles.append({
            "title": title,
            "date": m.group(2).strip(),
            "阅读": int(m.group(3)),
            "点赞": int(m.group(4)),
            "评论": int(m.group(5)),
            "收藏": int(m.group(6)),
            "分享": int(m.group(7)),
        })
    return articles


# ============================================================
# 平台注册
# ============================================================

PLATFORMS = {
    "toutiao": {
        "label": "今日头条",
        "fetch": _fetch_toutiao,
        "pages": 10,
        "fields": ["title", "date", "status", "展现", "阅读", "点赞", "评论"],
        "clean": _clean_toutiao,
    },
    "baijiahao": {
        "label": "百家号",
        "fetch": _fetch_baijiahao,
        "pages": 4,
        "fields": ["title", "date", "阅读", "点赞", "评论", "收藏", "分享"],
        "clean": None,  # 正则解析时已过滤
    },
}


# ============================================================
# 通用逻辑（不依赖具体平台）
# ============================================================

def _archive_old_files():
    for f in DATA_DIR.glob("*.csv"):
        dst = ARCHIVE_DIR / f.name
        if dst.exists():
            dst.unlink()
        shutil.move(str(f), str(dst))
        print(f"[归档] {f.name} → archive/")


def _default_clean(articles: list[dict]) -> list[dict]:
    """通用清洗：去空标题、去重"""
    seen = set()
    result = []
    for a in articles:
        title = (a.get("title") or "").strip()
        if not title:
            continue
        key = title[:30]
        if key in seen:
            continue
        seen.add(key)
        result.append(a)
    return result


def _sort_by_views(articles: list[dict]) -> list[dict]:
    def _get_views(a: dict) -> int:
        raw = a.get("阅读", a.get("views", 0))
        if isinstance(raw, (int, float)):
            return int(raw)
        s = str(raw).replace(",", "").replace("万", "0000")
        try:
            return int(float(s))
        except ValueError:
            return 0
    return sorted(articles, key=_get_views, reverse=True)


def _save_csv(platform_key: str, articles: list[dict], ts: str):
    """保存 CSV，并与历史数据合并——按标题去重，累计覆盖"""
    import csv as _csv
    if not articles:
        return
    cfg = PLATFORMS[platform_key]
    path = DATA_DIR / f"{platform_key}_{ts}.csv"
    fields = cfg["fields"]

    # 加载历史累计文件（如果存在）
    master_path = DATA_DIR / f"{platform_key}_master.csv"
    existing = {}
    if master_path.exists():
        with open(master_path, newline="", encoding="utf-8-sig") as f:
            reader = _csv.DictReader(f)
            for row in reader:
                key = (row.get("title") or "").strip()[:30]
                if key:
                    existing[key] = row

    # 新数据覆盖旧数据（以标题为 key）
    for a in articles:
        key = (a.get("title") or "").strip()[:30]
        if not key:
            continue
        existing[key] = a

    merged = list(existing.values())
    merged = _sort_by_views(merged)

    # 写主文件
    with open(master_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = _csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for a in merged:
            writer.writerow(a)

    # 写带时间戳的快照
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = _csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for a in _sort_by_views(articles):
            writer.writerow(a)

    print(f"[{cfg['label']}] CSV 已保存: {master_path.name}（累计 {len(merged)} 篇）, {path.name}（本次 {len(articles)} 篇）")


def _print_table(platform_key: str, articles: list[dict], top_n: int):
    cfg = PLATFORMS[platform_key]
    sorted_articles = _sort_by_views(articles)[:top_n]
    label = cfg["label"]
    print(f"\n{'=' * 65}")
    print(f"  {label} TOP {top_n}（共 {len(articles)} 篇）")
    print(f"{'=' * 65}")
    print(f"  {'#':<3} {'阅读':<6} {'点赞':<5} {'评论':<5} {'标题'}")
    print(f"  {'-' * 60}")
    for i, a in enumerate(sorted_articles, 1):
        title = a.get("title", "?")[:38]
        reads = a.get("阅读", a.get("views", 0))
        likes = a.get("点赞", 0)
        comments = a.get("评论", 0)
        date = (a.get("date") or "")[:10]
        print(f"  {i:<3} {str(reads):<6} {str(likes):<5} {str(comments):<5} {title}")
        if date:
            print(f"       {date}")
    print()


# ============================================================
# 主入口
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="回读发布平台文章数据")
    parser.add_argument("-p", "--platforms", default="toutiao,baijiahao",
                        help="目标平台（默认 toutiao,baijiahao）")
    parser.add_argument("-n", "--top", type=int, default=20,
                        help="显示 TOP N（默认 20）")
    parser.add_argument("--no-save", action="store_true",
                        help="不保存 CSV")
    args = parser.parse_args()

    platforms = [p.strip() for p in args.platforms.split(",")]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    if not args.no_save:
        _archive_old_files()

    for key in platforms:
        cfg = PLATFORMS.get(key)
        if not cfg:
            print(f"[Skip] 未知平台: {key}（可用: {', '.join(PLATFORMS)}）")
            continue

        print(f"\n[{cfg['label']}] 开始抓取...")
        articles = cfg["fetch"](cfg["pages"])
        if not articles:
            print(f"[{cfg['label']}] 无数据")
            continue

        cleaner = cfg.get("clean") or _default_clean
        articles = cleaner(articles)
        print(f"[{cfg['label']}] 清洗后 {len(articles)} 条有效数据")

        _print_table(key, articles, args.top)

        if not args.no_save:
            _save_csv(key, articles, ts)


if __name__ == "__main__":
    main()
