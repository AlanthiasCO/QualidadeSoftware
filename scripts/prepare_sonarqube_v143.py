from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "results" / "final" / "v143"
DEST = ROOT / "results" / "sonarqube" / "v143"


def main() -> None:
    with (FINAL / "consolidado_rq4_pares_v143.csv").open(encoding="utf-8", newline="") as stream:
        pairs = list(csv.DictReader(stream))
    with (FINAL / "consolidado_casos_v143.csv").open(encoding="utf-8", newline="") as stream:
        cases = {row["project_id"]: row for row in csv.DictReader(stream)}
    rows: list[dict[str, object]] = []
    for pair in pairs:
        case = cases[pair["project_id"]]
        for group in ("hotspot", "control"):
            rows.append(
                {
                    "pair_id": pair["pair_id"],
                    "project_id": pair["project_id"],
                    "system_name": pair["system_name"],
                    "group": group,
                    "language": pair["language"],
                    "branch": case["branch"],
                    "freeze_sha": case["freeze_sha"],
                    "file_id": pair[f"file_id_{group}"],
                    "path": pair[f"path_{group}"],
                    "h_median": pair[f"h_median_{group}"],
                    "nloc_median": pair[f"nloc_median_{group}"],
                    "snapshots": pair[f"snapshots_{group}"],
                    "analysis_status": "pending",
                }
            )

    DEST.mkdir(parents=True, exist_ok=True)
    manifest = DEST / "input_manifest_v143.csv"
    with manifest.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    result_columns = [
        "analysis_id", "project_id", "freeze_sha", "sonarqube_project_key",
        "sonarqube_version", "scanner_version", "quality_profile", "analysis_date",
        "pair_id", "group", "path", "analysis_status", "rule_key", "rule_name",
        "issue_type", "severity", "status", "line", "effort", "message",
    ]
    with (DEST / "issues_template_v143.csv").open("w", newline="", encoding="utf-8") as stream:
        csv.writer(stream, lineterminator="\n").writerow(result_columns)

    execution_columns = [
        "project_id", "freeze_sha", "sonarqube_project_key", "sonarqube_version",
        "scanner_version", "quality_profile", "analysis_date", "analysis_status",
        "files_expected", "files_found", "issues_export_file", "notes",
    ]
    with (DEST / "execution_log_template_v143.csv").open("w", newline="", encoding="utf-8") as stream:
        csv.writer(stream, lineterminator="\n").writerow(execution_columns)

    print(f"prepared {len(rows)} files in {DEST}")


if __name__ == "__main__":
    main()
