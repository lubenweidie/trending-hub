# 工具站手动验收清单

## 每个工具的验收项
- [ ] `catch(e)` 错误提示为通用文案，未暴露 `e.message`
- [ ] 用户输入用 `textContent` 渲染，确认无 `innerHTML` 赋值
- [ ] 文件上传有 `accept` 属性 + JS `file.type` 白名单
- [ ] 输入超限时前端提示友好错误信息（不崩溃不卡死）
- [ ] Chrome + Safari + 手机端各测试一次核心功能

## 首轮验收重点工具
1. image-compress: 上传正常图片→压缩→下载；上传SVG→被拒绝；上传>10MB→提示超限
2. regex-tester: 输入灾难性回溯正则→Worker超时提示；匹配结果正确高亮
3. json-formatter: 粘贴超1MB JSON→提示超限；粘贴含script标签→textContent转义
