// regex-worker.js — runs regex matching in a Web Worker to prevent ReDoS main-thread blocking
self.onmessage = function(e) {
    var pattern = e.data.pattern;
    var flags = e.data.flags;
    var text = e.data.text;
    try {
        var re = new RegExp(pattern, flags);
        var matches = [];
        var match;
        if (flags.indexOf('g') !== -1) {
            while ((match = re.exec(text)) !== null) {
                matches.push({
                    index: match.index,
                    full: match[0],
                    groups: match.slice(1)
                });
                if (match[0].length === 0) re.lastIndex++;
            }
        } else {
            match = re.exec(text);
            if (match) {
                matches.push({
                    index: match.index,
                    full: match[0],
                    groups: match.slice(1)
                });
            }
        }
        self.postMessage({ success: true, matches: matches });
    } catch (e) {
        self.postMessage({ success: false, error: e.message });
    }
};
