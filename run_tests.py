#!/usr/bin/env python3
"""
Test runner script for the jukebox label generator
"""

import subprocess
import sys
from pathlib import Path

def run_pytest(test_path, description):
    """Run pytest for a specific test path and return results."""
    print(f"\n{'='*60}")
    print(f"Running {description}")
    print('='*60)
    
    try:
        result = subprocess.run([
            'uv', 'run', 'pytest', test_path, '-v', '--tb=short'
        ], capture_output=False, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} - ALL TESTS PASSED")
            return True
        else:
            print(f"❌ {description} - SOME TESTS FAILED")
            return False
            
    except Exception as e:
        print(f"❌ {description} - ERROR RUNNING TESTS: {e}")
        return False

def run_test_coverage():
    """Run test coverage analysis."""
    print(f"\n{'='*60}")
    print("Running Test Coverage Analysis")
    print('='*60)
    
    try:
        subprocess.run([
            'uv', 'run', 'pytest', '--cov=.', '--cov-report=term-missing',
            'tests/', '--tb=short'
        ], check=False)
    except Exception as e:
        print(f"❌ Error running coverage: {e}")

def main():
    """Main test runner."""
    print("🎵 Jukebox Label Generator Test Suite")
    print("=====================================")
    
    # Change to project directory
    project_dir = Path(__file__).parent
    import os
    os.chdir(project_dir)
    
    test_results = []
    
    # Run individual test suites
    test_suites = [
        ("tests/test_jukebox_label.py", "JukeBox Label Tests"),
        ("tests/test_models.py", "Database Model Tests"), 
        ("tests/test_label_generator.py::TestLabelGenerator::test_default_settings_match_requirements", "Settings Tests"),
        ("tests/test_integration.py::TestPerformance::test_large_batch_label_generation", "Performance Tests")
    ]
    
    for test_path, description in test_suites:
        success = run_pytest(test_path, description)
        test_results.append((description, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for _, success in test_results if success)
    total = len(test_results)
    
    for description, success in test_results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status:<10} {description}")
    
    print(f"\nOverall: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All core functionality tests are working!")
        print("\nNext steps:")
        print("- Run full test suite with: uv run pytest")
        print("- Run with coverage: uv run pytest --cov")
        print("- Run specific tests: uv run pytest tests/test_name.py")
    else:
        print("⚠️  Some tests need attention. Check the output above.")
        
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())