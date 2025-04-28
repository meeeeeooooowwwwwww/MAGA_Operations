@echo off
REM MAGA Ops Setup Script
REM ---------------------

REM Set the project root directory (where this script is located)
set PROJECT_ROOT=%~dp0
cd /D "%PROJECT_ROOT%"

echo Starting MAGA Ops Setup...

REM --- Check Prerequisites ---
echo Checking for Python...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python 3 is not installed or not found in your PATH.
    echo Please install Python 3 from https://www.python.org/downloads/ and ensure it's added to your PATH.
    goto :error
) else (
    echo Python found.
)

echo Checking for Node.js...
node --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed or not found in your PATH.
    echo Please install Node.js (LTS recommended) from https://nodejs.org/ and ensure it's added to your PATH.
    goto :error
) else (
    echo Node.js found.
)

REM --- Install Dependencies ---
echo Installing Python dependencies from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Python dependencies.
    goto :error
) else (
    echo Python dependencies installed successfully.
)

echo Installing Node.js dependencies from package.json...
npm install
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Node.js dependencies.
    goto :error
) else (
    echo Node.js dependencies installed successfully.
)

REM --- Initialize Database ---
REM Check if the database file already exists
if exist maga_ops.db (
    echo Database file (maga_ops.db) already exists. Skipping schema initialization.
) else (
    echo Initializing database schema...
    python scripts/db/initialize_db.py
    if %errorlevel% neq 0 (
        echo ERROR: Failed to initialize the database schema.
        goto :error
    ) else (
        echo Database schema initialized successfully.
    )
)

REM --- Final Setup Steps ---
echo Checking for .env file...
if not exist .env (
    echo WARNING: '.env' file not found.
    echo Please copy '.env.example' to '.env' and fill in your API keys.
    echo Some features (like AI analysis and Twitter fetching) will not work without it.
) else (
    echo .env file found.
)

echo.
echo ===========================================
echo Setup Complete!
echo ===========================================
echo.
echo You can now try running the application:
REM echo Option 1: Run from source (requires Node.js)
echo   npm start
echo.
echo Remember to copy '.env.example' to '.env' and add your API keys if you haven't already.
echo.
goto :eof

:error
echo.
echo *******************************************
echo  Setup failed due to an error.
echo  Please review the messages above.
echo *******************************************
echo.

:eof
echo Press any key to exit...
pause > nul 