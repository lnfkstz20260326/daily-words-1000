# -*- coding: utf-8 -*-
"""
fix_mobile.py
只做两件事：
1. 修复按钮布局：小屏幕下每行1个按钮，整齐垂直排列
2. 修复手机端自动播放：点击按钮时先用一次空语音解锁Web Speech API权限
不动任何声音选择逻辑（保护电脑端男声）
"""
import glob, os

WORKDIR = r'C:\Users\Lenovo\WorkBuddy\daily-words-1000'
os.chdir(WORKDIR)

# ===== 修改1：CSS按钮样式 =====
# 旧的按钮组CSS（flex-wrap布局，会导致手机端5+1=6个按钮乱排）
OLD_BTN_CSS = """.button-group {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    justify-content: center;
}
.btn {
    padding: 6px 12px;
    border: none;
    border-radius: 15px;
    cursor: pointer;
    font-size: 0.85em;
    transition: all 0.3s;
}"""

# 新的按钮组CSS：手机端改为grid 2列，停止按钮单独一行居中
NEW_BTN_CSS = """.button-group {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
    justify-items: center;
    margin-top: 4px;
}
.button-group .btn-stop {
    grid-column: 1 / -1;
}
.btn {
    width: 100%;
    padding: 7px 8px;
    border: none;
    border-radius: 15px;
    cursor: pointer;
    font-size: 0.85em;
    transition: all 0.3s;
    white-space: nowrap;
}"""

# ===== 修改2：播放解锁 =====
# 在 startAutoPlay 函数开头，等待语音初始化之后、设置isPlaying=true之前
# 插入一个解锁用的空语音（静音播放，时长极短，目的是让浏览器允许后续自动播放）
OLD_UNLOCK = """    // 等待语音初始化
    await initVoices();
    
    isPlaying = true;"""

NEW_UNLOCK = """    // 等待语音初始化
    await initVoices();

    // 手机端解锁：用一次极短的空语音触发浏览器语音权限
    await new Promise((resolve) => {
        const u = new SpeechSynthesisUtterance(' ');
        u.volume = 0;
        u.rate = 2;
        u.onend = resolve;
        u.onerror = resolve;
        window.speechSynthesis.speak(u);
        setTimeout(resolve, 300);
    });

    isPlaying = true;"""

html_files = sorted(glob.glob('20??-??-??.html'))
ok_css = 0
ok_unlock = 0
skip_css = 0
skip_unlock = 0

for f in html_files:
    with open(f, 'r', encoding='utf-8') as fh:
        c = fh.read()
    
    changed = False
    
    if OLD_BTN_CSS in c:
        c = c.replace(OLD_BTN_CSS, NEW_BTN_CSS)
        ok_css += 1
        changed = True
    else:
        skip_css += 1
    
    if OLD_UNLOCK in c:
        c = c.replace(OLD_UNLOCK, NEW_UNLOCK)
        ok_unlock += 1
        changed = True
    else:
        skip_unlock += 1
    
    if changed:
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write(c)

print(f'CSS按钮布局修复: {ok_css}/{len(html_files)} 文件 (跳过:{skip_css})')
print(f'播放解锁修复:    {ok_unlock}/{len(html_files)} 文件 (跳过:{skip_unlock})')
print('完成')
