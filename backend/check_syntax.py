#!/usr/bin/env python3
"""Syntax checker for flow_engine_service.py"""

import sys

def check_syntax(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()

        # Try to compile
        compile(content, filename, 'exec')
        print("✅ No syntax errors found!")
        return True

    except SyntaxError as e:
        print(f"❌ Syntax Error:")
        print(f"   File: {e.filename}")
        print(f"   Line: {e.lineno}")
        print(f"   Text: {e.text.strip() if e.text else 'Unknown'}")
        print(f"   Error: {e.msg}")

        # Show some context
        if e.text and e.lineno:
            lines = content.split('\n')
            start = max(0, e.lineno - 3)
            end = min(len(lines), e.lineno + 2)
            print(f"\n   Context (lines {start+1}-{end}):")
            for i in range(start, end):
                marker = " >>> " if i == e.lineno - 1 else "     "
                print(f"   {marker}{i+1:4d}: {lines[i]}")

        return False
    except Exception as e:
        print(f"❌ Other error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_syntax.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    success = check_syntax(filename)
    sys.exit(0 if success else 1)