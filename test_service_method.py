#!/usr/bin/env python3
"""Simple test to verify SquadsService.get_all_members() works."""

import sys
import os
import tempfile

# Setup test database
temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
temp_db.close()
os.environ['DATABASE_URL'] = f'sqlite:///{temp_db.name}'

try:
    from infra.database import Member, session_scope
    from services.squads_service import SquadsService
    
    print("Testing SquadsService.get_all_members()...")
    print()
    
    # Create test members
    with session_scope() as session:
        members = [
            Member(name="Alice", status=True),
            Member(name="Bob", status=True),
            Member(name="Charlie", status=True),
        ]
        session.add_all(members)
        session.flush()
        print(f"✓ Created {len(members)} test members")
    
    # Test the new method
    service = SquadsService()
    result = service.get_all_members()
    
    print(f"✓ get_all_members() returned {len(result)} members")
    
    # Verify structure
    for i, member in enumerate(result, 1):
        assert 'id' in member, f"Member {i} missing 'id'"
        assert 'name' in member, f"Member {i} missing 'name'"
        print(f"  {i}. {member['name']} (id={member['id'][:8]}...)")
    
    # Verify ordering
    names = [m['name'] for m in result]
    expected_order = ["Alice", "Bob", "Charlie"]
    assert names == expected_order, f"Expected {expected_order}, got {names}"
    
    print()
    print("✓ Members are ordered alphabetically")
    print()
    print("=" * 60)
    print("✓ ALL CHECKS PASSED!")
    print("=" * 60)
    
    # Cleanup
    os.unlink(temp_db.name)
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
