(function(){
    var result = [];
    // Check current URL
    result.push('URL:' + window.location.href);
    // Find main content area - not sidebar/header
    var main = document.querySelector('[class*="content"], [class*="main"], [class*="works"], [class*="list"], [class*="table"]');
    if (main) {
        result.push('MAIN:' + (main.innerText||'').trim().substring(0, 500));
    }
    // Find all buttons
    var btns = document.querySelectorAll('button');
    for (var i = 0; i < btns.length; i++) {
        var b = btns[i];
        var t = (b.innerText||'').trim();
        if (t && t.length < 20) result.push('BTN:' + t);
    }
    // Find action links/buttons
    var spans = document.querySelectorAll('span');
    for (var j = 0; j < spans.length; j++) {
        var s = spans[j];
        var st = (s.innerText||'').trim();
        if ((st === '发布' || st === '编辑' || st === '删除' || st === '存草稿') && s.children.length === 0) {
            result.push('ACTION:' + st + ' parent:' + (s.parentElement? s.parentElement.tagName : ''));
        }
    }
    return JSON.stringify(result.slice(0, 30));
})()
