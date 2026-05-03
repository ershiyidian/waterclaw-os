$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$envName = if ($env:WATERCLAW_CONDA_ENV) { $env:WATERCLAW_CONDA_ENV } else { "waterclaw-llm" }
$env:CONDARC = (Resolve-Path "backend/condarc.yml")
$env:PYTHONNOUSERSITE = "1"

$envList = conda env list
$exists = $envList | Select-String -SimpleMatch $envName

if (-not $exists) {
    conda env create -f backend/environment.yml
}

conda run -n $envName python -s -m pip install --isolated --no-user --upgrade pip
conda run -n $envName python -s -m pip install --isolated --no-user -r backend/requirements.txt
conda run -n $envName python -s -m pip check
