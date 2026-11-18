@echo off
REM Accompaniment / lead vocal separation launcher (Windows, single GPU)
REM Put your songs into accom_separation\samples\raw\ first.
chcp 65001 >nul
cd /d "%~dp0accom_separation"

REM Restore the OpenMP runtime name expected by the PyTorch Windows wheel.
set "TL=%~dp0.venv\Lib\site-packages\torch\lib"
if not exist "%TL%\libomp140.x86_64.dll" if exist "%TL%\libiomp5md.dll" copy /y "%TL%\libiomp5md.dll" "%TL%\libomp140.x86_64.dll" >nul

set "CUDA_VISIBLE_DEVICES=0"
set "PATH=%~dp0bin;%~dp0.venv\Scripts;%PATH%"

"%~dp0.venv\Scripts\python.exe" inference.py ^
  --model_type bs_roformer ^
  --config_path ckpt/bs_roformer/config_bd_roformer.yaml ^
  --start_check_point ckpt/bs_roformer/bs_roformer.ckpt ^
  --input_folder samples/raw ^
  --store_dir samples/raw-infer ^
  --extract_other

echo.
echo Done. Stems are in accom_separation\samples\raw-infer\
pause
