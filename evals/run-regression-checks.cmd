@echo off
rem run-regression-checks launcher - interpreter fallback with Store-stub probe.
rem Tier 1: py (official launcher, always real).
rem Tier 2: python - but probe it first (Store placeholder exits 9009).
set "PYEXE="
where py >nul 2>nul && set "PYEXE=py"
if defined PYEXE goto run_py
where python >nul 2>nul && set "PYEXE=python"
if not defined PYEXE (
    echo ERROR: no Python interpreter found. Install real CPython first.
    exit /b 1
)
python -c "import sys; sys.exit(0 if sys.version_info>=(3,11) else 1)" >nul 2>nul
if errorlevel 1 (
    echo ERROR: python resolves to a Store placeholder or too-old interpreter. Use the py launcher.
    exit /b 1
)
:run_py
"%PYEXE%" "%~dp0run-regression-checks.py" %*
exit /b %ERRORLEVEL%
