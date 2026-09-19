param(
    [ValidateSet("all", "questions", "analysis")]
    [string]$Feature = "all",
    [string[]]$Case = @(),
    [int]$Limit = 0,
    [switch]$Judge,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Evaluator = Join-Path $PSScriptRoot "evaluate_teaching_agent.py"
$Python = if (Test-Path (Join-Path $RepoRoot ".venv\Scripts\python.exe")) {
    Join-Path $RepoRoot ".venv\Scripts\python.exe"
} else {
    "python"
}

$Arguments = @($Evaluator, "--feature", $Feature)
foreach ($Id in $Case) { $Arguments += @("--case", $Id) }
if ($Limit -gt 0) { $Arguments += @("--limit", $Limit) }
if ($Judge) { $Arguments += "--judge" }
if ($DryRun) { $Arguments += "--dry-run" }

& $Python @Arguments
exit $LASTEXITCODE
