"""
Test runner script for Vehicle Detection App
"""
import subprocess
import sys


def run_tests(args=None):
    """Run pytest with appropriate arguments"""
    if args is None:
        args = []
    
    # Default pytest arguments
    default_args = [
        'pytest',
        '-v',
        '--tb=short',
        'tests/'
    ]
    
    # Combine default and user arguments
    cmd = default_args + args
    
    print(f"Running: {' '.join(cmd)}")
    print("=" * 60)
    
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


if __name__ == '__main__':
    # Parse command line arguments
    user_args = sys.argv[1:]
    
    # Exit with pytest's exit code
    sys.exit(run_tests(user_args))
