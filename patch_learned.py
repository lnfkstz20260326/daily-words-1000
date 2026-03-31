#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修改daily-words-1000的HTML文件：
1. 7轮循环完成后标记已学习（写入localStorage learnedDays_uid）
2. 返回首页时带uid和name参数
3. 删除原来的"页面加载就标记"的错误逻辑
"""

import os
import re
import glob

WORK_DIR = r"C:\Users\Lenovo\WorkBuddy\daily-words-1000"

# 旧的进度追踪脚本块（完整匹配，替换掉）
OLD_TRACKING = '''<script>
// 学习进度追踪
function markAsLearned() {
    var dayNum = 1;
    var key = 'daily-words-1000-day-' + dayNum;
    localStorage.setItem(key, 'learned');
}

// 页面加载时标记为已学习
if (document.readyState === 'complete') {
    markAsLearned();
} else {
    window.addEventListener('load', markAsLearned);
}
</script>'''

# 新的进度追踪脚本块（7轮完成后才标记）
NEW_TRACKING = '''<script>
// ========== 学习进度追踪（7轮完成后才标记已学习）==========
(function() {
    var urlParams = new URLSearchParams(window.location.search);
    var userUID = urlParams.get('uid') || 'default';
    var userName = decodeURIComponent(urlParams.get('name') || '');
    var dayNum = parseInt(urlParams.get('day') || '0');
    var TOTAL_DAYS = 641;

    window._markLearnedIfDone = function(completedLoops, maxLoops) {
        // 只有7轮全部完成，且有uid和dayNum时才标记
        if (completedLoops < maxLoops) return;
        if (!dayNum || userUID === 'default') return;

        var KEY_LEARNED = 'learnedDays_' + userUID;
        var KEY_CURRENT = 'currentDay_' + userUID;

        var stored = localStorage.getItem(KEY_LEARNED);
        var learnedDays = stored ? JSON.parse(stored) : [];
        if (!learnedDays.includes(dayNum)) {
            learnedDays.push(dayNum);
            localStorage.setItem(KEY_LEARNED, JSON.stringify(learnedDays));
        }
        // 更新当前天为下一个未学习的天
        var nextDay = dayNum + 1;
        while (nextDay <= TOTAL_DAYS && learnedDays.includes(nextDay)) {
            nextDay++;
        }
        if (nextDay <= TOTAL_DAYS) {
            localStorage.setItem(KEY_CURRENT, nextDay.toString());
        }
    };

    // 返回首页时带uid和name参数
    window._buildIndexURL = function() {
        var base = 'index.html';
        if (userUID && userUID !== 'default') {
            base += '?uid=' + encodeURIComponent(userUID) + '&name=' + encodeURIComponent(userName);
        }
        return base;
    };
})();
</script>'''

# 旧的 goBack 函数
OLD_GOBACK = """// ========== 返回首页 ==========
function goBack() {
    stopSpeaking();
    setTimeout(() => {
        location.href = 'index.html';
    }, 100);
}"""

# 新的 goBack 函数
NEW_GOBACK = """// ========== 返回首页 ==========
function goBack() {
    stopSpeaking();
    setTimeout(() => {
        location.href = (typeof _buildIndexURL === 'function') ? _buildIndexURL() : 'index.html';
    }, 100);
}"""

# 旧的播放结束标志
OLD_END = """    // 播放结束
    isPlaying = false;
    statusDiv.textContent = '✅ 完成';
    btn.textContent = '▶️ 开始循环朗读';
}"""

# 新的播放结束标志（完成7轮后标记已学习）
NEW_END = """    // 播放结束
    isPlaying = false;
    statusDiv.textContent = '✅ 完成';
    btn.textContent = '▶️ 开始循环朗读';
    // 7轮完成，标记已学习
    if (typeof _markLearnedIfDone === 'function') {
        _markLearnedIfDone(currentLoop, maxLoops);
    }
}"""

html_files = glob.glob(os.path.join(WORK_DIR, "20*.html"))
html_files.sort()

ok = 0
skip = 0
err = 0

for fpath in html_files:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    changed = False

    # 1. 替换旧进度追踪脚本
    if OLD_TRACKING in content:
        content = content.replace(OLD_TRACKING, NEW_TRACKING)
        changed = True

    # 2. 替换 goBack 函数
    if OLD_GOBACK in content:
        content = content.replace(OLD_GOBACK, NEW_GOBACK)
        changed = True

    # 3. 替换播放结束逻辑
    if OLD_END in content:
        content = content.replace(OLD_END, NEW_END)
        changed = True

    if changed:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        ok += 1
    else:
        skip += 1

print(f"✅ 修改完成：{ok} 个文件已更新，{skip} 个跳过，{err} 个出错")
