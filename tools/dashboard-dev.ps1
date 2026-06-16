<#
.SYNOPSIS
  Launch the kerrigan-dashboard dev server, robustly, on Windows.

.DESCRIPTION
  Wraps the launch dance the conductor repeated ~6 times during the dashboard
  session:
    - free port 1420 if a stale Vite/Tauri process is holding it (the recurring
      "Port 1420 is already in use" failure),
    - refresh PATH from User+Machine so a freshly-installed global `pnpm` resolves,
    - launch either the full native Tauri app (default) or the web-only Vite server
      (-Web), the latter being the browser harness used for Playwright iteration.

  With -Live, writes apps/kerrigan-dashboard/.env.local with a GitHub token from
  `gh auth token` so the *web* build (no Tauri) can hit live GitHub via the
  dev-auth path (VITE_GH_TOKEN). The token is never echoed. .env.local is gitignored.

  Run this ASYNC (run_in_terminal mode=async) since the dev server is long-running.

.PARAMETER Web
  Run the web-only Vite server (pnpm dev:web) instead of the native Tauri app.
  Use this for browser-based Playwright iteration.

.PARAMETER Live
  Write apps/kerrigan-dashboard/.env.local with VITE_GH_TOKEN from `gh auth token`
  so the web build can load live GitHub data. Implies the dev-auth browser path.
  Dev-only; never use the token in a production build.

.PARAMETER Port
  Dev server port to free before launch. Defaults to 1420.

.EXAMPLE
  .\tools\dashboard-dev.ps1
  Launch the native Tauri dev app.

.EXAMPLE
  .\tools\dashboard-dev.ps1 -Web -Live
  Launch the web-only server with live GitHub data for browser/Playwright iteration.
#>
[CmdletBinding()]
param(
  [switch]$Web,
  [switch]$Live,
  [int]$Port = 1420
)

$ErrorActionPreference = 'Continue'
$repoRoot = Split-Path -Parent $PSScriptRoot
$appDir = Join-Path $repoRoot 'apps/kerrigan-dashboard'

# 1. Free the dev port if held by a stale process.
$listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($listener) {
  Stop-Process -Id $listener.OwningProcess -Force -ErrorAction SilentlyContinue
  Write-Host "[OK] Freed port $Port (pid $($listener.OwningProcess))" -ForegroundColor Green
}
else {
  Write-Host "[OK] Port $Port is free" -ForegroundColor Green
}

# 2. Optionally write the dev-auth token for the web/browser live path.
if ($Live) {
  $token = (& gh auth token 2>$null)
  if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Host "[WARN] 'gh auth token' returned nothing; is gh authenticated? Skipping .env.local." -ForegroundColor Yellow
  }
  else {
    $envPath = Join-Path $appDir '.env.local'
    # Write UTF-8 no-BOM, no trailing newline; never echo the token.
    [System.IO.File]::WriteAllText($envPath, "VITE_GH_TOKEN=$token", (New-Object System.Text.UTF8Encoding($false)))
    Write-Host "[OK] Wrote dev token to apps/kerrigan-dashboard/.env.local (gitignored, not echoed)" -ForegroundColor Green
  }
}

# 3. Refresh PATH so a freshly-installed global pnpm resolves.
$env:Path = [System.Environment]::GetEnvironmentVariable('Path', 'User') + ';' + [System.Environment]::GetEnvironmentVariable('Path', 'Machine')

# 4. Launch.
$script = if ($Web) { 'dev:web' } else { 'tauri dev' }
Write-Host "Launching kerrigan-dashboard ($script)$(if($Live){' [live data]'})..." -ForegroundColor Cyan
if ($Web) {
  & pnpm --filter kerrigan-dashboard dev:web
}
else {
  & pnpm --filter kerrigan-dashboard tauri dev
}
