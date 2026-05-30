# CLAUDE.md

makemoney 自动化变现项目管理仓库。三个 track 已拆分为独立 Git 仓库。

## Track 索引

| 仓库路径 | 定位 | 技术栈 |
|----------|------|--------|
| `../makemoney-track1/` | 闲鱼文案 Coze Bot Store — AI 提示词产品化上架闲鱼 | Python + 闲鱼 API |
| `../makemoney-track2/` | 内容发布流水线 — 热榜采集→AI扩写→多平台发布 | Python + opencli 浏览器自动化 |
| `../makemoney-track3/` | 在线工具集 — 浏览器端处理的静态工具站 | HTML/CSS/JS + Cloudflare Pages |

## 本仓库内容

仅保留跨 track 共享资源：`scripts/`、`.github/`、`.vscode/`、自动化规划文档。

## 核心规则

**完全隔离：** 每个 track 是独立 Git 仓库，无交叉污染。进入对应目录工作即可。

**调试前检查 skill：** 开始任何调试/编码任务前，先检查已安装的 skill 列表。

**opencli/bat 脚本：** 涉及 track2 的 publishers/、collectors/、scripts/ 修改，必须先加载 `/opencli-script` skill。
