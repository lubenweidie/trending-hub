# track2-content-pipeline — 内容自动化管线

## 项目概述

采集多平台热榜 → AI 摘要 → AI 扩写 → 配图 → 多平台发布（今日头条、百家号）。

## 核心文件

| 文件 | 作用 |
|------|------|
| `pipeline.py` | 管线主入口：采集→过滤→摘要→保存主题→HTML |
| `publish.py` | 一键发布入口：管线 + 多平台发布 + Word 存档 |
| `publishers/base.py` | 发布器基类：opencli 封装、源内容提取、AI 扩写、发布流程骨架 |
| `publishers/toutiao.py` | 今日头条发布器（mp.toutiao.com） |
| `publishers/baijiahao_publisher.py` | 百家号发布器 |
| `publishers/browser_utils.py` | 浏览器 JS 代码片段（图片提取、React 点击等） |
| `publishers/prompts.py` | AI 扩写提示词 |
| `article_writer.py` | 热点筛选 + 文章保存（去重基于 published/ 目录的源 URL） |
| `image_search.py` | 多源图片搜索（百度→Pexels→Pixabay→Unsplash，含下载） |
| `collectors/` | 各平台热榜采集器（微博、知乎、百度、掘金、V2EX） |
| `apikeys.conf` | API Key 和发布配置 |
| `一键发布.bat` | Windows 快捷启动脚本 |

## 常用命令

```bash
# 草稿模式发布到今日头条
PUBLISH_MODE=1 python publish.py -p toutiao

# 立即发布到百家号
PUBLISH_MODE=2 python publish.py -p baijiahao

# 同时发布到两个平台
PUBLISH_PLATFORMS=toutiao,baijiahao python publish.py -p toutiao,baijiahao

# 直接发布指定文章（跳过管线采集）
python -c "
from publishers.toutiao import ToutiaoPublisher
ToutiaoPublisher().publish(article_path='output/articles/xxx.md', mode='draft')
"
```

## 关键约束与经验

### 图片上传
- 头条编辑器会删除 data URI 的 `<img>` 标签，必须通过粘贴事件触发原生上传管线
- 图片通过 chunk 传输（每 chunk ≤4000 字符）→ 浏览器组装 → ClipboardEvent paste → CDN 上传
- cmd.exe 命令行限制 ~8191 字符，每个 opencli eval 命令总长必须在此范围内
- 图片预处理：PIL 缩放至 max 600px，JPEG quality 75

### 标题
- 头条标题限制 5-30 字符（超出截断，不足补全）

### 配图策略
- 优先从源页面抓图 → 源页面无图则用中文标题关键词搜图（百度优先）→ 英文关键词兜底

### 源内容提取
- 搜索/列表页（微博搜索、百度搜索）不跳外链（跳转目标不可控），直接用摘要扩写
- 提取失败时自动回退到 AI 摘要

### 去重
- `article_writer.py` 基于 `published/` 目录下的源 URL 去重，避免同一话题重复发布
- `publish.py` 发布成功后自动将文章归档到 `output/articles/published/`

### 发布模式
- `PUBLISH_MODE=1`：存草稿（安全，需手动上线）
- `PUBLISH_MODE=2`：立即发布
- 默认使用草稿模式

## 强制使用的 Skill

**调试 opencli 浏览器自动化问题前，必须先用 `/automation-debugging`**。该 skill 要求的标准流程：

1. 写独立诊断脚本隔离失败步骤（每个步骤一个 eval，返回唯一标签）
2. 在失败点 dump DOM 状态（检查 `offsetParent`、modal 层级、元素可见性）
3. 每个 try/catch 加唯一错误标签（不要同一个 "error:" 信息）
4. 最小化修改 + 单独验证

相关 skill：`python-clean-code`、`python-testing-patterns`、`prompt-engineering-patterns`（调 AI 扩写提示词时用）

## 偏好设置
- 发布前确认 PUBLISH_MODE=1（草稿），不要直接上线
- 不要在不同平台发布相同文章
- 修改代码后先跑完整流程验证，不要只看单元测试
- 开始调试自动化问题前，先加载 automation-debugging skill
