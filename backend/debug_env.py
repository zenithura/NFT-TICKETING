import os
from dotenv import load_dotenv

# Try loading without path
load_dotenv()
val = os.getenv("PRIVATE_KEY")
print(f"Loaded without path. PRIVATE_KEY present: {val is not None}")
if val:
    print(f"PRIVATE_KEY length: {len(val)}")
else:
    print("PRIVATE_KEY is empty or None")

# Try loading with explicit path
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path, override=True)
val = os.getenv("PRIVATE_KEY")
print(f"Loaded with explicit path. PRIVATE_KEY present: {val is not None}")
if val:
    print(f"PRIVATE_KEY length: {len(val)}")
else:
    print("PRIVATE_KEY is empty or None")
