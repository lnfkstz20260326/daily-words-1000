#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把640个旧版HTML文件的进度追踪脚本替换成碎片化累计新版
旧版特征：含 'daily-words-1000-day-' 字样
新版：每轮保存，累计7轮标记已学习，支持导出/导入进度码
"""
import glob, os, re

WORKDIR = r"C:\Users\Lenovo\WorkBuddy\daily-words-1000"
os.chdir(WORKDIR)

# 旧版进度脚本的特征字符串（用正则匹配整个script块）
OLD_PATTERN = re.compile(
    r'<script>\s*// 学习进度追踪\s*\n.*?</script>',
    re.DOTALL
)

def make_new_script(day_num):
    return f"""<script>
// ========== 学习进度追踪（碎片化累计，每轮保存，累计7轮标记已学习）==========
(function() {{
    var urlParams = new URLSearchParams(window.location.search);
    var userUID = urlParams.get('uid') || 'default';
    var userName = decodeURIComponent(urlParams.get('name') || '');
    var dayNum = {day_num};
    var TOTAL_DAYS = 641;
    var ROUNDS_NEEDED = 7;

    var KEY_LEARNED = 'learnedDays_' + userUID;
    var KEY_CURRENT = 'currentDay_' + userUID;
    var KEY_ROUNDS  = 'roundsData_' + userUID;

    function getRounds(day) {{
        if (!day || userUID === 'default') return 0;
        var stored = localStorage.getItem(KEY_ROUNDS);
        var data = stored ? JSON.parse(stored) : {{}};
        return data[day] || 0;
    }}

    window._saveRoundProgress = function(completedLoops) {{
        if (!dayNum || userUID === 'default') return;
        var stored = localStorage.getItem(KEY_ROUNDS);
        var data = stored ? JSON.parse(stored) : {{}};
        data[dayNum] = Math.max(data[dayNum] || 0, completedLoops);
        localStorage.setItem(KEY_ROUNDS, JSON.stringify(data));
        if (data[dayNum] >= ROUNDS_NEEDED) {{
            _doMarkLearned(dayNum);
        }}
    }};

    function _doMarkLearned(day) {{
        var stored = localStorage.getItem(KEY_LEARNED);
        var learnedDays = stored ? JSON.parse(stored) : [];
        if (!learnedDays.includes(day)) {{
            learnedDays.push(day);
            localStorage.setItem(KEY_LEARNED, JSON.stringify(learnedDays));
        }}
        var nextDay = day + 1;
        while (nextDay <= TOTAL_DAYS && learnedDays.includes(nextDay)) {{
            nextDay++;
        }}
        if (nextDay <= TOTAL_DAYS) {{
            localStorage.setItem(KEY_CURRENT, nextDay.toString());
        }}
    }}

    window._markLearnedIfDone = function(completedLoops, maxLoops) {{
        if (!dayNum || userUID === 'default') return;
        window._saveRoundProgress(completedLoops);
    }};

    window._buildIndexURL = function() {{
        var base = 'index.html';
        if (userUID && userUID !== 'default') {{
            base += '?uid=' + encodeURIComponent(userUID) + '&name=' + encodeURIComponent(userName);
        }}
        return base;
    }};

    window.addEventListener('load', function() {{
        if (!dayNum || userUID === 'default') return;
        var done = getRounds(dayNum);
        if (done > 0 && done < ROUNDS_NEEDED) {{
            var statusDiv = document.getElementById('loopStatus');
            if (statusDiv) {{
                statusDiv.textContent = '📌 已累计 ' + done + '/' + ROUNDS_NEEDED + ' 轮，继续加油！';
            }}
        }}
    }});
}})();
</script>"""

# 处理640个旧版文件
files = sorted(glob.glob('20??-??-??.html'))
ok = skip = fail = 0

for f in files:
    with open(f, 'r', encoding='utf-8') as fh:
        c = fh.read()

    # 跳过已经是新版的
    if 'roundsData_' in c:
        skip += 1
        continue

    # 从文件名提取天数（需要从URL参数里读，或从文件内容里找day=N）
    # 查找 var dayNum = N; 或 'day-' + dayNum 里的数字
    # 旧版里是 var dayNum = N;
    day_match = re.search(r"var dayNum\s*=\s*(\d+);", c)
    if not day_match:
        # 尝试从文件内找 day-N 的数字
        day_match2 = re.search(r"'daily-words-1000-day-'\s*\+\s*dayNum.*?var dayNum\s*=\s*(\d+)", c, re.DOTALL)
        if not day_match2:
            # 从文件名推算不了，直接从内容找
            day_match3 = re.search(r"markAsLearned\(\).*?var dayNum\s*=\s*(\d+)", c, re.DOTALL)
            if not day_match3:
                print(f"  WARN: {f} 找不到dayNum")
                fail += 1
                continue
            day_num = int(day_match3.group(1))
        else:
            day_num = int(day_match2.group(1))
    else:
        day_num = int(day_match.group(1))

    # 也要确保有 _saveRoundProgress 的钩子（每轮保存）
    # 旧版文件里 while loop 结束部分可能也需要插入钩子
    new_script = make_new_script(day_num)

    # 替换旧的进度脚本块
    new_c, n = OLD_PATTERN.subn(new_script, c)
    if n == 0:
        print(f"  WARN: {f} 正则未匹配到进度脚本块")
        fail += 1
        continue

    # 同时确保while loop里有_saveRoundProgress钩子
    OLD_LOOP_END = """        // 每轮结束后等待2秒
        if (isPlaying && currentLoop < maxLoops) {
            await sleep(2000);
        }
    }"""
    NEW_LOOP_END = """        // 每轮结束 - 立即保存累计轮数
        if (typeof _saveRoundProgress === 'function') {
            _saveRoundProgress(currentLoop);
        }
        // 每轮结束后等待2秒
        if (isPlaying && currentLoop < maxLoops) {
            await sleep(2000);
        }
    }"""
    if OLD_LOOP_END in new_c:
        new_c = new_c.replace(OLD_LOOP_END, NEW_LOOP_END)

    with open(f, 'w', encoding='utf-8') as fh:
        fh.write(new_c)
    ok += 1

print(f"HTML: 更新{ok}个, 跳过{skip}个, 失败{fail}个, 共{len(files)}个")
