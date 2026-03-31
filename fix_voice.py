# -*- coding: utf-8 -*-
"""
修改所有HTML文件的语音选择逻辑，优先使用男性语音
"""

import os
import re

work_dir = r"C:\Users\Lenovo\WorkBuddy\daily-words-1000"

html_files = [f for f in os.listdir(work_dir) if f.endswith('.html') and f.startswith('20')]
html_files.sort()

print(f"找到 {len(html_files)} 个HTML文件")

for filename in html_files:
    filepath = os.path.join(work_dir, filename)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经修改过
    if 'Microsoft David' in content:
        continue
    
    # 替换语音选择逻辑
    content = re.sub(
        r"// 选择语音\n\s*if \(lang === 'en-US'\) \{\n\s*const voice = allVoices\.find\(v => v\.lang\.startsWith\('en'\)\) \|\| allVoices\[0\];\n\s*if \(voice\) utterance\.voice = voice;\n\s*\} else if \(lang === 'zh-CN'\) \{\n\s*const voice = allVoices\.find\(v => v\.lang\.startsWith\('zh'\)\) \|\| allVoices\[0\];\n\s*if \(voice\) utterance\.voice = voice;\n\s*\}",
        "// 选择语音 - 优先选择男性英语语音\n        if (lang === 'en-US') {\n            // 优先级：Microsoft David > Google US English Male > 其他男性 > 任意英语\n            let voice = allVoices.find(v => v.name.includes('David') && v.lang.startsWith('en'));\n            if (!voice) voice = allVoices.find(v => v.name.includes('Male') && v.lang.startsWith('en'));\n            if (!voice) voice = allVoices.find(v => v.lang.startsWith('en'));\n            if (voice) utterance.voice = voice;\n        } else if (lang === 'zh-CN') {\n            const voice = allVoices.find(v => v.lang.startsWith('zh')) || allVoices[0];\n            if (voice) utterance.voice = voice;\n        }",
        content
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    if (len([f for f in html_files if f == filename])) % 100 == 0:
        idx = html_files.index(filename) + 1
        print(f"已处理 {idx} 个文件...")

print(f"完成！共修改 {len(html_files)} 个文件")
