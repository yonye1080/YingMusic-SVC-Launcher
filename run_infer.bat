@echo off
REM YingMusic-SVC command line inference template (Windows)
REM Edit SOURCE / TARGET / ACCOMPANY / VOCAL_OFFSET / INST_GAIN below before running.
chcp 65001 >nul
cd /d "%~dp0"

REM Restore the OpenMP runtime name expected by the PyTorch Windows wheel.
set "TL=%~dp0.venv\Lib\site-packages\torch\lib"
if not exist "%TL%\libomp140.x86_64.dll" if exist "%TL%\libiomp5md.dll" copy /y "%TL%\libiomp5md.dll" "%TL%\libomp140.x86_64.dll" >nul

set "HF_ENDPOINT=https://hf-mirror.com"
set "HF_HOME=%~dp0checkpoints"
set "HF_HUB_CACHE=%~dp0checkpoints\hf_cache"
set "PATH=%~dp0bin;%~dp0.venv\Scripts;%PATH%"

set "SOURCE=path\to\source_vocal.wav"
set "TARGET=path\to\target_timbre.wav"
set "ACCOMPANY="
set "VOCAL_OFFSET=0.0"
set "INST_GAIN=-3.0"

"%~dp0.venv\Scripts\python.exe" my_inference.py ^
  --source "%SOURCE%" ^
  --target "%TARGET%" ^
  --diffusion-steps 100 ^
  --checkpoint "checkpoints\YingMusic-SVC-full.pt" ^
  --expname "my_exp" ^
  --cuda 0 ^
  --fp16 True ^
  --accompany "%ACCOMPANY%" ^
  --vocal-offset %VOCAL_OFFSET% ^
  --inst-gain %INST_GAIN% ^
  --config "configs\YingMusic-SVC.yml"

echo.
echo Done. Results are in the outputs\ folder.
pause
