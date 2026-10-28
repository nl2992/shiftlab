"""Static import-isolation check for external adapters (P4 section 1)."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ALLOWED_THIRD_PARTY = frozenset({"numpy", "scipy"})
CONTRACT_PACKAGE = "shiftlab.contract"
# External adapters may use the interface only, never the evaluator-side or baseline modules.
FORBIDDEN_CONTRACT_MODULES = frozenset({"harness", "baselines", "isolation"})
DYNAMIC_IMPORT_NAMES = frozenset({"__import__", "import_module"})


def _top_level(name: str) -> str:
    return name.split(".", 1)[0]


def _module_violation(module: str) -> str | None:
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
