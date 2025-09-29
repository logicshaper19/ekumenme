"""
Test runner for all optimization services.

Run all tests with:
    python tests/run_optimization_tests.py

Run specific test file:
    pytest tests/test_unified_router_service.py -v

Run with coverage:
    pytest tests/ --cov=app/services --cov-report=html
"""

import pytest
import sys


def run_all_tests():
    """Run all optimization service tests"""
    
    test_files = [
        "tests/test_unified_router_service.py",
        "tests/test_parallel_executor_service.py",
        "tests/test_smart_tool_selector_service.py",
    ]
    
    print("=" * 80)
    print("RUNNING OPTIMIZATION SERVICE TESTS")
    print("=" * 80)
    
    # Run tests with verbose output
    args = [
        "-v",  # Verbose
        "--tb=short",  # Short traceback
        "--color=yes",  # Colored output
        *test_files
    ]
    
    exit_code = pytest.main(args)
    
    print("\n" + "=" * 80)
    if exit_code == 0:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 80)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(run_all_tests())

