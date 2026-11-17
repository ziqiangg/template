# The project's quality gate: the only file that lists the project's check commands.
# Run: pwsh -NoProfile -File scripts/gate.ps1 (it moves to the project root itself).
# The workflow rules (flow.py verify) are a separate pre-commit step, not part of this file.
# Rules: stop at the first failure with a non-zero exit; print only failures and one summary line;
# never stage, commit or change files (no git add, no --fix). The hooks run it through `flow.py gate`,
# which skips a repeat on files that already passed. Order the steps cheapest first (lint, format check,
# type checks, fast unit tests, then slow tests and builds), so a quick failure never waits on a slow step.
#
# GATE-NOT-CONFIGURED  <- delete this line when the commands below are filled in (SETUP state)

$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot)
$steps = @(
    # 'uv run ruff check .'
    # 'uv run ruff format --check .'
    # 'uv run mypy --strict src tests'
    # 'npm --prefix web run lint'
    # 'npm --prefix web run typecheck'
    # 'npm --prefix web exec prettier -- --check web/src'
    # 'uv run pytest -q tests/unit'
    # 'npm --prefix web run test'
    # 'uv run pytest -q tests/integration'
    # 'npm --prefix web run build'
    # 'npm --prefix web exec -- react-doctor web --verbose --blocking error'
)

if ($steps.Count -eq 0) {
    Write-Output 'gate: not configured yet (see .claude/instructions/setup.md)'
    exit 1
}

foreach ($step in $steps) {
    $out = Invoke-Expression "$step 2>&1"
    if ($LASTEXITCODE -ne 0) {
        $out | Select-Object -Last 40
        Write-Output "gate: FAILED at '$step'"
        exit 1
    }
}
Write-Output "gate: passed ($($steps.Count) checks)"
