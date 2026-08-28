@echo off
REM Auto-bootstrap and launch the Universal Downloader GUI (Windows).
cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe"

if not exist "%PY%" (
  echo [run] Creating virtual environment...
  py -3 -m venv .venv
  set "PY=.venv\Scripts\python.exe"
)

"%PY%" -c "import downloader.app.main" >nul 2>&1
if errorlevel 1 (
  echo [run] Installing dependencies (first run, this may take a while)...
  "%PY%" -m pip install --upgrade pip
  "%PY%" -m pip install -e ".[dev]"
)

"%PY%" -m downloader.app.main %*
