$ErrorActionPreference = "Stop"

Write-Host "Validacao automatica da pipeline de hotspots" -ForegroundColor Cyan
Write-Host "Projeto padrao: SAPL" -ForegroundColor DarkGray

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "ERRO: .venv nao encontrado. Execute este script na raiz do projeto, com o ambiente criado." -ForegroundColor Red
    exit 1
}

& .\.venv\Scripts\python.exe .\validate_pipeline.py --project sapl
if ($LASTEXITCODE -ne 0) {
    Write-Host "A validacao terminou com erro." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "" 
Write-Host "Resumo:" -ForegroundColor Green
Get-Content .\validation\sapl\validation_summary.txt
