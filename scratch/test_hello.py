import sys
print("Python executable:", sys.executable)
print("Python path:", sys.path)
try:
    import openai
    print("openai package is installed!")
except ImportError:
    print("openai package is NOT installed")
