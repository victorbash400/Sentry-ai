"""
Test Runner Script
Quick commands to run different test suites
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and print results"""
    print(f"\n{'=' * 60}")
    print(f"{description}")
    print(f"{'=' * 60}")
    print(f"Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode


def main():
    """Run test suites based on command line arguments"""
    
    if len(sys.argv) < 2:
        print("Sentry Test Runner")
        print("\nUsage: python run_tests.py [command]")
        print("\nCommands:")
        print("  all          - Run all tests")
        print("  data         - Test data generator")
        print("  trainer      - Test model trainer")
        print("  extractor    - Test feature extractor")
        print("  model        - Test risk model")
        print("  gee          - Test Google Earth Engine")
        print("  integration  - Test full pipeline")
        print("  coverage     - Run all tests with coverage report")
        print("  fast         - Run fast tests only (skip slow)")
        print("  verbose      - Run all tests with verbose output")
        return 1
    
    command = sys.argv[1].lower()
    
    # Test commands mapping
    commands = {
        'all': (
            ['pytest', 'tests/', '-v'],
            "Running All Tests"
        ),
        'data': (
            ['pytest', 'tests/test_data_generator.py', '-v'],
            "Testing Synthetic Data Generator"
        ),
        'trainer': (
            ['pytest', 'tests/test_model_trainer.py', '-v'],
            "Testing Model Trainer"
        ),
        'extractor': (
            ['pytest', 'tests/test_feature_extractor.py', '-v'],
            "Testing Feature Extractor"
        ),
        'model': (
            ['pytest', 'tests/test_risk_model.py', '-v'],
            "Testing Risk Model"
        ),
        'gee': (
            ['pytest', 'tests/test_gee_satellite.py', '-v'],
            "Testing Google Earth Engine Integration"
        ),
        'integration': (
            ['pytest', 'tests/test_integration.py', '-v'],
            "Testing Full Pipeline Integration"
        ),
        'coverage': (
            ['pytest', 'tests/', '--cov=.', '--cov-report=html', '--cov-report=term'],
            "Running Tests with Coverage Report"
        ),
        'fast': (
            ['pytest', 'tests/', '-v', '-m', 'not slow'],
            "Running Fast Tests Only"
        ),
        'verbose': (
            ['pytest', 'tests/', '-vv', '-s'],
            "Running All Tests (Verbose)"
        ),
    }
    
    if command not in commands:
        print(f"ERROR: Unknown command '{command}'")
        print("Run 'python run_tests.py' to see available commands")
        return 1
    
    cmd, description = commands[command]
    return_code = run_command(cmd, description)
    
    if command == 'coverage':
        print("\nCoverage report generated in: htmlcov/index.html")
    
    return return_code


if __name__ == '__main__':
    sys.exit(main())
