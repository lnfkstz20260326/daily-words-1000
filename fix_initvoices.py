"""
fix_initvoices.py
只改 initVoices 函数：加超时兜底，手机端 onvoiceschanged 不触发时也能继续播放
其余代码完全不动
"""
import glob, os

OLD = """function initVoices() {
    return new Promise((resolve) => {
        allVoices = window.speechSynthesis.getVoices();
        if (allVoices.length > 0) {
            resolve();
        } else {
            window.speechSynthesis.onvoiceschanged = () => {
                allVoices = window.speechSynthesis.getVoices();
                resolve();
            };
        }
    });
}"""

NEW = """function initVoices() {
    return new Promise((resolve) => {
        allVoices = window.speechSynthesis.getVoices();
        if (allVoices.length > 0) {
            resolve();
            return;
        }
        var resolved = false;
        function done() {
            if (resolved) return;
            resolved = true;
            allVoices = window.speechSynthesis.getVoices();
            resolve();
        }
        window.speechSynthesis.onvoiceschanged = done;
        // 手机端兜底：最多等1秒，不管有没有触发都继续
        setTimeout(done, 1000);
    });
}"""

files = sorted(glob.glob('20??-??-??.html'))
ok = 0
skip = 0
for f in files:
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    if OLD in content:
        content = content.replace(OLD, NEW)
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write(content)
        ok += 1
    else:
        skip += 1

print(f'修复: {ok}/{len(files)}  跳过(已是新版): {skip}')
