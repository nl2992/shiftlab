import importlib.metadata
import sys

print(sys.version)
for name in ["shiftlab", "numpy", "scipy", "scikit-learn", "pydantic"]:
    print(name, importlib.metadata.version(name))
