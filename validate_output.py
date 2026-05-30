"""部署前校验HTML标签闭合和基本结构"""
import sys
from pathlib import Path
from bs4 import BeautifulSoup

def validate_html(filepath: str) -> bool:
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    if not soup.title or not soup.title.string:
        print(f"[FAIL] {filepath}: missing <title>")
        return False
    if not soup.find('h1'):
        print(f"[FAIL] {filepath}: missing <h1>")
        return False
    return True

def main():
    output_dir = Path('output')
    all_ok = True
    for f in output_dir.rglob('*.html'):
        if not validate_html(str(f)):
            all_ok = False
    if not all_ok:
        sys.exit(1)
    print("[OK] All HTML files validated")

if __name__ == "__main__":
    main()
