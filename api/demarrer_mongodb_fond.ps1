# Script pour démarrer MongoDB en arrière-plan
Write-Host "🔍 Recherche de MongoDB..." -ForegroundColor Cyan

# Chercher mongod.exe
$mongodPath = $null
$searchPaths = @(
    "C:\Program Files\MongoDB\Server\*\bin\mongod.exe",
    "C:\Program Files (x86)\MongoDB\Server\*\bin\mongod.exe"
)

foreach ($path in $searchPaths) {
    $found = Get-ChildItem -Path $path -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) {
        $mongodPath = $found.FullName
        break
    }
}

if (-not $mongodPath) {
    Write-Host "❌ MongoDB non trouvé" -ForegroundColor Red
    Write-Host "💡 Installez MongoDB depuis: https://www.mongodb.com/try/download/community" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ MongoDB trouvé: $mongodPath" -ForegroundColor Green

# Créer le dossier de données
$dataDir = "C:\data\db"
if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
    Write-Host "📁 Dossier de données créé: $dataDir" -ForegroundColor Green
}

# Vérifier si MongoDB est déjà en cours d'exécution
$mongodProcess = Get-Process -Name "mongod" -ErrorAction SilentlyContinue
if ($mongodProcess) {
    Write-Host "✅ MongoDB est déjà en cours d'exécution (PID: $($mongodProcess.Id))" -ForegroundColor Green
    Write-Host "🌐 MongoDB est accessible sur localhost:27017" -ForegroundColor Cyan
    exit 0
}

# Démarrer MongoDB en arrière-plan
Write-Host "🚀 Démarrage de MongoDB en arrière-plan..." -ForegroundColor Cyan

# Créer un fichier de log
$logFile = Join-Path $PSScriptRoot "mongodb.log"

try {
    # Démarrer MongoDB avec redirection des logs
    $process = Start-Process -FilePath $mongodPath -ArgumentList "--dbpath", $dataDir -WindowStyle Hidden -PassThru -RedirectStandardOutput $logFile -RedirectStandardError $logFile
    
    Write-Host "✅ MongoDB démarré (PID: $($process.Id))" -ForegroundColor Green
    Write-Host "⏳ Attente de 5 secondes pour que MongoDB démarre..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Vérifier que le processus est toujours actif
    $stillRunning = Get-Process -Id $process.Id -ErrorAction SilentlyContinue
    if (-not $stillRunning) {
        Write-Host "❌ MongoDB s'est arrêté immédiatement. Vérifiez les logs: $logFile" -ForegroundColor Red
        exit 1
    }
    
    # Vérifier que MongoDB écoute sur le port 27017
    $listening = netstat -an | Select-String ":27017" | Select-String "LISTENING"
    if ($listening) {
        Write-Host "✅ MongoDB est maintenant accessible sur localhost:27017" -ForegroundColor Green
        Write-Host "📋 Logs disponibles dans: $logFile" -ForegroundColor Cyan
        Write-Host "" -ForegroundColor Cyan
        Write-Host "💡 MongoDB continuera de fonctionner en arrière-plan" -ForegroundColor Yellow
        Write-Host "💡 Vous pouvez maintenant lancer l'application avec: python app.py" -ForegroundColor Cyan
        Write-Host "💡 Pour arrêter MongoDB, utilisez: Stop-Process -Name mongod" -ForegroundColor Yellow
    } else {
        Write-Host "⚠️  MongoDB a démarré mais le port 27017 n'est pas encore actif" -ForegroundColor Yellow
        Write-Host "💡 Attendez quelques secondes et vérifiez avec: netstat -an | findstr ':27017'" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Erreur lors du démarrage de MongoDB: $_" -ForegroundColor Red
    Write-Host "💡 Vérifiez les logs: $logFile" -ForegroundColor Yellow
    exit 1
}










