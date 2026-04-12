@echo off
setlocal

set IMAGE=pm-project
set CONTAINER=pm-project
set PORT=8000
set VOLUME=pm-project-data
set OLD_VOLUME=kanban-studio-data

where docker >nul 2>&1
if errorlevel 1 (
  echo Error: docker is not installed or not on PATH.
  echo Install Docker, start it, then rerun scripts\start.bat.
  exit /b 1
)

docker ps -a --format "{{.Names}}" | findstr /x "%CONTAINER%" >nul 2>&1
if not errorlevel 1 (
  echo Removing existing container...
  docker rm -f %CONTAINER%
)

docker build -t %IMAGE% "%~dp0.."

set HAS_OLD=
set HAS_NEW=
for /f "delims=" %%v in ('docker volume ls --format "{{.Name}}"') do (
  if /I "%%v"=="%OLD_VOLUME%" set HAS_OLD=1
  if /I "%%v"=="%VOLUME%" set HAS_NEW=1
)

if defined HAS_OLD if not defined HAS_NEW (
  echo Migrating Docker volume %OLD_VOLUME% to %VOLUME%...
  docker volume create %VOLUME% >nul
  docker run --rm -v %OLD_VOLUME%:/from -v %VOLUME%:/to alpine sh -c "cp -a /from/. /to/"
)

set ENV_ARG=
if exist "%~dp0..\.env" set ENV_ARG=--env-file "%~dp0..\.env"
docker run -d --name %CONTAINER% -p %PORT%:8000 -v %VOLUME%:/app/data %ENV_ARG% %IMAGE%

docker ps --format "{{.Names}}" | findstr /x "%CONTAINER%" >nul 2>&1
if errorlevel 1 (
  echo Error: container failed to start.
  docker logs %CONTAINER%
  exit /b 1
)

echo pm-project running at http://localhost:%PORT%
