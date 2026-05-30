// 测试 goofish.com MTOP 连接（只读，安全）
// 在 goofish.com 控制台粘贴执行

window.lib.mtop.request({
  api: 'mtop.idle.web.user.page.nav',
  v: '1.0',
  data: {}
}).then(function(r) {
  console.log('连接成功! 用户信息:');
  console.log(JSON.stringify(r, null, 2));
}).catch(function(e) {
  console.error('连接失败:');
  console.error(JSON.stringify(e, null, 2));
});
