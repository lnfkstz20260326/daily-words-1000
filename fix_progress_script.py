#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
替换641个HTML文件的进度追踪脚本块
旧版：只有7轮全部完成才标记
新版：碎片化累计，每轮保存，累计7轮标记
"""
import glob, os, sys

WORKDIR = r"C:\Users\Lenovo\WorkBuddy\daily-words-1000"
os.chdir(WORKDIR)

OLD_SCRIPT = """<script>
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
</script>"""

NEW_SCRIPT = """<script>
// ========== 学习进度追踪（碎片化累计，每轮保存，累计7轮标记已学习）==========
(function() {
    var urlParams = new URLSearchParams(window.location.search);
    var userUID = urlParams.get('uid') || 'default';
    var userName = decodeURIComponent(urlParams.get('name') || '');
    var dayNum = parseInt(urlParams.get('day') || '0');
    var TOTAL_DAYS = 641;
    var ROUNDS_NEEDED = 7;

    var KEY_LEARNED = 'learnedDays_' + userUID;
    var KEY_CURRENT = 'currentDay_' + userUID;
    var KEY_ROUNDS  = 'roundsData_' + userUID;

    // 获取某天已完成轮数
    function getRounds(day) {
        if (!day || userUID === 'default') return 0;
        var stored = localStorage.getItem(KEY_ROUNDS);
        var data = stored ? JSON.parse(stored) : {};
        return data[day] || 0;
    }

    // 每完成1轮立即保存（碎片化核心）
    window._saveRoundProgress = function(completedLoops) {
        if (!dayNum || userUID === 'default') return;
        var stored = localStorage.getItem(KEY_ROUNDS);
        var data = stored ? JSON.parse(stored) : {};
        data[dayNum] = Math.max(data[dayNum] || 0, completedLoops);
        localStorage.setItem(KEY_ROUNDS, JSON.stringify(data));
        if (data[dayNum] >= ROUNDS_NEEDED) {
            _doMarkLearned(dayNum);
        }
    };

    // 标记某天为已学习
    function _doMarkLearned(day) {
        var stored = localStorage.getItem(KEY_LEARNED);
        var learnedDays = stored ? JSON.parse(stored) : [];
        if (!learnedDays.includes(day)) {
            learnedDays.push(day);
            localStorage.setItem(KEY_LEARNED, JSON.stringify(learnedDays));
        }
        var nextDay = day + 1;
        while (nextDay <= TOTAL_DAYS && learnedDays.includes(nextDay)) {
            nextDay++;
        }
        if (nextDay <= TOTAL_DAYS) {
            localStorage.setItem(KEY_CURRENT, nextDay.toString());
        }
    }

    // 兜底：播放结束时也检查
    window._markLearnedIfDone = function(completedLoops, maxLoops) {
        if (!dayNum || userUID === 'default') return;
        window._saveRoundProgress(completedLoops);
    };

    // 返回首页时带uid和name参数
    window._buildIndexURL = function() {
        var base = 'index.html';
        if (userUID && userUID !== 'default') {
            base += '?uid=' + encodeURIComponent(userUID) + '&name=' + encodeURIComponent(userName);
        }
        return base;
    };

    // 页面加载时显示当天已完成轮数提示
    window.addEventListener('load', function() {
        if (!dayNum || userUID === 'default') return;
        var done = getRounds(dayNum);
        if (done > 0 && done < ROUNDS_NEEDED) {
            var statusDiv = document.getElementById('loopStatus');
            if (statusDiv) {
                statusDiv.textContent = '📌 已累计 ' + done + '/' + ROUNDS_NEEDED + ' 轮，继续加油！';
            }
        }
    });
})();
</script>"""

files = sorted(glob.glob('20??-??-??.html'))
ok = skip = fail = 0

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as fh:
            c = fh.read()
        if OLD_SCRIPT in c:
            c = c.replace(OLD_SCRIPT, NEW_SCRIPT)
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write(c)
            ok += 1
        elif 'roundsData_' in c:
            skip += 1  # 已经是新版
        else:
            fail += 1
            print(f'  WARN: {f} 无法匹配')
    except Exception as e:
        print(f'  ERROR: {f}: {e}')
        fail += 1

print(f'HTML文件: 更新{ok}个，跳过{skip}个，失败{fail}个，共{len(files)}个')
