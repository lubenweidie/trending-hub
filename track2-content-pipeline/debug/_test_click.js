(function(){
    var cm = document.querySelector('[role="dialog"].cheetah-modal');
    if (!cm) return 'no_cheetah_modal';

    // Find the confirm button
    var btns = cm.querySelectorAll('button');
    var confirmBtn = null;
    for (var i = 0; i < btns.length; i++) {
        var t = (btns[i].innerText || '').trim();
        if (t.indexOf('确定') !== -1) {
            confirmBtn = btns[i];
            break;
        }
    }
    if (!confirmBtn) return 'no_confirm_btn';

    // Try Approach 1: Dispatch full mouse event sequence with coordinates
    var rect = confirmBtn.getBoundingClientRect();
    var cx = rect.left + rect.width / 2;
    var cy = rect.top + rect.height / 2;

    var events = [];
    ['mousedown', 'mouseup', 'click'].forEach(function(evtType) {
        var evt = new MouseEvent(evtType, {
            bubbles: true,
            cancelable: true,
            view: window,
            clientX: cx,
            clientY: cy,
            button: 0
        });
        confirmBtn.dispatchEvent(evt);
        events.push(evtType + ':dispatched');
    });

    // Wait a moment and check
    return JSON.stringify({
        dispatched: events,
        btnText: (confirmBtn.innerText || '').trim(),
        btnRect: {x: Math.round(cx), y: Math.round(cy)},
        hasPointerEvents: typeof PointerEvent !== 'undefined'
    });
})()
