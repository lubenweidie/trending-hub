(function(){
    var cm = document.querySelector('[role="dialog"].cheetah-modal');
    if (!cm) return 'no cheetah modal';
    var btns = cm.querySelectorAll('button');
    var result = [];
    for (var i = 0; i < btns.length; i++) {
        var b = btns[i];
        result.push({
            text: (b.innerText||'').trim(),
            class: (b.className||'').substring(0, 80),
            ref: b.getAttribute('data-opencli-ref')||''
        });
    }
    return JSON.stringify(result);
})()
