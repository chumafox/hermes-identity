tell application "Safari"
    do JavaScript "
        var links = document.querySelectorAll('a');
        var unique = {};
        for(var i=0; i<links.length; i++) {
            var h = links[i].href;
            if(h && h.match(/SITE\\.ru\\/\\d+[a-z\\-]*\\.html/)) {
                unique[h] = 1;
            }
        }
        var result = '';
        for(var url in unique) result += url + '\\n';
        result;
    " in current tab of window 1
end tell
