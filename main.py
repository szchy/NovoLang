import sys
import os
import json

# Add python directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'python'))

from lexer import Lexer
from parser import Parser
from py_executor import PyExecutor

# Try to import the C++ backend
try:
    import novolang_core
    HAS_CPP = True
except ImportError:
    HAS_CPP = False
    # print("Warning: 'novolang_core' module not found. C++ backend is not available.")
    # print("Please compile the extension using 'python setup.py build_ext --inplace'")

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <file.nl>")
        return

    filename = sys.argv[1]
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found.")
        return

    with open(filename, 'r', encoding='utf-8') as f:
        code = f.read()

    print(f"Running {filename}...")
    
    # 1. Lexer
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    # print("Tokens:", tokens)
    
    # 2. Parser
    parser = Parser(tokens)
    ast = parser.parse()
    
    # 3. Execution
    if HAS_CPP:
        print("Executing with C++ backend...")
        try:
            executor = novolang_core.ASTExecutor()
            executor.execute(ast)
        except Exception as e:
            print(f"Execution Error: {e}")
    else:
        print("Executing with Python backend (C++ extension not found)...")
        try:
            executor = PyExecutor()
            executor.execute(ast)
        except Exception as e:
            print(f"Execution Error: {e}")

if __name__ == "__main__":
    main()
