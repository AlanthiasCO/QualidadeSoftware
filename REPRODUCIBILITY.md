# Reproducibility guide

## Scientific status

This repository preserves a paper-faithful consolidation of pipeline v1.4.3. It is not yet a complete replication package because the completed contextual-coding records and the final 20-pair static-analysis dataset were not found in version control.

The authoritative status of each result is recorded in `results/paper_final/value_registry.csv`:

- `verified_from_code`: implementation is present and tested;
- `verified_from_versioned_data`: value can be checked against versioned data;
- `declared_in_paper`: value is reported by the manuscript but its final source dataset is unavailable;
- `known_mismatch`: an older artifact exists but does not represent the final corpus.

## Final corpus

- Novo SGP: 2020–2026
- SAPL: 2020–2026
- SIGA: 2020–2025
- SIGI: 2020–2026
- VLibras Web Browsers: 2020–2026

Painel e-SUS APS belongs to the historical corpus and must not be included in final-paper aggregations.

## Local validation

Python 3.11 or newer is required.

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest -q
python scripts/verify_paper_final.py
python scripts/verify_paper_final_checksums.py
```

The first verifier validates the five-system scope, RQ2 medians and the structure of the 25 matched pairs. It also confirms that the contextual sheets remain unfilled and therefore prevents an accidental claim of full reproduction.

## Quantitative pipeline

The original per-project execution is documented by the configuration files, `scripts/run_project_validated.sh`, `scripts/validate_pipeline.py` and the validation records under `results/validation/v1.4.3/`.

A complete clean rerun additionally requires cloning the five external repositories at their recorded freeze SHAs. That expensive network-dependent execution was not performed while preparing this branch.

## Known gaps

1. Completed reviewer sheets supporting 7/25 priority files and 3/25 controls are absent.
2. The final static-analysis dataset supporting 5/10/5 over 20 classified pairs is absent.
3. The old static dataset represents Painel e-SUS and reports 9/11/5; it is historical, not final evidence.
4. The historical C# build failure must not be interpreted as proof of zero findings.
5. File counts for Novo SGP and SIGA, and the reported VLibras `Plugin.js` score, require reconciliation.

Until these gaps are resolved, use the wording “paper-faithful consolidation with partial verification,” not “full reproduction.”
