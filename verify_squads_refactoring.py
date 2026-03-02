#!/usr/bin/env python3
"""Quick verification of SquadsFrame refactoring."""

import sys
import os
import tempfile

# Create test DB
temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
temp_db.close()
os.environ['DATABASE_URL'] = f'sqlite:///{temp_db.name}'

try:
    from gui.squads import SquadsFrame
    from services.squads_service import SquadsService
    import tkinter as tk
    
    print("Testing gui/squads.py refactoring...")
    print()
    
    # Check imports
    with open('gui/squads.py', 'r') as f:
        content = f.read()
    
    checks = [
        ('session_scope removed from imports', 'from infra.database import Member, session_scope' not in content),
        ('_on_select uses service.get_all_members()', 'self.service.get_all_members()' in content),
        ('No direct session_scope() calls', content.count('session_scope()') == 0),
        ('SquadsService imported', 'SquadsService' in content),
    ]
    
    for check_name, result in checks:
        status = "✓" if result else "✗"
        print(f"{status} {check_name}")
        if not result:
            sys.exit(1)
    
    # Test initialization
    root = tk.Tk()
    root.withdraw()
    
    frame = SquadsFrame(root)
    
    init_checks = [
        ('SquadsFrame has service', hasattr(frame, 'service')),
        ('service is SquadsService', isinstance(frame.service, SquadsService)),
        ('SquadsService has get_all_members', hasattr(SquadsService, 'get_all_members')),
    ]
    
    for check_name, result in init_checks:
        status = "✓" if result else "✗"
        print(f"{status} {check_name}")
        if not result:
            sys.exit(1)
    
    root.destroy()
    
    print()
    print("=" * 60)
    print("✓ REFACTORING VERIFICATION PASSED!")
    print("=" * 60)
    
    # Cleanup
    os.unlink(temp_db.name)
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
