@echo off
REM ============================================================================
REM QuantumShield — Build & Push Docker Images to Docker Hub
REM
REM Prerequisites:
REM   1. Install Docker Desktop: https://www.docker.com/products/docker-desktop
REM   2. Create Docker Hub account: https://hub.docker.com (free, no CC)
REM   3. Run: docker login
REM
REM Usage:
REM   deploy\build_and_push.bat <your-dockerhub-username>
REM
REM Example:
REM   deploy\build_and_push.bat maboroshitech
REM ============================================================================

if "%~1"=="" (
    echo.
    echo ERROR: Please provide your Docker Hub username
    echo Usage: deploy\build_and_push.bat ^<dockerhub-username^>
    echo.
    echo Example: deploy\build_and_push.bat maboroshitech
    exit /b 1
)

set DOCKER_USER=%~1
set GATEWAY_IMAGE=%DOCKER_USER%/quantumshield-gateway:latest
set ML_IMAGE=%DOCKER_USER%/quantumshield-ml:latest

echo.
echo ============================================================
echo   QuantumShield Docker Build ^& Push
echo   Docker Hub User: %DOCKER_USER%
echo ============================================================
echo.

REM --- Step 1: Build Gateway (Render) ---
echo [1/4] Building Gateway image (Render)...
docker build -t %GATEWAY_IMAGE% -f Dockerfile .
if errorlevel 1 (
    echo ERROR: Gateway build failed!
    exit /b 1
)
echo      Gateway image built successfully.

REM --- Step 2: Build ML Service (Railway) ---
echo.
echo [2/4] Building ML Service image (Railway)...
echo      This will take 5-10 minutes on first build (PyTorch + RDKit)...
docker build -t %ML_IMAGE% -f Dockerfile.railway .
if errorlevel 1 (
    echo ERROR: ML Service build failed!
    exit /b 1
)
echo      ML Service image built successfully.

REM --- Step 3: Push Gateway ---
echo.
echo [3/4] Pushing Gateway image to Docker Hub...
docker push %GATEWAY_IMAGE%
if errorlevel 1 (
    echo ERROR: Gateway push failed! Run 'docker login' first.
    exit /b 1
)
echo      Gateway pushed: %GATEWAY_IMAGE%

REM --- Step 4: Push ML Service ---
echo.
echo [4/4] Pushing ML Service image to Docker Hub...
docker push %ML_IMAGE%
if errorlevel 1 (
    echo ERROR: ML Service push failed!
    exit /b 1
)
echo      ML Service pushed: %ML_IMAGE%

echo.
echo ============================================================
echo   BUILD ^& PUSH COMPLETE!
echo ============================================================
echo.
echo   Gateway Image:    %GATEWAY_IMAGE%
echo   ML Service Image: %ML_IMAGE%
echo.
echo   Next steps:
echo.
echo   1. RAILWAY (ML Service):
echo      - Go to railway.app ^> New Project ^> Docker Image
echo      - Enter: %ML_IMAGE%
echo      - Add env var: GEMINI_API_KEY = your-key
echo      - Generate domain ^> copy the URL
echo.
echo   2. RENDER (Gateway):
echo      - Go to render.com ^> New ^> Web Service ^> Existing Image
echo      - Enter: %GATEWAY_IMAGE%
echo      - Add env var: ML_SERVICE_URL = ^<Railway URL from step 1^>
echo      - Copy the Render URL
echo.
echo   3. FRONTEND:
echo      - Edit .env.production: VITE_API_BASE_URL=^<Render URL^>
echo      - Run: npm run build
echo      - Run: npx firebase-tools deploy --only hosting
echo.
echo   4. KEEP-ALIVE:
echo      - Go to cron-job.org ^> create job
echo      - URL: ^<Render URL^>/health
echo      - Schedule: every 5 minutes
echo.
echo ============================================================
pause
