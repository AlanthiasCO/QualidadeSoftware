param(
    [string]$Config = "configs/novo_sgp.yml",
    [string]$Output = "outputs"
)

python .\run_with_progress.py --config $Config --output $Output
