#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
碎片化累计升级脚本
- 每完成1轮立即保存到 localStorage
- 累计7轮才标记已学习
- 同时升级 index.html 导出/导入进度码功能
"""

import glob
import os
import re

WORKDIR = r"C:\Users\Lenovo\WorkBuddy\daily-words-1000"

# ============================================================
# 1. 替换 HTML 文件中的 JS 逻辑
# ============================================================

# 旧的：每轮结束后等待（无保存），7轮完成后才标记
OLD_LOOP_END = '''        // 每轮结束后等待2秒
        if (isPlaying && currentLoop < maxLoops) {
            await sleep(2000);
        }
    }'''

# 新的：每轮结束后立即保存轮数，再等待
NEW_LOOP_END = '''        // 每轮结束 - 立即保存累计轮数
        if (typeof _saveRoundProgress === 'function') {
            _saveRoundProgress(currentLoop);
        }
        // 每轮结束后等待2秒
        if (isPlaying && currentLoop < maxLoops) {
            await sleep(2000);
        }
    }'''

# 旧的：播放结束后调用 _markLearnedIfDone
OLD_MARK = '''    // 7轮完成，标记已学习
    if (typeof _markLearnedIfDone === 'function') {
        _markLearnedIfDone(currentLoop, maxLoops);
    }'''

# 新的：播放结束后也调用（兜底，确保7轮时标记）
NEW_MARK = '''    // 播放结束，检查是否已累计7轮
    if (typeof _markLearnedIfDone === 'function') {
        _markLearnedIfDone(currentLoop, maxLoops);
    }'''

# 旧的进度追踪脚本块（完整替换）
OLD_PROGRESS_SCRIPT = '''<script>
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

NEW_PROGRESS_SCRIPT = '''<script>
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
    var KEY_ROUNDS  = 'roundsData_' + userUID;  // {dayNum: 已完成轮数}

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
        // 只增不减：取当前存储值和本次播放进度的较大值
        data[dayNum] = Math.max(data[dayNum] || 0, completedLoops);
        localStorage.setItem(KEY_ROUNDS, JSON.stringify(data));

        // 检查是否已累计够7轮
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
        // 更新当前天为下一个未学习的天
        var nextDay = day + 1;
        while (nextDay <= TOTAL_DAYS && learnedDays.includes(nextDay)) {
            nextDay++;
        }
        if (nextDay <= TOTAL_DAYS) {
            localStorage.setItem(KEY_CURRENT, nextDay.toString());
        }
    }

    // 兜底：播放结束时也检查（兼容旧逻辑）
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
</script>'''


def upgrade_html_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    changed = False

    # 1. 替换每轮结束保存逻辑
    if OLD_LOOP_END in content:
        content = content.replace(OLD_LOOP_END, NEW_LOOP_END)
        changed = True

    # 2. 替换播放结束标记逻辑
    if OLD_MARK in content:
        content = content.replace(OLD_MARK, NEW_MARK)
        changed = True

    # 3. 替换进度追踪脚本块
    if OLD_PROGRESS_SCRIPT in content:
        content = content.replace(OLD_PROGRESS_SCRIPT, NEW_PROGRESS_SCRIPT)
        changed = True

    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    return changed


# ============================================================
# 2. 升级 index.html：导出/导入进度码
# ============================================================

# 旧的恢复进度函数（完整匹配）
OLD_RESTORE_FUNC = '''// 恢复进度（换设备后手动输入已学天数）
function restoreProgress() {
    var val = parseInt(document.getElementById('restore-day').value);
    if (!val || val < 1 || val > TOTAL_DAYS) {
        alert('请输入 1 ~ ' + TOTAL_DAYS + ' 之间的天数');
        return;
    }
    if (!confirm('将把第1天到第' + val + '天全部标记为已学习，确定吗？')) return;
    var days = [];
    for (var i = 1; i <= val; i++) { days.push(i); }
    saveLearnedDays(days);
    saveCurrentDay(val + 1 <= TOTAL_DAYS ? val + 1 : val);
    document.getElementById('restore-day').value = '';
    renderDaysGrid();
    updateStats();
    alert('✅ 进度已恢复到第' + val + '天！');'''

NEW_RESTORE_FUNC = '''// 恢复进度（换设备后手动输入已学天数）
function restoreProgress() {
    var val = parseInt(document.getElementById('restore-day').value);
    if (!val || val < 1 || val > TOTAL_DAYS) {
        alert('请输入 1 ~ ' + TOTAL_DAYS + ' 之间的天数');
        return;
    }
    if (!confirm('将把第1天到第' + val + '天全部标记为已学习，确定吗？')) return;
    var days = [];
    for (var i = 1; i <= val; i++) { days.push(i); }
    saveLearnedDays(days);
    // 同步设置每天轮数为7（碎片化数据）
    var KEY_ROUNDS = 'roundsData_' + userUID;
    var roundsData = {};
    for (var i = 1; i <= val; i++) { roundsData[i] = 7; }
    localStorage.setItem(KEY_ROUNDS, JSON.stringify(roundsData));
    saveCurrentDay(val + 1 <= TOTAL_DAYS ? val + 1 : val);
    document.getElementById('restore-day').value = '';
    renderDaysGrid();
    updateStats();
    alert('✅ 进度已恢复到第' + val + '天！');'''

# 旧的底部 HTML（重置+恢复进度区块）
OLD_BOTTOM_HTML = '''    <div style="text-align:right; padding: 16px 4px 0 0;">
        <span style="font-size:0.82em; color:#666;">📲 换设备？已学到第</span>
        <input type="number" id="restore-day" min="1" max="641" placeholder="天"
               style="width:54px; padding:4px 6px; border:1px solid #aaa; border-radius:6px; font-size:0.82em; text-align:center;" />
        <span style="font-size:0.82em; color:#666;">天</span>
        <button onclick="restoreProgress()"
                style="background:#43a047; color:white; border:none; border-radius:6px; padding:5px 10px; font-size:0.82em; cursor:pointer; margin-left:4px;">恢复进度</button>
    </div>
    <div style="text-align:right; padding: 6px 4px 4px 0;">
        <span onclick="resetProgress()" style="font-size:0.72em; color:#bbb; cursor:pointer; user-select:none;">重置进度</span>
    </div>
</div>'''

NEW_BOTTOM_HTML = '''    <div style="text-align:right; padding: 16px 4px 0 0; line-height:2.2;">
        <button onclick="exportProgress()"
                style="background:#1565c0; color:white; border:none; border-radius:6px; padding:5px 12px; font-size:0.82em; cursor:pointer; margin-right:6px;">📤 导出进度码</button>
        <span style="font-size:0.82em; color:#666;">换设备？粘贴进度码：</span>
        <input type="text" id="import-code" placeholder="粘贴进度码"
               style="width:110px; padding:4px 6px; border:1px solid #aaa; border-radius:6px; font-size:0.82em;" />
        <button onclick="importProgress()"
                style="background:#43a047; color:white; border:none; border-radius:6px; padding:5px 10px; font-size:0.82em; cursor:pointer; margin-left:4px;">导入恢复</button>
    </div>
    <div style="text-align:right; padding: 6px 4px 4px 0;">
        <span onclick="resetProgress()" style="font-size:0.72em; color:#bbb; cursor:pointer; user-select:none;">重置进度</span>
    </div>
</div>'''

# 在 resetProgress 函数前插入导出/导入函数
OLD_RESET_FUNC_START = '''// 重置进度
function resetProgress() {'''

NEW_EXPORT_IMPORT = '''// 导出进度码
function exportProgress() {
    var KEY_ROUNDS = 'roundsData_' + userUID;
    var learnedDays = getLearnedDays();
    var stored = localStorage.getItem(KEY_ROUNDS);
    var roundsData = stored ? JSON.parse(stored) : {};
    // 确保已学习的天都有rounds=7
    learnedDays.forEach(function(d) {
        if (!roundsData[d]) roundsData[d] = 7;
    });
    var payload = { v: 2, uid: userUID, r: roundsData };
    var code = btoa(unescape(encodeURIComponent(JSON.stringify(payload))));
    // 显示进度码并自动复制
    var msg = '📤 进度码（请截图或复制保存）：\\n\\n' + code + '\\n\\n点确定后自动复制到剪贴板';
    if (confirm(msg)) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(code).then(function() {
                alert('✅ 进度码已复制！在新设备粘贴导入即可恢复。');
            });
        } else {
            prompt('请手动复制以下进度码：', code);
        }
    }
}

// 导入进度码
function importProgress() {
    var code = document.getElementById('import-code').value.trim();
    if (!code) { alert('请先粘贴进度码'); return; }
    try {
        var json = decodeURIComponent(escape(atob(code)));
        var payload = JSON.parse(json);
        if (!payload.r) throw new Error('格式错误');
        var roundsData = payload.r;
        var KEY_ROUNDS = 'roundsData_' + userUID;
        // 合并：取两边较大值（保护本机已有进度）
        var stored = localStorage.getItem(KEY_ROUNDS);
        var existData = stored ? JSON.parse(stored) : {};
        Object.keys(roundsData).forEach(function(k) {
            existData[k] = Math.max(existData[k] || 0, roundsData[k]);
        });
        localStorage.setItem(KEY_ROUNDS, JSON.stringify(existData));
        // 同步 learnedDays
        var learnedDays = getLearnedDays();
        Object.keys(existData).forEach(function(k) {
            var d = parseInt(k);
            if (existData[k] >= 7 && !learnedDays.includes(d)) {
                learnedDays.push(d);
            }
        });
        saveLearnedDays(learnedDays);
        // 更新当前天
        var maxLearned = learnedDays.length > 0 ? Math.max.apply(null, learnedDays) : 0;
        var nextDay = maxLearned + 1;
        if (nextDay <= TOTAL_DAYS) saveCurrentDay(nextDay);
        document.getElementById('import-code').value = '';
        renderDaysGrid();
        updateStats();
        alert('✅ 进度恢复成功！共恢复 ' + learnedDays.length + ' 天记录。');
    } catch(e) {
        alert('❌ 进度码无效，请重新复制。');
    }
}

// 重置进度
function resetProgress() {'''

def upgrade_index_html(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    changed = False

    # 1. 替换底部 HTML（导出/导入 UI）
    if OLD_BOTTOM_HTML in content:
        content = content.replace(OLD_BOTTOM_HTML, NEW_BOTTOM_HTML)
        changed = True

    # 2. 在 resetProgress 前插入导出/导入函数
    if OLD_RESET_FUNC_START in content and 'exportProgress' not in content:
        content = content.replace(OLD_RESET_FUNC_START, NEW_EXPORT_IMPORT)
        changed = True

    # 3. 更新 restoreProgress 函数（同步 roundsData）
    if OLD_RESTORE_FUNC in content:
        content = content.replace(OLD_RESTORE_FUNC, NEW_RESTORE_FUNC)
        changed = True

    # 4. 移除已无用的旧 restore-day input（如还存在）
    # 已在 NEW_BOTTOM_HTML 里替换掉了，不用单独处理

    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    return changed


# ============================================================
# 主程序
# ============================================================
if __name__ == '__main__':
    os.chdir(WORKDIR)

    # 升级所有 HTML 文件（碎片化累计）
    html_files = sorted(glob.glob('20??-??-??.html'))
    ok = 0
    fail = 0
    skip = 0
    for f in html_files:
        try:
            if upgrade_html_file(f):
                ok += 1
            else:
                skip += 1
        except Exception as e:
            print(f'  ❌ {f}: {e}')
            fail += 1

    print(f'HTML文件: 更新 {ok} 个，跳过 {skip} 个，失败 {fail} 个')

    # 升级 index.html
    try:
        if upgrade_index_html('index.html'):
            print('index.html: ✅ 已升级（导出/导入进度码）')
        else:
            print('index.html: ⚠️ 未找到匹配内容，请检查')
    except Exception as e:
        print(f'index.html: ❌ {e}')

    print('\n✅ 全部完成！')
