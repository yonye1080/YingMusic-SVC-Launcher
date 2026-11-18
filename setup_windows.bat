@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"
title YingMusic-SVC Setup (Windows)

echo ============================================================
echo   YingMusic-SVC one-click setup (Windows / China mirrors)
echo ============================================================
echo.

REM ---- 1. Locate Python 3.10 ----
echo [1/6] Checking Python 3.10 ...
set "PYEXE="
for /f "delims=" %%v in ('py -3.10 -c "import sys;print(sys.executable)" 2^>nul') do set "PYEXE=%%v"
if not defined PYEXE (
  for /f "delims=" %%v in ('python -c "import sys;print(sys.executable) if sys.version_info[:2]==(3,10) else ''" 2^>nul') do set "PYEXE=%%v"
)
if not defined PYEXE (
  echo   Python 3.10 not found.
  echo   Please install Python 3.10 first:
  echo     https://mirrors.huaweicloud.com/python/3.10.11/python-3.10.11-amd64.exe
  echo   Remember to check "Add python.exe to PATH" during installation.
  pause
  exit /b 1
)
echo   Using Python: !PYEXE!

REM ---- 2. Create virtual environment ----
echo [2/6] Creating virtual environment .venv ...
if not exist ".venv\Scripts\python.exe" (
  "!PYEXE!" -m venv .venv
  if errorlevel 1 ( echo   Failed to create venv. & pause & exit /b 1 )
) else (
  echo   .venv already exists, skipping.
)
set "VENVPY=%~dp0.venv\Scripts\python.exe"

REM ---- 3. Install dependencies (requirements.txt already points to ----
REM         Tsinghua PyPI + Aliyun cu124 wheels) ----
echo [3/6] Installing dependencies (incl. torch 2.4.0+cu124, ~2.5GB, please wait)...
"!VENVPY!" -m pip install --upgrade pip
"!VENVPY!" -m pip install -r requirements.txt
if errorlevel 1 ( echo   Dependency installation failed. & pause & exit /b 1 )

REM ---- 4. Restore OpenMP runtime name expected by torch Windows wheel ----
echo [4/6] Restoring libomp140.x86_64.dll ...
set "TL=%~dp0.venv\Lib\site-packages\torch\lib"
if not exist "%TL%\libomp140.x86_64.dll" if exist "%TL%\libiomp5md.dll" copy /y "%TL%\libiomp5md.dll" "%TL%\libomp140.x86_64.dll" >nul

REM ---- 5. Deploy ffmpeg (provided by imageio-ffmpeg) ----
echo [5/6] Deploying ffmpeg ...
if not exist "bin" mkdir bin
"!VENVPY!" -c "import imageio_ffmpeg,shutil,os; os.makedirs('bin',exist_ok=True); shutil.copy(imageio_ffmpeg.get_ffmpeg_exe(),'bin/ffmpeg.exe'); print('  ffmpeg -> bin/ffmpeg.exe')"

REM ---- 6. Download models (main weights via ModelScope, runtime via hf-mirror) ----
echo [6/6] Downloading models (main: ModelScope, runtime: hf-mirror)...
"!VENVPY!" download_models.py --mirror cn
if errorlevel 1 (
  echo   Some models are not ready. Re-run this script to resume.
  pause
  exit /b 1
)

echo.
echo ============================================================
echo   Setup complete! Double-click run_gradio.bat to start the UI.
echo   Open http://127.0.0.1:30911 in your browser.
echo ============================================================
pause
