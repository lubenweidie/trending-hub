# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

采集多平台热榜 → AI 摘要 → AI 扩写 → 配图 → 多平台发布（今日头条、百家号）。

## 核心文件

| 文件 | 作用 |
|------|------|
| `pipeline.py` | 管线主入口：采集→过滤→摘要→保存主题→HTML |
| `publish.py` | 一键发布入口：管线 + 单平台发布 + Word 存档。`--publish` 立即发布，否则存草稿 |
| `quick_publish.py` | 快捷发布：跳过管线，直接发布已有文章到指定平台 |
| `publishers/base.py` | 发布器基类：opencli 封装、内容提取、AI 扩写、发布流程骨架 |
| `publishers/toutiao.py` | 今日头条发布器（mp.toutiao.com） |
| `publishers/baijiahao.py` | 百家号发布器 |
| `publishers/browser_utils.py` | 浏览器 JS 代码片段（图片提取、React 点击等） |
| `publishers/prompts.py` | AI 扩写提示词 |
| `article_writer.py` | 热点筛选 + 文章保存（基于 `published/` 源 URL 去重） |
| `image_search.py` | 多源图片搜索（百度→Bing→Pexels→Pixabay→Unsplash） |
| `config_loader.py` | 从 `apikeys.conf` 加载配置到 `os.environ`（只设未设置的 key） |
| `一键发布.bat` | Windows 快捷启动：依次跑两次管线，分别发布头条和百家号 |

## 常用命令

```bash
# 一键发布（管线 + 立即发布）
python publish.py -p toutiao --publish

# 草稿模式
python publish.py -p toutiao

# 快捷发布已有文章（跳过管线）
python quick_publish.py toutiao
python quick_publish.py toutiao --publish  # 立即发布

# 发布到百家号
python publish.py -p baijiahao --publish
```

**`一键发布.bat`** 行为：先跑 `publish.py -p toutiao --publish`，再跑 `publish.py -p baijiahao --publish`。两次独立运行，生成不同文章。

## 文章目录结构（硬规则）

```
output/articles/
  {标题}-{时间戳}/                      ← 每篇文章独立文件夹
    {标题}-{时间戳}.md                  ← 文章
    {标题}-{时间戳}.source.txt          ← 源内容
    cover.jpg / img_00.jpg / img_01.jpg ← 配图
  published/
    {标题}-{时间戳}-{发布平台}/          ← 归档（发布后整个文件夹移入）
```

**规则：**
- 目录名格式：`{safe_title}-{YYYYMMDD_HHMM}`，`safe_title` = 去非法字符 + 截断至 30 字
- 图文一体，不分离 `images/` 子目录
- 归档时目录名追加 `-{发布平台}`，无需额外时间戳前缀
- `find_latest_article` 用 `*/*.md` glob 搜索子文件夹

## 图片策略（硬规则）

**不从源页面抓图。用百度/Bing 关键词搜索。**

源页面图片不可靠（平台 branding、UI 元素、头像）。`collect_images_from_source()` 不得进入发布主路径。

流程：
1. 管线预下载图片（`find_article_images`）→ 直接使用
2. 否则用中文标题搜百度 → 英文关键词（AI 生成的 `image_keywords`）搜 Bing/Pexels 兜底
3. 图片直接下载到文章文件夹（不再建 `images/` 子目录）

## 图片上传

- 头条编辑器删除 data URI 的 `<img>`，必须通过 ClipboardEvent paste 触发原生上传管线
- 图片分 chunk 传输（每 chunk ≤4000 字符，cmd.exe 限制 ~8191 字符）
- 预处理：PIL 缩放至 max 600px，JPEG quality 75
- 封面通过 React fiber 事件系统触发上传（`set_cover_image` 三步流程）

## 标题处理

两层防线：
1. AI 提示词约束「严格≤30字」
2. 发布器填标题时在自然断点截断（。！？；，），不硬切 `[:30]`

## 源内容提取

- 搜索/列表页（`s?word=`、`s?wd=`、`m.baidu.com/s?`、`/weibo?`）**先判断再 open**，避免超时
- 搜索页直接返回空，让上层用 AI 摘要替代
- 非搜索页才 `open` + `extract`

## 发布流程

### 头条发布（3 步按钮流程）
1. 点击「预览并发布」→ 预览面板出现
2. 有「预览并定时发布」时先点它 →「确认发布」出现
3. 点击「确认发布」→ 等待成功
4. 草稿模式（`mode="draft"`）跳过上述步骤，直接返回成功

### 百家号发布
单个「发布」按钮 → 确认弹窗 → 点击确认。

## 去重

`article_writer.py` 扫描 `published/` 下所有 `*/*.md`，提取源 URL，新采集的相同 URL 直接跳过。

## 强制使用的 Skill

**调试 opencli 浏览器自动化问题前，必须先用 `/automation-debugging`。** 标准流程：
1. 写独立诊断脚本隔离失败步骤（每个步骤一个 eval，返回唯一标签）
2. 在失败点 dump DOM 状态（检查 `offsetParent`、modal 层级、元素可见性）
3. 每个 try/catch 加唯一错误标签（不要同一个 "error:" 信息）
4. 最小化修改 + 单独验证

相关 skill：`content-pipeline-patterns`（目录结构/图片/标题/归档硬规则）、`python-clean-code`、`prompt-engineering-patterns`。
