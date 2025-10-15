# mini_crm_base tasks (PowerShell)
# Usage examples:
#   .\tasks.ps1 help
#   .\tasks.ps1 venv
#   .\tasks.ps1 dev-up
#   .\tasks.ps1 dc-up
#   .\tasks.ps1 dc-smoke

param(
  [Parameter(Position=0)]
  [ValidateSet(
    'help','venv','dev-up','migrate','makemigrations','superuser','shell',
    'test','schema','lint','fix','check',
    'dc-build','dc-up','dc-down','dc-down-v','reset-dc',
    'logs','logs-web','logs-worker','logs-beat','dc-smoke',
    'precommit-install','clean','ci'
  )]
  [string]$Task = 'help',

  [int]$Port = 8000,
  [string]$DjangoSettings = 'config.settings.dev',
  [string]$HealthUrl = "http://127.0.0.1:$Port/health/"
)

$ErrorActionPreference = 'Stop'
$PY = 'python'
$Manage = 'src/manage.py'
$Compose = 'docker compose'

function Ensure-Command([string]$cmd) {
  if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
    throw "Command '$cmd' not found. Install it or add to PATH."
  }
}

function Use-Venv {
  if (-not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
    Write-Host "Creating virtualenv .venv ..." -ForegroundColor Yellow
    & $PY -m venv .venv
  }
  . .\.venv\Scripts\Activate.ps1
}

function Ensure-Env {
  if (-not $env:DJANGO_SETTINGS_MODULE) { $env:DJANGO_SETTINGS_MODULE = $DjangoSettings }
}

# -------- Dev (no Docker) --------
function Task-Venv {
  Ensure-Command $PY
  Use-Venv
  python -m pip install --upgrade pip
  pip install -r requirements-dev.txt
  Write-Host "venv ready. Activate: .\.venv\Scripts\Activate.ps1" -ForegroundColor Green
}

function Task-DevUp {
  Ensure-Command $PY
  Use-Venv; Ensure-Env
  & $PY $Manage migrate
  & $PY $Manage runserver "127.0.0.1:$Port"
}

function Task-Migrate { Use-Venv; Ensure-Env; & $PY $Manage migrate }
function Task-MakeMigrations { Use-Venv; Ensure-Env; & $PY $Manage makemigrations }
function Task-Superuser { Use-Venv; Ensure-Env; & $PY $Manage createsuperuser }
function Task-Shell { Use-Venv; Ensure-Env; & $PY $Manage shell }

# -------- Tests / Quality --------
function Task-Test { Use-Venv; Ensure-Env; pytest -q }
function Task-Schema { Use-Venv; Ensure-Env; & $PY $Manage spectacular --validate --file src/schema.yaml }

function Task-Lint {
  if (-not (Get-Command 'pre-commit' -ErrorAction SilentlyContinue)) {
    Write-Host "Installing pre-commit into venv..." -ForegroundColor Yellow
    Use-Venv; pip install pre-commit
  } else { Use-Venv }
  pre-commit run -a
}

function Task-Fix {
  if (-not (Get-Command 'pre-commit' -ErrorAction SilentlyContinue)) {
    Use-Venv; pip install pre-commit
  } else { Use-Venv }
  pre-commit run -a -v; $code = $LASTEXITCODE
  pre-commit run -a
  if ($code -ne 0) { Write-Host "Autoformat changed files; second pass is OK." -ForegroundColor Yellow }
}

function Task-Check { Task-Lint; Task-Test; Task-Schema }

# -------- Docker workflow --------
function Task-DcBuild { & $Compose build }
function Task-DcUp { & $Compose up -d; & $Compose ps }
function Task-DcDown { & $Compose down }
function Task-DcDownV { & $Compose down -v }
function Task-ResetDC { Task-DcDownV; Task-DcBuild; Task-DcUp }

function Task-Logs { & $Compose logs --no-color --tail=200 }
function Task-LogsWeb { & $Compose logs --no-color --tail=200 web }
function Task-LogsWorker { & $Compose logs --no-color --tail=200 worker }
function Task-LogsBeat { & $Compose logs --no-color --tail=200 beat }

function Task-DcSmoke {
  Write-Host "Waiting for $HealthUrl ..." -ForegroundColor Yellow
  $ok = $false
  for ($i=1; $i -le 30; $i++) {
    try {
      $resp = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -TimeoutSec 3
      if ($resp.StatusCode -eq 200) { $ok = $true; break }
    } catch { Start-Sleep -Seconds 2 }
  }
  if ($ok) { Write-Host "OK: $HealthUrl" -ForegroundColor Green }
  else { Write-Error "FAIL: $HealthUrl not ready in time" }
}

# -------- Misc --------
function Task-PrecommitInstall {
  if (-not (Get-Command 'pre-commit' -ErrorAction SilentlyContinue)) {
    Use-Venv; pip install pre-commit
  } else { Use-Venv }
  pre-commit install
  Write-Host "pre-commit hooks installed." -ForegroundColor Green
}

function Task-Clean {
  Write-Host "Cleaning artifacts..." -ForegroundColor Yellow
  Get-ChildItem -Recurse -Include *.pyc | Remove-Item -Force -ErrorAction SilentlyContinue
  Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
  Remove-Item -Recurse -Force build,dist -ErrorAction SilentlyContinue
}

function Task-CI { Task-Lint; Task-Test; Task-Schema }

# -------- Help --------
function Task-Help {
  @"
Available tasks (usage: .\tasks.ps1 <task>):

  help                 - show this message
  venv                 - create venv and install requirements-dev.txt
  dev-up               - runserver locally on 127.0.0.1:$Port
  migrate              - apply migrations
  makemigrations       - create migrations
  superuser            - create superuser
  shell                - open Django shell

  test                 - pytest (writes coverage.xml)
  schema               - generate/validate OpenAPI (src/schema.yaml)
  lint                 - pre-commit run -a
  fix                  - autoformat + second pass
  check                - lint + test + schema

  dc-build             - docker compose build
  dc-up                - docker compose up -d
  dc-down              - docker compose down
  dc-down-v            - docker compose down -v (remove volumes)
  reset-dc             - clean rebuild and up
  logs                 - docker compose logs (tail 200)
  logs-web             - logs for web
  logs-worker          - logs for worker
  logs-beat            - logs for beat
  dc-smoke             - wait for /health 200 at $HealthUrl

  precommit-install    - install git hooks for pre-commit
  clean                - remove pyc and __pycache__
  ci                   - local CI: lint + tests + schema

Parameters:
  -Port <int>                port for runserver/health (default 8000)
  -DjangoSettings <string>   settings module (default config.settings.dev)
  -HealthUrl <string>        health URL (default http://127.0.0.1:$Port/health/)
"@ | Write-Host
}

switch ($Task) {
  'help'              { Task-Help }
  'venv'              { Task-Venv }
  'dev-up'            { Task-DevUp }
  'migrate'           { Task-Migrate }
  'makemigrations'    { Task-MakeMigrations }
  'superuser'         { Task-Superuser }
  'shell'             { Task-Shell }

  'test'              { Task-Test }
  'schema'            { Task-Schema }
  'lint'              { Task-Lint }
  'fix'               { Task-Fix }
  'check'             { Task-Check }

  'dc-build'          { Task-DcBuild }
  'dc-up'             { Task-DcUp }
  'dc-down'           { Task-DcDown }
  'dc-down-v'         { Task-DcDownV }
  'reset-dc'          { Task-ResetDC }

  'logs'              { Task-Logs }
  'logs-web'          { Task-LogsWeb }
  'logs-worker'       { Task-LogsWorker }
  'logs-beat'         { Task-LogsBeat }
  'dc-smoke'          { Task-DcSmoke }

  'precommit-install' { Task-PrecommitInstall }
  'clean'             { Task-Clean }
  'ci'                { Task-CI }
  default             { Task-Help }
}
