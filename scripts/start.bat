@echo off
setlocal

set IMAGE=kanban-studio
set CONTAINER=kanban-studio
set PORT=8000

docker ps -a --format "{{.Names}}" | findstr /x "%CONTAINER%" >nul 2>&1
if not errorlevel 1 (
  echo Removing existing container...
  docker rm -f %CONTAINER%
)

docker build -t %IMAGE% "%~dp0.."
set ENV_ARG=
if exist "%~dp0..\.env" set ENV_ARG=--env-file "%~dp0..\.env"
docker run -d --name %CONTAINER% -p %PORT%:8000 %ENV_ARG% %IMAGE%
echo Kanban Studio running at http://localhost:%PORT%
