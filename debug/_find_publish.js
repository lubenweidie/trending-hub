(function(){
    var result = [];
    // Get the full text of main content area to understand the layout
    var body = document.body.innerText || '';
    result.push('BODY_TEXT:' + body.substring(0, 1500));
    // Find ALL buttons with their classes
    var btns = document.querySelectorAll('button');
    for (var i = 0; i < btns.length; i++) {
        var b = btns[i];
        if (b.offsetParent === null) continue;
        var t = (b.innerText||'').trim();
        if (t) result.push('BTN[' + b.className.substring(0,40) + ']:' + t.substring(0,20));
    }
    // Find elements that might contain "发布" text
    var all = document.querySelectorAll('*');
    for (var j = 0; j < all.length; j++) {
        var el = all[j];
        if (el.children.length > 0) continue;
        var et = (el.innerText||'').trim();
        if (et === '发布' || et === '立即发布' || et === '公开发布') {
            result.push('PUBLISH_ELEM:' + el.tagName + '.' + (el.className||'').substring(0,40));
        }
    }
    return JSON.stringify(result.slice(0, 30));
})()
