from __future__ import annotations

from pathlib import PurePosixPath
import re

from .config import ProjectConfig
from .utils import is_excluded

# Pascal/camel-case test indicators common in Java/C# repositories.
_CAMEL_TEST_RE = re.compile(r"(?:Test|Tests|Teste|Testes)(?:[A-Z0-9_]|$)")
_SPECIAL_TEST_FILES = {"conftest.py", "testutils.py", "test_utils.py", "setuptests.js", "setuptests.ts", "setuptests.jsx", "setuptests.tsx"}
_PREFIX_TEST_RE = re.compile(r"^(?:test|teste)(?:_|[A-Z0-9])")


def include_path(path: str, cfg: ProjectConfig) -> bool:
    norm = path.replace("\\", "/").lstrip("./")
    pp = PurePosixPath(norm)
    if cfg.extensions and not any(norm.lower().endswith(ext.lower()) for ext in cfg.extensions):
        return False
    if is_excluded(norm, cfg.exclude_paths):
        return False

    parts_raw = list(pp.parts)
    parts = [p.lower() for p in parts_raw]
    stem_raw = pp.stem
    stem = stem_raw.lower()
    name = pp.name.lower()

    if cfg.exclude_tests:
        markers = {m.lower() for m in cfg.test_markers}
        # Directory/package markers and exact test filenames/stems.
        if any(p in markers for p in parts):
            return False
        if stem in markers or name in _SPECIAL_TEST_FILES:
            return False
        # Conventional Python/Ruby/etc. test naming.
        if stem.startswith(("test_", "teste_")) or stem.endswith(("_test", "_tests", "_teste", "_testes", ".spec", ".test")):
            return False
        if _PREFIX_TEST_RE.search(stem_raw):
            return False
        # Conventional Java/C# class names (FooTest, FooTeste, MassaTesteDJE, ...).
        if _CAMEL_TEST_RE.search(stem_raw):
            return False

    if cfg.exclude_migrations:
        if any(p in {"migration", "migrations"} for p in parts):
            return False

    return True
