param(
    [string]$OutputsDir = "outputs_v14",
    [string]$FreezeDir = "freeze_quantitativo_v1.4.1"
)

$ErrorActionPreference = "Stop"

Write-Host "==============================================="
Write-Host " CONGELAMENTO DA ETAPA QUANTITATIVA v1.4.1"
Write-Host "==============================================="
Write-Host ""

$root = (Get-Location).Path
$freezePath = Join-Path $root $FreezeDir
$metadataDir = Join-Path $freezePath "metadata"
$configsDir = Join-Path $freezePath "configs"
$pipelineDir = Join-Path $freezePath "pipeline"
$outputsDest = Join-Path $freezePath "outputs_v14_raw"

New-Item -ItemType Directory -Force -Path $freezePath | Out-Null
New-Item -ItemType Directory -Force -Path $metadataDir | Out-Null
New-Item -ItemType Directory -Force -Path $configsDir | Out-Null
New-Item -ItemType Directory -Force -Path $pipelineDir | Out-Null

Write-Host "[1/6] Registrando ambiente..."
$envFile = Join-Path $metadataDir "environment_versions.txt"
"Congelamento quantitativo v1.4.1" | Out-File $envFile -Encoding utf8
"Data: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')" | Out-File $envFile -Append -Encoding utf8
"Diretorio raiz: $root" | Out-File $envFile -Append -Encoding utf8
"" | Out-File $envFile -Append -Encoding utf8

try { "Python: $(python --version 2>&1)" | Out-File $envFile -Append -Encoding utf8 } catch { "Python: NAO IDENTIFICADO" | Out-File $envFile -Append -Encoding utf8 }
try { "Git: $(git --version 2>&1)" | Out-File $envFile -Append -Encoding utf8 } catch { "Git: NAO IDENTIFICADO" | Out-File $envFile -Append -Encoding utf8 }

$packages = @("pydriller","lizard","pandas","numpy","scipy","PyYAML","matplotlib","pytest")
foreach ($pkg in $packages) {
    try {
        $v = python -c "import importlib.metadata as m; print(m.version('$pkg'))" 2>$null
        "${pkg}: $v" | Out-File $envFile -Append -Encoding utf8
    }
    catch {
        "${pkg}: NAO IDENTIFICADO" | Out-File $envFile -Append -Encoding utf8
    }
}

try {
    python -m pip freeze | Out-File (Join-Path $metadataDir "pip_freeze.txt") -Encoding utf8
} catch {
    "Nao foi possivel executar pip freeze." | Out-File (Join-Path $metadataDir "pip_freeze.txt") -Encoding utf8
}

Write-Host "[2/6] Copiando configuracoes e pipeline..."
if (Test-Path ".\configs") {
    Copy-Item ".\configs\*" $configsDir -Recurse -Force
}
if (Test-Path ".\src") {
    Copy-Item ".\src" $pipelineDir -Recurse -Force
}
foreach ($f in @("pyproject.toml","requirements.txt","README.md","validate_pipeline.py","run_with_progress.py","compare_outputs.py")) {
    if (Test-Path ".\$f") {
        Copy-Item ".\$f" $pipelineDir -Force
    }
}

Write-Host "[3/6] Copiando outputs brutos..."
if (-not (Test-Path ".\$OutputsDir")) {
    throw "Pasta de outputs nao encontrada: $OutputsDir"
}
if (Test-Path $outputsDest) {
    Remove-Item $outputsDest -Recurse -Force
}
Copy-Item ".\$OutputsDir" $outputsDest -Recurse -Force

Write-Host "[4/6] Copiando artefatos finais..."
$finalArtifacts = @(
    "resultados_corrigidos_v141.zip",
    "consolidacao_final_resultados_v141.xlsx",
    "relatorio_final_v141.md",
    "figuras_finais_v141.zip",
    "ajustes-pipeline-v1.4.1.zip",
    "FECHAMENTO_ETAPA_QUANTITATIVA_v1.4.1.md"
)
foreach ($f in $finalArtifacts) {
    if (Test-Path ".\$f") {
        Copy-Item ".\$f" $freezePath -Force
    }
}

Write-Host "[5/6] Gerando manifesto dos cinco casos..."
$manifestPath = Join-Path $metadataDir "freeze_manifest.csv"
$rows = @()
$projects = @("novo_sgp","sapl","siga","sigi","painel_esus")
foreach ($p in $projects) {
    $audit = Join-Path (Join-Path ".\$OutputsDir" $p) "00_audit.csv"
    if (Test-Path $audit) {
        $data = Import-Csv $audit
        foreach ($r in $data) {
            $rows += [PSCustomObject]@{
                project_id = $r.project_id
                name = $r.name
                repo_url = $r.repo_url
                branch = $r.branch
                freeze_sha = $r.freeze_sha
                freeze_date = $r.freeze_date
                commits_since_start_year = $r.commits_since_start_year
                authors_since_start_year = $r.authors_since_start_year
                files_at_freeze = $r.files_at_freeze
                included_first_party_files_at_freeze = $r.included_first_party_files_at_freeze
                included_file_pct = $r.included_file_pct
                extensions = $r.extensions
                exclude_paths = $r.exclude_paths
            }
        }
    }
    else {
        Write-Warning "Audit nao encontrado para ${p}: $audit"
    }
}
$rows | Export-Csv $manifestPath -NoTypeInformation -Encoding utf8

Write-Host "[6/6] Gerando hashes SHA-256..."
$hashFile = Join-Path $metadataDir "SHA256SUMS.txt"
if (Test-Path $hashFile) { Remove-Item $hashFile -Force }

Get-ChildItem $freezePath -File -Recurse |
    Where-Object { $_.FullName -ne $hashFile } |
    Sort-Object FullName |
    ForEach-Object {
        $hash = Get-FileHash $_.FullName -Algorithm SHA256
        $rel = $_.FullName.Substring($freezePath.Length).TrimStart('\')
        "$($hash.Hash)  $rel" | Out-File $hashFile -Append -Encoding ascii
    }

Write-Host ""
Write-Host "Congelamento concluido." -ForegroundColor Green
Write-Host "Pasta: $freezePath"
Write-Host "Manifesto: $manifestPath"
Write-Host "Ambiente: $envFile"
Write-Host "Hashes: $hashFile"
Write-Host ""
Write-Host "A partir daqui, trate esta pasta como somente leitura."
