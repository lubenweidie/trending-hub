(function(){
    // Find and click "作品管理" in sidebar
    var all = document.querySelectorAll('div, span, a, li');
    for (var i = 0; i < all.length; i++) {
        var el = all[i];
        if (el.children.length === 0 && (el.innerText || '').trim() === '作品管理') {
            // Click the clickable parent
            var p = el;
            while (p) {
                if (p.tagName === 'A' || p.onclick || p.getAttribute('data-url')) {
                    p.click();
                    return 'clicked 作品管理 via ' + p.tagName;
                }
                p = p.parentElement;
            }
            el.click();
            return 'clicked 作品管理 (leaf)';
        }
    }
    return 'not found';
})()
