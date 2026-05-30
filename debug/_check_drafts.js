(function(){
    var result = [];
    // Find all elements around the first draft item
    var bodyText = document.body.innerText || '';
    // Get structure around first draft
    var items = document.querySelectorAll('[class*="item"], [class*="row"], [class*="card"], tr, li');
    for (var i = 0; i < items.length; i++) {
        var item = items[i];
        var text = (item.innerText||'').trim();
        if (text.indexOf('一天消灭3万只蚊子') !== -1) {
            // Found a draft item, get its HTML
            result.push('DRAFT_HTML:' + item.outerHTML.substring(0, 1000));
            // Find all clickable elements in this item
            var clickable = item.querySelectorAll('button, a, span, div[class*="btn"], [class*="action"], [onclick]');
            for (var j = 0; j < clickable.length; j++) {
                var cl = clickable[j];
                var ct = (cl.innerText||'').trim();
                if (ct) result.push('CLICKABLE:' + ct + ' ' + cl.tagName + '.' + (cl.className||'').substring(0,40));
            }
            break;
        }
    }
    // Also look for "..." or more-actions buttons
    var all = document.querySelectorAll('*');
    for (var k = 0; k < all.length; k++) {
        var el = all[k];
        if (el.children.length > 0) continue;
        var t = (el.innerText||'').trim();
        if (t === '...' || t === '更多' || t === '操作') {
            result.push('MORE_BTN:' + el.tagName + '.' + (el.className||'').substring(0,40) + ' parent:' + (el.parentElement?el.parentElement.tagName:''));
        }
    }
    return JSON.stringify(result.slice(0, 20));
})()
