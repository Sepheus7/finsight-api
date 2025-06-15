#!/usr/bin/env python3
"""
FinSight Test Runner
Executes all main tests in the correct order
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

def run_test(test_file, description):
    """Run a single test file and report results"""
    print(f"\n{'='*60}")
    print(f"🧪 Running: {description}")
    print(f"📁 File: {test_file}")
    print('='*60)
    
    start_time = time.time()
    
    try:
        result = subprocess.run([
            sys.executable, test_file
        ], capture_output=True, text=True, cwd=project_root)
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ PASSED ({duration:.2f}s)")
            if result.stdout:
                print("📋 Output:")
                print(result.stdout)
        else:
            print(f"❌ FAILED ({duration:.2f}s)")
            print("📋 Error Output:")
            print(result.stderr)
            if result.stdout:
                print("📋 Standard Output:")
                print(result.stdout)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 FinSight Test Suite")
    print("=" * 60)
    
    # Define tests in order of execution
    tests = [
        {
            'file': 'tests/validate_system.py',
            'description': 'System Validation - Basic component checks'
        },
        {
            'file': 'tests/test_rag_foundation_validation.py', 
            'description': 'RAG Foundation - Core functionality validation'
        },
        {
            'file': 'tests/demo_rag_performance.py',
            'description': 'Performance Demo - RAG vs Regular Chat comparison'
        },
        {
            'file': 'tests/test_integration.py',
            'description': 'Integration Tests - End-to-end functionality'
        }
    ]
    
    results = []
    total_start = time.time()
    
    for test in tests:
        test_file = project_root / test['file']
        if test_file.exists():
            success = run_test(str(test_file), test['description'])
            results.append({
                'name': test['description'],
                'file': test['file'],
                'success': success
            })
        else:
            print(f"\n⚠️  SKIPPED: {test['description']}")
            print(f"   File not found: {test['file']}")
            results.append({
                'name': test['description'],
                'file': test['file'],
                'success': None
            })
    
    # Summary
    total_duration = time.time() - total_start
    passed = sum(1 for r in results if r['success'] is True)
    failed = sum(1 for r in results if r['success'] is False)
    skipped = sum(1 for r in results if r['success'] is None)
    
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print('='*60)
    print(f"⏱️  Total Time: {total_duration:.2f}s")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Skipped: {skipped}")
    print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%" if (passed+failed) > 0 else "N/A")
    
    print(f"\n📋 Detailed Results:")
    for result in results:
        status = "✅ PASS" if result['success'] is True else "❌ FAIL" if result['success'] is False else "⚠️  SKIP"
        print(f"  {status} - {result['name']}")
    
    if failed > 0:
        print(f"\n❌ {failed} test(s) failed. Check the output above for details.")
        return 1
    elif passed == 0:
        print(f"\n⚠️  No tests were successfully executed.")
        return 1
    else:
        print(f"\n🎉 All {passed} test(s) passed successfully!")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 