# Script simple pour démarrer MongoDB manuellement
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
    Write-Host "❌ MongoDB non trouvé dans les emplacements standards" -ForegroundColor Red
    Write-Host "💡 Essayez de démarrer MongoDB en tant qu'administrateur avec: net start MongoDB" -ForegroundColor Yellow
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

# Démarrer MongoDB
Write-Host "🚀 Démarrage de MongoDB..." -ForegroundColor Cyan
try {
    $process = Start-Process -FilePath $mongodPath -ArgumentList "--dbpath", $dataDir -WindowStyle Hidden -PassThru
    Write-Host "✅ MongoDB démarré (PID: $($process.Id))" -ForegroundColor Green
    Write-Host "⏳ Attente de 5 secondes pour que MongoDB démarre complètement..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Vérifier que MongoDB écoute sur le port 27017
    $listening = netstat -an | Select-String ":27017" | Select-String "LISTENING"
    if ($listening) {
        Write-Host "✅ MongoDB est maintenant accessible sur localhost:27017" -ForegroundColor Green
        Write-Host "💡 Vous pouvez maintenant lancer l'application avec: python app.py" -ForegroundColor Cyan
        Write-Host "⚠️  Gardez ce terminal ouvert pour que MongoDB continue de fonctionner" -ForegroundColor Yellow
    } else {
        Write-Host "⚠️  MongoDB a démarré mais le port 27017 n'est pas encore actif. Attendez quelques secondes." -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Erreur lors du démarrage de MongoDB: $_" -ForegroundColor Red
    Write-Host "💡 Essayez de démarrer MongoDB en tant qu'administrateur avec: net start MongoDB" -ForegroundColor Yellow
    exit 1
}







