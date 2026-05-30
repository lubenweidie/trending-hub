// 闲鱼 MTOP PC 发布: 【AI简历优化】资深HR级智能体 自动诊断+改写 求职/跳槽/校招通用 秒出Ma
// 复制整段代码 → 在 goofish.com 控制台粘贴 → 回车执行

(function() {
  // 生成 uniqueCode
  var uniqueCode = crypto.randomUUID ? crypto.randomUUID().replace(/-/g, '') : 'xxxxxxxxxxxx4xxxyxxxxxxxxxxxxxxx'.replace(/[xy]/g, function(c) { var r = Math.random()*16|0, v = c === 'x' ? r : (r&0x3|0x8); return v.toString(16); });

  var publishData = {"title": "【AI简历优化】资深HR级智能体 自动诊断+改写 求职/跳槽/校招通用 秒出Markdown排版", "price": 9900, "description": "【简历优化助手】Coze AI 智能体模板\n\n📌 适用人群：求职者、应届生、职场跳槽\n📂 分类：职场\n\n━━━━━━ 功能介绍 ━━━━━━\n✅ **3 大问题诊断** — 结构混乱？用词不专业？成果没量化？一键定位\n✅ **修改前后对比** — 每个问题给出原文 vs 优化版，看得见的提升\n✅ **完整简历输出** — 直接生成优化后的完整简历，Markdown 格式，复制即用\n✅ **1-10 分评分** — 量化你的简历水平，给出改进方向\n\n━━━━━━ 版本与价格 ━━━━━━\n🔹 标准版：¥99\n   → 智能体模板文件，一键导入你的 Coze 账号，永久使用\n\n🔹 定制版：¥299\n   → 标准版全部内容 + 深度定制优化\n\n━━━━━━ 使用方式 ━━━━━━\n1️⃣ 在应用商店下载\"扣子\"APP 或访问 coze.cn 注册（免费）\n2️⃣ 收到模板文件后一键导入\n3️⃣ 按说明输入内容，秒出结果\n\n━━━━━━ 买家必读 ━━━━━━\n⚠️ 本商品为虚拟商品，售出不退不换\n📱 需要自行注册 Coze 账号（完全免费）\n🔒 在你自己账号下运行，数据不上传第三方\n💬 使用问题随时问我，看到必回\n\n💡 下单后秒发货！如未及时回复请稍等，24h内必发。\n", "categoryId": "50025969", "condition": 1, "freight": {"type": "free"}, "location": {"province": "广东", "city": "深圳", "district": "南山区"}, "itemType": "virtual", "itemTypeStr": "b", "quantity": "1", "freebies": false, "simpleItem": "true"};
  publishData.uniqueCode = uniqueCode;
  publishData.bizcode = 'pcMainPublish';
  publishData.publishScene = 'pcMainPublish';

  console.log('正在发布: ' + publishData.title);
  console.log('uniqueCode: ' + uniqueCode);

  window.lib.mtop.request({
    api: 'mtop.idle.pc.idleitem.publish',
    v: '1.0',
    data: publishData
  }).then(function(res) {
    var ret = res.ret || [];
    if (ret[0] && ret[0].indexOf('SUCCESS') === 0) {
      console.log('===== 发布成功! =====');
      console.log('itemId:', res.data && res.data.itemId);
      console.log(JSON.stringify(res, null, 2));
    } else {
      console.log('===== 发布失败 =====');
      console.log('ret:', JSON.stringify(ret));
      console.log('完整响应:', JSON.stringify(res, null, 2));
    }
  }).catch(function(e) {
    console.error('===== 请求异常 =====');
    console.error('ret:', JSON.stringify(e.ret || e));
    console.error('message:', e.message || '');
    console.error('完整:', JSON.stringify(e, null, 2));
  });
})();
