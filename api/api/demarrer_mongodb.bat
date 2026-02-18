@echo off
echo ========================================
echo   Demarrage de MongoDB
echo ========================================
echo.

REM Essayer de démarrer le service MongoDB
echo [1/3] Tentative de demarrage du service MongoDB...
net start MongoDB 2>nul
if %errorlevel% == 0 (
    echo [OK] MongoDB demarre en tant que service
    goto :verify
)

echo [INFO] Le service MongoDB necessite des privileges administrateur
echo [2/3] Demarrage manuel de MongoDB...

REM Chercher mongod.exe
set MONGOD_PATH=
for /d %%i in ("C:\Program Files\MongoDB\Server\*") do (
    if exist "%%i\bin\mongod.exe" (
        set MONGOD_PATH=%%i\bin\mongod.exe
        goto :found
    )
)

for /d %%i in ("C:\Program Files (x86)\MongoDB\Server\*") do (
    if exist "%%i\bin\mongod.exe" (
        set MONGOD_PATH=%%i\bin\mongod.exe
        goto :found
    )
)

:found
if "%MONGOD_PATH%"=="" (
    echo [ERREUR] MongoDB non trouve
    echo [INFO] Installez MongoDB depuis: https://www.mongodb.com/try/download/community
    pause
    exit /b 1
)

echo [OK] MongoDB trouve: %MONGOD_PATH%

REM Creer le dossier de donnees
if not exist "C:\data\db" (
    mkdir "C:\data\db" 2>nul
    echo [OK] Dossier de donnees cree: C:\data\db
)

REM Verifier si MongoDB est deja en cours d'execution
tasklist /FI "IMAGENAME eq mongod.exe" 2>NUL | find /I /N "mongod.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] MongoDB est deja en cours d'execution
    goto :verify
)

REM Demarrer MongoDB
echo [3/3] Demarrage de MongoDB...
start /B "" "%MONGOD_PATH%" --dbpath "C:\data\db"
timeout /t 5 /nobreak >nul

:verify
echo.
echo [VERIFICATION] Verification du port 27017...
netstat -an | findstr ":27017" | findstr "LISTENING" >nul
if %errorlevel% == 0 (
    echo [OK] MongoDB est accessible sur localhost:27017
    echo.
    echo ========================================
    echo   MongoDB est pret !
    echo ========================================
    echo.
    echo Vous pouvez maintenant lancer l'application avec:
    echo   python app.py
    echo.
    echo IMPORTANT: Gardez cette fenetre ouverte pour que MongoDB continue de fonctionner.
    echo.
) else (
    echo [ATTENTION] Le port 27017 n'est pas encore actif.
    echo [INFO] Attendez quelques secondes et verifiez avec: netstat -an ^| findstr ":27017"
    echo.
)

pause







