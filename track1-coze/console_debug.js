// 在 goofish.com 控制台粘贴运行
// 拦截 MTOP 请求，捕获完整的请求URL + 响应头

(function() {
  console.clear();
  console.log('=== MTOP 请求拦截器已启动 ===');
  console.log('请刷新页面(F5)，然后查看下方输出');
  console.log('');

  // 1. 先打印当前浏览器可见的 Cookie
  console.log('--- 当前可见 Cookie ---');
  console.log(document.cookie);
  console.log('');

  // 2. 拦截 fetch (MTOP 2.x 使用 fetch)
  const origFetch = window.fetch;
  window.fetch = function(...args) {
    const url = typeof args[0] === 'string' ? args[0] : args[0].url;
    if (url.includes('mtop') || url.includes('h5api')) {
      console.log('>>> MTOP FETCH <<<');
      console.log('URL:', url);
      console.log('Options:', JSON.stringify(args[1] || {}, null, 2));

      return origFetch.apply(this, args).then(resp => {
        // 克隆响应以读取 headers
        const cloned = resp.clone();
        console.log('Status:', resp.status);
        console.log('Response Headers:');
        resp.headers.forEach((v, k) => {
          if (k.toLowerCase().includes('cookie') || k.toLowerCase().includes('token') || k.toLowerCase().includes('set-cookie') || k.toLowerCase().includes('h5')) {
            console.log(`  ${k}: ${v}`);
          }
        });

        // 尝试读 body
        cloned.text().then(t => {
          console.log('Body (前500字符):', t.substring(0, 500));
        }).catch(() => {});

        return resp;
      });
    }
    return origFetch.apply(this, args);
  };

  // 3. 拦截 XMLHttpRequest
  const OrigXHR = window.XMLHttpRequest;
  window.XMLHttpRequest = function() {
    const xhr = new OrigXHR();
    const origOpen = xhr.open;
    const origSend = xhr.send;
    const origSetHeader = xhr.setRequestHeader;
    let _url = '', _method = '';

    xhr.open = function(method, url, ...rest) {
      _url = url;
      _method = method;
      return origOpen.apply(this, [method, url, ...rest]);
    };

    xhr.send = function(...args) {
      if (_url.includes('mtop') || _url.includes('h5api')) {
        console.log('>>> MTOP XHR <<<');
        console.log(_method, _url);

        xhr.addEventListener('load', function() {
          console.log('Status:', xhr.status);
          console.log('Response Headers:', xhr.getAllResponseHeaders());
          console.log('Body (前500):', xhr.responseText.substring(0, 500));
        });
      }
      return origSend.apply(this, args);
    };

    return xhr;
  };

  console.log('就绪！请按 F5 刷新页面');
})();
