@echo off
setlocal

set CONTAINER=pm-project

docker ps -a --format "{{.Names}}" | findstr /x "%CONTAINER%" >nul 2>&1
if not errorlevel 1 (
  docker rm -f %CONTAINER%
  echo pm-project stopped.
) else (
  echo No container found.
)
