@echo off
setlocal

set CONTAINER=kanban-studio

docker ps -a --format "{{.Names}}" | findstr /x "%CONTAINER%" >nul 2>&1
if not errorlevel 1 (
  docker rm -f %CONTAINER%
  echo Kanban Studio stopped.
) else (
  echo No container found.
)
