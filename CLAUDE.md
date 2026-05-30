# CLAUDE.md

makemoney 自动化变现 monorepo。三个独立 track，互不依赖，各有一套技术栈。

## Track 索引

| 目录 | 定位 | 技术栈 |
|------|------|--------|
| `track1-coze/` | 闲鱼文案 Coze Bot Store — AI 提示词产品化上架闲鱼 | Python + 闲鱼 API |
| `track2-content-pipeline/` | 内容发布流水线 — 热榜采集→AI扩写→多平台发布 | Python + opencli 浏览器自动化 |
| `track3-tools-site/` | 在线工具集 — 浏览器端处理的静态工具站 | HTML/CSS/JS + Cloudflare Pages |

## 核心规则

**上下文隔离：** 每个 track 有独立 CLAUDE.md，进入子目录后只关注当前 track。Git 操作均加 `-- .` 限定当前目录，防止交叉污染。

**调试前检查 skill：** 开始任何调试/编码任务前，先检查已安装的 skill 列表，看是否有匹配当前任务的 skill（见 `memory/feedback_check-skills.md`）。

**opencli/bat 脚本：** 涉及 track2 的 publishers/、collectors/、scripts/ 修改，必须先加载 `/opencli-script` skill。
