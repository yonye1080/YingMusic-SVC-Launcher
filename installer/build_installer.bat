@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
title Build installer for YingMusic-SVC-Launcher

REM ============================================================
REM  Compile the Inno Setup installer from the portable bundle.
REM
REM  Usage:
REM    build_installer.bat                       (default payload D:\YingMusic-SVC-Portable)
REM    build_installer.bat <payloadDir> [outDir]
REM
REM  Requires Inno Setup 6:
REM    winget install --id JRSoftware.InnoSetup -e
REM ============================================================

set "ROOT=%~dp0"
set "PAYLOAD=%~1"
if "%PAYLOAD%"=="" set "PAYLOAD=D:\YingMusic-SVC-Portable"
set "OUT=%~2"
if "%OUT%"=="" set "OUT=D:\YingMusic-SVC-Installer\out"

if not exist "%PAYLOAD%\python\python.exe" (
  echo [ERROR] Portable payload not found: %PAYLOAD%
  echo         Build it first with build_portable.bat
  exit /b 1
)

set "ISCC="
for %%P in (
  "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
  "%ProgramFiles%\Inno Setup 6\ISCC.exe"
  "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
) do (
  if exist %%P if not defined ISCC set "ISCC=%%~P"
)
if not defined ISCC (
  echo [ERROR] Inno Setup 6 not found.
  echo         winget install --id JRSoftware.InnoSetup -e
  echo         or https://jrsoftware.org/isdl.php
  exit /b 1
)

echo ============================================================
echo   Compiler : !ISCC!
echo   Payload  : %PAYLOAD%
echo   Output   : %OUT%
echo ============================================================
echo.

if not exist "%OUT%" mkdir "%OUT%"

"!ISCC!" /Qp /DPayloadDir="%PAYLOAD%" /DOutDir="%OUT%" "%ROOT%YingMusic-SVC-Launcher.iss"

if errorlevel 1 (
  echo.
  echo [ERROR] Compile failed. See messages above.
  exit /b 1
)

echo.
echo ============================================================
echo   Done. Output files:
dir /b "%OUT%"
echo ============================================================
