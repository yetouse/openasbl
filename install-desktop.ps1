[CmdletBinding()]
param(
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Step {
  param([string]$Message)
  Write-Host "==> $Message"
}

function Run-Command {
  param(
    [Parameter(Mandatory = $true)][scriptblock]$Action,
    [string]$Display = ''
  )

  if ($Display) {
    Write-Host "  $Display"
  }

  if ($DryRun) {
    return
  }

  & $Action
}

function Get-PythonCommand {
  if (Get-Command py -ErrorAction SilentlyContinue) {
    return @{ Command = 'py'; Args = @('-3') }
  }

  if (Get-Command python -ErrorAction SilentlyContinue) {
    return @{ Command = 'python'; Args = @() }
  }

  throw 'Python introuvable. Installez Python 3.11+ puis relancez le script.'
}

function Get-NpmCommand {
  if (Get-Command npm -ErrorAction SilentlyContinue) {
    return 'npm'
  }

  throw 'npm introuvable. Installez Node.js 20+ puis relancez le script.'
}

function Get-GitCommand {
  if (Get-Command git -ErrorAction SilentlyContinue) {
    return 'git'
  }

  throw 'git introuvable. Installez Git puis relancez le script.'
}

$repoUrl = 'https://github.com/yetouse/openasbl.git'
$installDir = if ($env:OPENASBL_INSTALL_DIR) {
  $env:OPENASBL_INSTALL_DIR
} else {
  Join-Path $HOME 'openasbl'
}

$dataDir = if ($env:OPENASBL_DATA_DIR) {
  $env:OPENASBL_DATA_DIR
} else {
  if ($env:LOCALAPPDATA) {
    Join-Path $env:LOCALAPPDATA 'OpenASBL\data'
  } else {
    Join-Path $HOME 'AppData\Local\OpenASBL\data'
  }
}

$port = if ($env:OPENASBL_PORT) { $env:OPENASBL_PORT } else { '8765' }
$git = Get-GitCommand
$python = Get-PythonCommand
$npm = Get-NpmCommand
$pythonArgs = $python.Args
$repoRoot = $installDir
$desktopDir = Join-Path $repoRoot 'desktop'
$venvDir = Join-Path $repoRoot '.venv'
$venvPython = Join-Path $venvDir 'Scripts\python.exe'

Write-Step "Dépôt dans $installDir"
if (Test-Path (Join-Path $repoRoot '.git')) {
  Run-Command -Display "$git -C `"$repoRoot`" pull --ff-only" -Action {
    & $git -C $repoRoot pull --ff-only
  }
} else {
  Run-Command -Display "$git clone $repoUrl `"$repoRoot`"" -Action {
    & $git clone $repoUrl $repoRoot
  }
}

Write-Step 'Environnement virtuel Python'
if (-not (Test-Path $venvPython)) {
  Run-Command -Display "$($python.Command) $($pythonArgs -join ' ') -m venv `"$venvDir`"" -Action {
    & $python.Command @pythonArgs -m venv $venvDir
  }
}

Run-Command -Display "`"$venvPython`" -m pip install --upgrade pip" -Action {
  & $venvPython -m pip install --upgrade pip
}

Run-Command -Display "`"$venvPython`" -m pip install -r requirements.txt" -Action {
  & $venvPython -m pip install -r (Join-Path $repoRoot 'requirements.txt')
}

Write-Step 'Dépendances Node du desktop'
Run-Command -Display "cd `"$desktopDir`"; $npm install" -Action {
  Push-Location $desktopDir
  try {
    & $npm install
  } finally {
    Pop-Location
  }
}

Write-Step 'Répertoire de données'
Run-Command -Display "New-Item -ItemType Directory -Force -Path `"$dataDir`" | Out-Null" -Action {
  New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
}

Write-Step 'Migrations Django'
$env:OPENASBL_RUNTIME_MODE = 'desktop'
$env:OPENASBL_DATA_DIR = $dataDir
$env:OPENASBL_PORT = $port

Run-Command -Display "`"$venvPython`" manage.py migrate --noinput" -Action {
  & $venvPython (Join-Path $repoRoot 'manage.py') migrate --noinput
}

Write-Host ''
Write-Host '================================================'
Write-Host '  Installation desktop terminée !'
Write-Host '================================================'
Write-Host ''
Write-Host 'Pour lancer OpenASBL en mode desktop :'
Write-Host "  cd $desktopDir"
Write-Host '  npm run dev'
Write-Host ''
Write-Host 'Données utilisateur :'
Write-Host "  $dataDir"
Write-Host ''
Write-Host 'Démo / aperçu sans exécution :'
Write-Host '  powershell -NoProfile -ExecutionPolicy Bypass -File .\install-desktop.ps1 -DryRun'
