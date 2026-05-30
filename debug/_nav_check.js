(function(){
    var result = [];
    var containers = document.querySelectorAll('[class*="nav"], [class*="menu"], [class*="tab"], [class*="sidebar"], [class*="sider"], [class*="header"]');
    for (var i = 0; i < containers.length; i++) {
        var c = containers[i];
        if (c.offsetParent === null) continue;
        var text = (c.innerText || '').trim();
        if (text && text.length < 100) {
            result.push(text.substring(0, 80));
        }
    }
    var links = document.querySelectorAll('a');
    for (var j = 0; j < links.length; j++) {
        var l = links[j];
        var t = (l.innerText || '').trim();
        if (t && t.length < 30) {
            result.push('LINK:' + t + ' -> ' + (l.href || '').substring(0, 80));
        }
    }
    return JSON.stringify(result.slice(0, 30));
})()
