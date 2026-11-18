@echo off
REM YingMusic-SVC Web UI launcher (Windows)
chcp 65001 >nul
cd /d "%~dp0"

REM Restore the OpenMP runtime name expected by the PyTorch Windows wheel.
set "TL=%~dp0.venv\Lib\site-packages\torch\lib"
if not exist "%TL%\libomp140.x86_64.dll" if exist "%TL%\libiomp5md.dll" copy /y "%TL%\libiomp5md.dll" "%TL%\libomp140.x86_64.dll" >nul

set "HF_ENDPOINT=https://hf-mirror.com"
set "HF_HOME=%~dp0checkpoints"
set "HF_HUB_CACHE=%~dp0checkpoints\hf_cache"
set "HF_HUB_DISABLE_TELEMETRY=1"
set "PATH=%~dp0bin;%~dp0.venv\Scripts;%PATH%"

REM UI language is switched at the top of the web page; the choice is saved to ui_lang.json.
REM Optional first-run default (only used before any in-page choice is made):
REM set "YMSVC_LANG=zh"

echo Starting YingMusic-SVC Web UI ...
echo Switch the interface language (Chinese / English) at the top of the page.
echo Open http://127.0.0.1:30911 in your browser (it opens automatically).
echo Press Ctrl+C to stop.
echo.

"%~dp0.venv\Scripts\python.exe" gradio_app.py

echo.
echo Gradio exited with code %ERRORLEVEL%.
pause
