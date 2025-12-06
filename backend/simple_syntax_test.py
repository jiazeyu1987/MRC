#!/usr/bin/env python3
"""Simple syntax test"""

try:
    with open('app/services/flow_engine_service.py', 'r', encoding='utf-8') as f:
        source = f.read()

    # Parse the source code
    compile(source, 'app/services/flow_engine_service.py', 'exec')

    print("✅ SUCCESS: No syntax errors found!")

except SyntaxError as e:
    print(f"❌ SYNTAX ERROR:")
    print(f"   File: {e.filename}")
    print(f"   Line: {e.lineno}")
    print(f"   Error: {e.msg}")
    if e.text:
        print(f"   Code: {e.text.strip()}")
        if e.offset:
            pointer = ' ' * (e.offset - 1) + '^'
            print(f"         {pointer}")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()