import importlib.util
from pathlib import Path

import pandas as pd


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "validate_pipeline.py"
SPEC = importlib.util.spec_from_file_location("validate_pipeline", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
validation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validation)


def command_paths(command):
    separator = command.index("--")
    return command[separator + 1 :]


def test_file_without_aliases_queries_only_current_path(monkeypatch):
    identity = pd.DataFrame(
        [{"file_id": "current-id", "path": "src/current.cs"}]
    )
    aliases = validation.identity_aliases(identity, "current-id", "src/current.cs")
    captured = {}

    def fake_git(repo, *args, **kwargs):
        captured["args"] = list(args)
        return "@@COMMIT@@abc\n8\t0\tsrc/current.cs"

    monkeypatch.setattr(validation, "git", fake_git)
    result = validation.recompute_git_metrics(
        Path("repo"), aliases, "2023-01-01", "2023-12-31", "freeze"
    )

    assert aliases == ["src/current.cs"]
    assert "--full-history" in captured["args"]
    assert "--follow" not in captured["args"]
    assert command_paths(captured["args"]) == ["src/current.cs"]
    assert result == (1, 8, 0, 8)


def test_legitimate_rename_queries_both_approved_aliases(monkeypatch):
    identity = pd.DataFrame(
        [
            {"file_id": "same-id", "path": "src/new.cs"},
            {"file_id": "same-id", "path": "src/old.cs"},
        ]
    )
    aliases = validation.identity_aliases(identity, "same-id", "src/new.cs")
    captured = {}

    def fake_git(repo, *args, **kwargs):
        captured["args"] = list(args)
        return ""

    monkeypatch.setattr(validation, "git", fake_git)
    validation.recompute_git_metrics(
        Path("repo"), aliases, "2023-01-01", "2023-12-31", "freeze"
    )

    assert aliases == ["src/new.cs", "src/old.cs"]
    assert command_paths(captured["args"]) == ["src/new.cs", "src/old.cs"]


def test_false_rename_chain_is_not_traversed(monkeypatch):
    current = "src/ILimpezaRegistroFrequenciaAlunoDuplicadoUseCase.cs"
    false_chain = [
        "src/IRegistrarMetricaAcessosSGPUseCase.cs",
        "src/IAcessosDiarioSGPUseCase.cs",
        "src/ILimpezaConselhoClasseDuplicadoUseCase.cs",
        "src/IConselhoClasseAlunoUeDuplicadoUseCase.cs",
    ]
    identity = pd.DataFrame(
        [{"file_id": "current-id", "path": current}]
        + [
            {"file_id": f"other-{index}", "path": path}
            for index, path in enumerate(false_chain)
        ]
    )
    captured = {}

    def fake_git(repo, *args, **kwargs):
        captured["args"] = list(args)
        return "@@COMMIT@@abc\n8\t0\t" + current

    monkeypatch.setattr(validation, "git", fake_git)
    aliases = validation.identity_aliases(identity, "current-id", current)
    result = validation.recompute_git_metrics(
        Path("repo"), aliases, "2023-01-01", "2023-12-31", "freeze"
    )

    assert command_paths(captured["args"]) == [current]
    assert not set(false_chain) & set(captured["args"])
    assert result == (1, 8, 0, 8)


def test_alias_query_is_sorted_and_deduplicated(monkeypatch):
    calls = []

    def fake_git(repo, *args, **kwargs):
        calls.append(list(args))
        return ""

    monkeypatch.setattr(validation, "git", fake_git)
    aliases = ["src/z.cs", "src/a.cs", "src/z.cs", "src/m.cs"]
    validation.recompute_git_metrics(
        Path("repo"), aliases, "2023-01-01", "2023-12-31", "freeze"
    )
    validation.recompute_git_metrics(
        Path("repo"), list(reversed(aliases)), "2023-01-01", "2023-12-31", "freeze"
    )

    assert command_paths(calls[0]) == ["src/a.cs", "src/m.cs", "src/z.cs"]
    assert calls[0] == calls[1]


def test_commit_is_counted_once_when_multiple_aliases_change(monkeypatch):
    output = "\n".join(
        [
            "@@COMMIT@@same-hash",
            "3\t1\tsrc/old.cs",
            "5\t2\tsrc/new.cs",
            "@@COMMIT@@same-hash",
        ]
    )
    monkeypatch.setattr(validation, "git", lambda *args, **kwargs: output)

    result = validation.recompute_git_metrics(
        Path("repo"),
        ["src/old.cs", "src/new.cs"],
        "2023-01-01",
        "2023-12-31",
        "freeze",
    )

    assert result == (1, 8, 3, 11)


def test_commit_without_numeric_numstat_does_not_increment_nmod():
    output = "\n".join(
        [
            "@@COMMIT@@without-numstat",
            "",
            "@@COMMIT@@binary-only",
            "-\t-\tassets/file.bin",
            "@@COMMIT@@with-numstat",
            "2\t1\tsrc/file.cs",
        ]
    )

    assert validation.parse_git_log_numstat(output) == (1, 2, 1)


def test_multiple_numstat_lines_count_the_commit_only_once():
    output = "\n".join(
        [
            "@@COMMIT@@same-commit",
            "3\t1\tsrc/old.cs",
            "5\t2\tsrc/new.cs",
        ]
    )

    assert validation.parse_git_log_numstat(output) == (1, 8, 3)
