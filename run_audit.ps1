param([string]$TestDatabaseUrl = $env:TEST_DATABASE_URL)

$ErrorActionPreference = 'Stop'
$previousTestUrl = $env:TEST_DATABASE_URL
try {
    if ($TestDatabaseUrl) { $env:TEST_DATABASE_URL = $TestDatabaseUrl }
    Push-Location (Join-Path $PSScriptRoot 'backend')
    try {
        uv run --frozen ruff check .
        if ($LASTEXITCODE) { throw 'Backend lint failed' }
        uv run --frozen pytest -q
        if ($LASTEXITCODE) { throw 'Backend tests failed' }
    } finally { Pop-Location }
    Push-Location (Join-Path $PSScriptRoot 'frontend')
    try {
        npm.cmd run build
        if ($LASTEXITCODE) { throw 'Frontend build failed' }
        npm.cmd test
        if ($LASTEXITCODE) { throw 'Frontend tests failed' }
    } finally { Pop-Location }
} finally { $env:TEST_DATABASE_URL = $previousTestUrl }
