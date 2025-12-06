#!/usr/bin/env python3
"""Verify the syntax fixes work by attempting import"""

import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    print("Attempting to import flow_engine_service module...")

    # Try to compile the module
    with open('app/services/flow_engine_service.py', 'r', encoding='utf-8') as f:
        source_code = f.read()

    # Compile check
    compile(source_code, 'flow_engine_service.py', 'exec')
    print("✅ Module compiles successfully!")

    # Try to import (this will also check for import dependencies)
    try:
        from services import flow_engine_service
        print("✅ Module imports successfully!")
        print(f"✅ FlowEngineService class exists: {hasattr(flow_engine_service, 'FlowEngineService')}")
    except ImportError as e:
        print(f"⚠️  Import dependency issue (but syntax is OK): {e}")
    except Exception as e:
        print(f"⚠️  Runtime issue (but syntax is OK): {e}")

    print("\n🎉 VERIFICATION COMPLETE: All syntax errors have been fixed!")

except SyntaxError as e:
    print(f"❌ SYNTAX ERROR STILL EXISTS:")
    print(f"   Line {e.lineno}: {e.msg}")
    if e.text:
        print(f"   Code: {e.text.strip()}")
    sys.exit(1)

except Exception as e:
    print(f"❌ OTHER ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)