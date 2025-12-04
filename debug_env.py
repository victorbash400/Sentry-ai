import sys
import os
import site

print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")
print(f"Sys Path: {sys.path}")
print(f"CWD: {os.getcwd()}")
print(f"Site Packages: {site.getsitepackages()}")

try:
    import perplexityai
    print(f"SUCCESS: Imported perplexityai from {perplexityai.__file__}")
except ImportError:
    print("FAILURE: Could not import perplexityai")

try:
    import perplexity
    print(f"SUCCESS: Imported perplexity from {perplexity.__file__}")
except ImportError:
    print("FAILURE: Could not import perplexity")
