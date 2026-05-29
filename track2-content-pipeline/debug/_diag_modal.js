(function(){
    var result = {};

    // 1. Check cheetah-modal
    var cm = document.querySelector('[role="dialog"].cheetah-modal');
    if (cm) {
        result.cheetah_visible = cm.offsetParent !== null;
        result.cheetah_text = (cm.innerText || '').trim().substring(0, 500);

        // Find all buttons
        var btns = cm.querySelectorAll('button');
        result.cheetah_buttons = [];
        for (var i = 0; i < btns.length; i++) {
            var b = btns[i];
            result.cheetah_buttons.push({
                text: (b.innerText || '').trim(),
                className: (b.className || '').substring(0, 80),
                disabled: b.disabled,
                visible: b.offsetParent !== null
            });
        }
    } else {
        result.cheetah_modal = 'not found';
    }

    // 2. Check for form elements
    var forms = document.querySelectorAll('form');
    result.forms_count = forms.length;
    result.form_details = [];
    for (var f = 0; f < forms.length; f++) {
        var form = forms[f];
        result.form_details.push({
            visible: form.offsetParent !== null,
            html_snippet: form.outerHTML.substring(0, 500)
        });
    }

    // 3. Check URL and title input
    result.url = window.location.href;

    // 4. Check if there are any error/toast messages
    var allDivs = document.querySelectorAll('div');
    for (var d = 0; d < allDivs.length; d++) {
        var div = allDivs[d];
        var t = (div.innerText || '').trim();
        if (t.indexOf('错误') !== -1 || t.indexOf('失败') !== -1 || t.indexOf('请') !== -1) {
            if (t.length < 100 && div.offsetParent !== null) {
                result.error_msg = t;
                break;
            }
        }
    }

    return JSON.stringify(result);
})()
