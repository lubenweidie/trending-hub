(function(){
    var result = [];
    // Find ALL visible modals
    var modals = document.querySelectorAll('.modal.fade,.ant-modal,[role="dialog"],.modal');
    for (var m = 0; m < modals.length; m++) {
        var md = modals[m];
        if (md.offsetParent === null && md.style.display === 'none') continue;
        result.push('=== MODAL ' + m + ' ===');
        result.push('CLASS:' + (md.className||'').substring(0,100));
        result.push('ID:' + (md.id||''));
        result.push('HTML:' + md.outerHTML.substring(0, 1500));
        result.push('TEXT:' + (md.innerText||'').trim().substring(0, 500));
    }
    // Also find any dialog/overlay
    var dialogs = document.querySelectorAll('[class*="dialog"], [class*="Dialog"], [class*="overlay"], [class*="Overlay"]');
    for (var d = 0; d < dialogs.length; d++) {
        var dg = dialogs[d];
        if (dg.offsetParent === null) continue;
        var dt = (dg.innerText||'').trim();
        if (dt && dt.length < 200) {
            result.push('DIALOG:' + dg.className.substring(0,60) + ' -> ' + dt.substring(0,150));
        }
    }
    return JSON.stringify(result.slice(0, 15));
})()
