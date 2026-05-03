$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$envName = if ($env:WATERCLAW_CONDA_ENV) { $env:WATERCLAW_CONDA_ENV } else { "waterclaw-llm" }
$env:CONDARC = (Resolve-Path "backend/condarc.yml")
$env:PYTHONNOUSERSITE = "1"
$env:LITELLM_LOCAL_MODEL_COST_MAP = "True"

conda run --no-capture-output -n $envName python -s -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8787 --reload
