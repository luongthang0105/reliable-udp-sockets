import sys
import os

if len(sys.argv) < 2:
    print("Usage: python run.py <sender|receiver> <args>")
    sys.exit(1)

role = sys.argv[1]
args = " ".join(sys.argv[2:])

script_path = os.path.join(os.path.dirname(__file__), 'src', role, f"{role}.py")
if not os.path.exists(script_path):
    print(f"Error: {role}.py not found in src/{role}/")
    sys.exit(1)

os.system(f"python -m src.{role}.{role} {args}")