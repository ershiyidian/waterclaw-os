$ErrorActionPreference = "Stop"

$PluginRoot = Split-Path -Parent $PSScriptRoot
$RepoRoot = Resolve-Path (Join-Path $PluginRoot "..\..")
$env:PYTHONPATH = Join-Path $RepoRoot "backend"
$env:PYTHONNOUSERSITE = "1"

conda run --no-capture-output -n waterclaw-llm python -s -m app.mcp.fastmcp_server --transport stdio
