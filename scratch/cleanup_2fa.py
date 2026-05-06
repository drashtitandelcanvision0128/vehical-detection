
import re

with open('web_test_app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False

# Patterns that start a 2FA section
start_patterns = [
    r"@app\.route\('/api/2fa/",
    r"@app\.route\('/2fa_",
    r"TWO_FACTOR_VERIFY_TEMPLATE =",
    r"TWO_FACTOR_SETTINGS_TEMPLATE =",
    r"# ===== Two-Factor Authentication \(2FA\) Routes ====="
]

# Next section markers to stop skipping
stop_patterns = [
    r"# Multi-Camera Detection Page Template",
    r"MULTI_CAMERA_TEMPLATE =",
    r"@app\.route\('/live_detection'\)",
    r"@app\.route\('/multi_camera'\)"
]

current_skip_count = 0
for line in lines:
    if not skip:
        for p in start_patterns:
            if re.search(p, line):
                skip = True
                print(f"Starting skip at: {line.strip()}")
                break
        if not skip:
            new_lines.append(line)
    else:
        for p in stop_patterns:
            if re.search(p, line):
                skip = False
                new_lines.append(line)
                print(f"Stopped skip at: {line.strip()}")
                break

with open('web_test_app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Cleanup complete.")
