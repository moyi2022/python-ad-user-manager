import sys
import os

# 强制设置 UTF-8 编码
os.environ['PYTHONIOENCODING'] = 'utf-8'
if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass
if sys.stderr:
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass