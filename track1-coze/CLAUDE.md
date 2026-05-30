# CLAUDE.md

## 项目概述

闲鱼文案 Coze Bot Store — 将 AI 提示词产品化，打包上架到闲鱼"虚拟服务"类目变现。每个 Bot 包含 prompt 源码、移动端网页、闲鱼商品信息。

## 项目结构

```
track1-coze/
  Prompt源码/                  ← 5 个 Bot 的完整 prompt 文本
    合同风险-prompt.txt
    客服话术-prompt.txt
    日报生成-prompt.txt
    竞品监控-prompt.txt
    简历优化-prompt.txt
  闲鱼文案/                    ← 5 个 Bot 的商品文案（title/description/copy）
    合同风险扫描.md
    客服话术库.md
    日报生成器.md
    竞品监控器.md
    简历优化助手.md
  manage.py                   ← 管理脚本（复制/导出/状态管理）
  generate_copy.py            ← 批量生成闲鱼商品文案
  image_generator.py          ← 商品配图生成
  mobile_copy_page.py         ← 移动端文案落地页生成
  publisher.py                ← 通用发布辅助
  xianyu_publisher.py         ← 闲鱼发布器
  xianyu_api.py               ← 闲鱼 API 封装
  config.py                   ← 配置文件
  console_debug.js            ← 闲鱼控制台调试脚本
  products.json               ← 商品信息数据
  SOP文档模板.md              ← 上架标准操作流程
  requirements.txt            ← Python 依赖
  exports/                    ← 导出产物（每个 Bot 一个子目录）
    resume-optimizer/
      listing.json            ← 闲鱼商品信息
      description.txt         ← 商品描述
      title.txt               ← 商品标题
      prompt.txt              ← AI prompt
      copy.md                 ← 文案
      index.html              ← 移动端落地页
      publish.js              ← 上架脚本
      images/                 ← 商品配图
```

## 工作流

1. 选 Bot → 完善 Prompt 源码（`Prompt源码/`）
2. 生成闲鱼文案（`闲鱼文案/`）— title + description + copy
3. 生成配图（`image_generator.py`）— 封面 + 功能图 + 对比图 + CTA
4. 导出到 `exports/{bot-name}/`（`manage.py`）
5. 上架到闲鱼（`xianyu_publisher.py`）

## 与兄弟 track 的关系

- **track2-content-pipeline**（内容发布流水线）：无关
- **track3-tools-site**（工具站）：无关
- 本 track 独立开发和提交，git 操作限定 `-- .` 不涉及其他 track
