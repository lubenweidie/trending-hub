# CLAUDE.md

## 项目概述

在线工具集合静态站 — 所有处理在浏览器端完成，文件不上传服务器。部署在 Cloudflare Pages。

## 项目结构

```
track3-tools-site/
  index.html                    ← 首页（工具卡片网格）
  tools/
    json-formatter.html         ← JSON 格式化/压缩/验证
    timestamp.html              ← Unix 时间戳与日期互转
    base64.html                 ← Base64 编解码
    url-encode.html             ← URL 编解码
    image-compress.html         ← 浏览器端图片压缩（Canvas API）
    md5-hash.html               ← MD5/SHA-256 哈希（Web Crypto API）
    regex-tester.html           ← 正则测试（Web Worker 防 ReDoS）
    color-convert.html          ← HEX/RGB/HSL 颜色互转
  static/
    style.css                   ← 全局样式
    regex-worker.js             ← Web Worker，超时终止防主线程阻塞
  about.html / privacy.html / contact.html / disclosure.html  ← 信息页
  sitemap.xml / robots.txt / ads.txt / _headers                ← SEO + Cloudflare
  tests/manual_checklist.md     ← 手动验收清单
```

## 技术栈

- 纯静态 HTML/CSS/JS，无构建工具
- Tailwind CSS CDN（`cdn.tailwindcss.com`）
- 部署目标：Cloudflare Pages

## 安全约定

- **页面**：用户输入渲染必须用 `textContent`，禁止 `innerHTML`
- **正则测试器**：在 Web Worker 中执行，超时 3s 终止，防 ReDoS
- **文件上传**：有 `accept` 属性 + JS `file.type` 白名单 + 大小上限
- **`_headers`**：CSP 限制 script-src，X-Frame-Options DENY，HSTS preload

## 当前占位符（等域名确定后批量替换）

全站 29 处 `https://你的域名/` → 替换为实际域名
`contact@你的域名` → 替换为实际邮箱
`ads.txt` publisher ID `pub-XXXXXXXXXXXXXXX` → 替换为实际 ID

## 与兄弟 track 的关系

- **track1-coze**（闲鱼文案 Coze Bot）：无关，不要混入上下文
- **track2-content-pipeline**（内容发布流水线）：无关，不要混入上下文
- 本 track 独立开发和提交，git 操作限定 `-- .` 不涉及其他 track
