@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
title Build portable YingMusic-SVC

REM ============================================================
REM  Build a self-contained portable folder from a working install.
REM
REM  Prerequisite: this repo already has a working .venv and all
REM  models downloaded (run setup_windows.bat first).
REM
REM  Usage:
REM    build_portable.bat                 -> ..\YingMusic-SVC-Portable
REM    build_portable.bat D:\MyFolder     -> custom destination
REM    set NO_PAUSE=1                     -> unattended (skip pauses)
REM ============================================================

set "SRC=%~dp0"
if "%SRC:~-1%"=="\" set "SRC=%SRC:~0,-1%"

set "DEST=%~1"
if "%DEST%"=="" set "DEST=%SRC%\..\YingMusic-SVC-Portable"
for %%I in ("%DEST%") do set "DEST=%%~fI"

set "PYVER=3.10.11"
set "PYZIP=%TEMP%\python-%PYVER%-embed-amd64.zip"
set "PYURL=https://mirrors.huaweicloud.com/python/%PYVER%/python-%PYVER%-embed-amd64.zip"

set "HOLD=pause"
if "%NO_PAUSE%"=="1" set "HOLD=echo."

echo ============================================================
echo   Build portable bundle (target PC needs no Python)
echo   Source : %SRC%
echo   Target : %DEST%
echo ============================================================
echo.

if not exist "%SRC%\.venv\Scripts\python.exe" (
  echo [ERROR] .venv not found. Run setup_windows.bat first.
  goto :fail
)
if "%DEST%"=="%SRC%" (
  echo [ERROR] Target must differ from source directory.
  goto :fail
)

REM ---- 1. Embeddable Python ----
echo [1/6] Preparing embeddable Python %PYVER% ...
if exist "%PYZIP%" goto :have_zip
echo   Downloading from huaweicloud mirror ...
powershell -NoProfile -Command "try { Invoke-WebRequest -Uri '%PYURL%' -OutFile '%PYZIP%' -UseBasicParsing -TimeoutSec 180 } catch { exit 1 }"
if errorlevel 1 (
  echo [ERROR] Download failed. Fetch manually:
  echo   %PYURL%
  echo Save as %PYZIP% then re-run.
  goto :fail
)
:have_zip
if not exist "%DEST%\python" mkdir "%DEST%\python"
powershell -NoProfile -Command "Expand-Archive -LiteralPath '%PYZIP%' -DestinationPath '%DEST%\python' -Force"
if errorlevel 1 (
  echo [ERROR] Extract failed.
  goto :fail
)

> "%DEST%\python\python310._pth" echo python310.zip
>>"%DEST%\python\python310._pth" echo .
>>"%DEST%\python\python310._pth" echo Lib\site-packages
>>"%DEST%\python\python310._pth" echo import site

REM ---- 2. Dependencies ----
echo [2/6] Copying site-packages (about 5.8 GB) ...
robocopy "%SRC%\.venv\Lib\site-packages" "%DEST%\python\Lib\site-packages" /E /MT:16 /R:1 /W:1 /NFL /NDL /NJH /NJS /NP
if errorlevel 8 (
  echo [ERROR] Copy of site-packages failed.
  goto :fail
)

REM ---- 3. Project code ----
REM Dev-only leftovers are excluded so the bundle looks like a product, not a
REM working tree: VCS metadata, the *.original / *.before_* backup copies of
REM gradio_app.py / my_inference.py / run_*.bat, and every *.md but README.md
REM (that is how the Chinese handover note stays out while README still ships).
echo [3/6] Copying project code ...
robocopy "%SRC%" "%DEST%" /E /MT:8 /R:1 /W:1 /NFL /NDL /NJH /NJS /NP /XD "%SRC%\.venv" "%SRC%\.git" "%SRC%\.workbuddy" "%SRC%\outputs" "%SRC%\timbre_library" "%SRC%\checkpoints" "%SRC%\__pycache__" /XF "*.pyc" "*.log" ".gitignore" ".gitattributes" "*.original.py" "*.original.txt" "*.before_*.py" "*.before_*.bat" "*.md"
copy /y "%SRC%\README.md" "%DEST%\README.md" >nul
if errorlevel 8 (
  echo [ERROR] Copy of project code failed.
  goto :fail
)

REM ---- 4. Models ----
echo [4/6] Copying model weights (about 3.5 GB) ...
robocopy "%SRC%\checkpoints" "%DEST%\checkpoints" /E /MT:16 /R:1 /W:1 /NFL /NDL /NJH /NJS /NP
if errorlevel 8 (
  echo [ERROR] Copy of checkpoints failed.
  goto :fail
)
robocopy "%SRC%\accom_separation\ckpt" "%DEST%\accom_separation\ckpt" /E /MT:8 /R:1 /W:1 /NFL /NDL /NJH /NJS /NP
if errorlevel 8 (
  echo [ERROR] Copy of separation weights failed.
  goto :fail
)

REM ---- 5. Runtime fixups ----
echo [5/6] Applying runtime fixups ...
set "TL=%DEST%\python\Lib\site-packages\torch\lib"
if not exist "%TL%\libomp140.x86_64.dll" if exist "%TL%\libiomp5md.dll" (
  copy /y "%TL%\libiomp5md.dll" "%TL%\libomp140.x86_64.dll" >nul
  echo   OpenMP shim created
)
if not exist "%DEST%\timbre_library" mkdir "%DEST%\timbre_library"
if not exist "%DEST%\outputs" mkdir "%DEST%\outputs"

REM ---- 6. Launcher ----
echo [6/6] Writing start.bat ...
> "%DEST%\start.bat" echo @echo off
>>"%DEST%\start.bat" echo chcp 65001 ^>nul
>>"%DEST%\start.bat" echo cd /d "%%~dp0"
>>"%DEST%\start.bat" echo set "HF_ENDPOINT=https://hf-mirror.com"
>>"%DEST%\start.bat" echo set "HF_HOME=%%~dp0checkpoints"
>>"%DEST%\start.bat" echo set "HF_HUB_CACHE=%%~dp0checkpoints\hf_cache"
>>"%DEST%\start.bat" echo set "HF_HUB_DISABLE_TELEMETRY=1"
>>"%DEST%\start.bat" echo set "PATH=%%~dp0bin;%%~dp0python;%%PATH%%"
>>"%DEST%\start.bat" echo set "NUMBA_CACHE_DIR=%%LOCALAPPDATA%%\YingMusic-SVC-Launcher\numba_cache"
>>"%DEST%\start.bat" echo if not exist "%%NUMBA_CACHE_DIR%%" mkdir "%%NUMBA_CACHE_DIR%%" ^>nul 2^>nul
>>"%DEST%\start.bat" echo echo Starting YingMusic-SVC ... close this window to stop.
>>"%DEST%\start.bat" echo "%%~dp0python\python.exe" gradio_app.py
>>"%DEST%\start.bat" echo pause

echo.
echo ============================================================
echo   Done.
echo   Run: %DEST%\start.bat
echo ============================================================
goto :eof

:fail
%HOLD%
exit /b 1
