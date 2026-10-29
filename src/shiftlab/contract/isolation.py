"""Static import lint for external adapters (P4 section 1).

This is only a lint. It cannot establish isolation (allowed stdlib modules can still reach files
or process state); isolation comes from ``sandbox.py`` plus the procedural packet rule.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

# ``interface`` is the standalone copy of interface.py shipped in the sandbox packet.
ALLOWED_THIRD_PARTY = frozenset({"numpy", "scipy", "interface"})
CONTRACT_PACKAGE = "shiftlab.contract"
# External adapters may use the interface only, never the evaluator-side or baseline modules.
FORBIDDEN_CONTRACT_MODULES = frozenset({"harness", "baselines", "isolation"})
DYNAMIC_IMPORT_NAMES = frozenset({"__import__", "import_module"})
# Standard-library modules that give introspection or native-code access.
FORBIDDEN_STDLIB = frozenset({"gc", "inspect", "ctypes", "_ctypes", "cffi", "_cffi_backend"})
# Attributes / names / string literals used to reach frames, closures, globals or builtins.
FORBIDDEN_NAMES = frozenset(
    {
        "_getframe",
        "_current_frames",
        "__closure__",
        "cell_contents",
        "__code__",
        "__globals__",
        "__defaults__",
        "__kwdefaults__",
        "__subclasses__",
        "__builtins__",
        "f_back",
        "f_globals",
        "f_locals",
        "f_builtins",
        "tb_frame",
        "get_objects",
        "get_referrers",
        "get_referents",
        "gc",
        "inspect",
    }
)


def _top_level(name: str) -> str:
    return name.split(".", 1)[0]


def _module_violation(module: str) -> str | None:
    if _top_level(module) in FORBIDDEN_STDLIB:
        return f"forbidden introspection/native module {module}"
    if _top_level(module) in sys.stdlib_module_names or _top_level(module) in ALLOWED_THIRD_PARTY:
        return None
    if module == CONTRACT_PACKAGE:
        return None
    if module.startswith(CONTRACT_PACKAGE + "."):
        sub = module[len(CONTRACT_PACKAGE) + 1 :].split(".", 1)[0]
        if sub in FORBIDDEN_CONTRACT_MODULES:
            return f"forbidden contract module {module}"
        return None
    return f"disallowed import {module}"


def check_source(source: str, filename: str = "<adapter>") -> list[str]:
    """Return violation messages for the imports in ``source`` (empty means compliant)."""
    tree = ast.parse(source, filename=filename)
    violations: list[str] = []
    for node in ast.walk(tree):
        line = getattr(node, "lineno", 0)
        if isinstance(node, ast.Import):
            for alias in node.names:
                if (message := _module_violation(alias.name)) is not None:
                    violations.append(f"{filename}:{line}: {message}")
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                violations.append(f"{filename}:{line}: relative import is not allowed")
                continue
            module = node.module or ""
            if (message := _module_violation(module)) is not None:
                violations.append(f"{filename}:{line}: {message}")
            elif module == CONTRACT_PACKAGE:
                for alias in node.names:
                    if alias.name in FORBIDDEN_CONTRACT_MODULES:
                        violations.append(
                            f"{filename}:{line}: forbidden contract module {alias.name}"
                        )
        elif isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_NAMES:
            violations.append(f"{filename}:{line}: forbidden attribute .{node.attr}")
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            violations.append(f"{filename}:{line}: forbidden name {node.id}")
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value in FORBIDDEN_NAMES
        ):
            violations.append(f"{filename}:{line}: forbidden name string {node.value!r}")
        elif isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
            if name in DYNAMIC_IMPORT_NAMES:
                violations.append(f"{filename}:{line}: dynamic import via {name}")
    return violations


def check_imports(path: str | Path) -> list[str]:
    """Parse a module file and return import violations against the allowlist.

    Allowed: standard library, numpy, scipy, and ``shiftlab.contract`` (interface only;
    ``harness`` and ``baselines`` are excluded). Relative imports and dynamic imports are flagged.
    """
    file = Path(path)
    return check_source(file.read_text(encoding="utf-8"), filename=str(file))
