# build_android.ps1
# Script PowerShell de compilation APK HAYAATI - Alarme Native
# Usage :
#   .\build_android.ps1          -> Mode FAST (rebuild rapide, preserve le template Flutter)
#   .\build_android.ps1 -Scratch -> Mode SCRATCH (clean total + rebuild complet)
#
# [NEW] Version nettoyee suite a la migration hors pyjnius :
#    - Retrait complet de la copie manuelle de l'ancien module hayaati_alarm
#      (Java, res/raw, patch du Manifest) : l'alarme passe desormais par une
#      extension Flet standard (paquet local 'hayaati_alarm' wrappant le
#      package Flutter 'alarm'), bundlee automatiquement par
#      `flet build apk` comme n'importe quelle dependance Flutter normale,
#      exactement comme flet-android-notifications l'est deja.
#    - Retrait de la verification pyjnius (plus utilise nulle part).
#    - Ajout d'une verification legere : le paquet local hayaati_alarm est
#      bien installe, et les fichiers audio sont bien dans assets/sounds/
#      (nouvel emplacement, remplace l'ancien res/raw/).

param([switch]$Scratch = $false)

$ErrorActionPreference = "Stop"
$host.ui.RawUI.WindowTitle = "HAYAATI BUILD APK"

# FIX ENCODAGE UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

# ============================================================================
# MODE
# ============================================================================
if ($Scratch) {
    Write-Host "[MODE] FROM SCRATCH - clean total + rebuild complet" -ForegroundColor Magenta
} else {
    Write-Host "[MODE] FAST - rebuild rapide (template Flutter conserve)" -ForegroundColor Green
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  HAYAATI - Build APK" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# ============================================================================
# PORTABILITY
# ============================================================================
$projectRoot = if ($PSScriptRoot) { $PSScriptRoot } else { "F:\Flet HAYAATI" }
if (-not (Test-Path $projectRoot)) {
    Write-Host ""
    Write-Host "[ERROR] Dossier projet introuvable: $projectRoot" -ForegroundColor Red
    Read-Host "Appuyez sur Entree pour quitter"
    exit 1
}
Set-Location $projectRoot
Write-Host "[INFO] Dossier de travail: $projectRoot" -ForegroundColor Gray

# ============================================================================
# [NEW] VERIFICATION DE L'EXTENSION HAYAATI_ALARM (remplace pyjnius)
# ============================================================================
Write-Host ""
Write-Host "[VERIF] Verification de l'extension hayaati_alarm..." -ForegroundColor Yellow

$alarmExtensionOk = $false
foreach ($depFile in @("pyproject.toml", "requirements.txt")) {
    if (Test-Path $depFile) {
        $depContent = Get-Content $depFile -Raw
        if ($depContent -match '(?i)hayaati[-_]alarm') {
            Write-Host "    [OK] 'hayaati_alarm' reference dans $depFile" -ForegroundColor Green
            $alarmExtensionOk = $true
        }
        if ($depContent -match '(?i)pyjnius') {
            Write-Host "    [WARN] 'pyjnius' encore present dans $depFile — n'est plus utilise nulle part," -ForegroundColor DarkYellow
            Write-Host "           tu peux le retirer en toute securite." -ForegroundColor DarkYellow
        }
    }
}
if (-not $alarmExtensionOk) {
    Write-Host "    [WARN] 'hayaati_alarm' introuvable dans pyproject.toml/requirements.txt" -ForegroundColor Red
    Write-Host "           L'alarme ne pourra pas etre programmee sans cette dependance locale." -ForegroundColor Red
    $reponse = Read-Host "    Continuer quand meme ? (o/N)"
    if ($reponse -notmatch '^[oOyY]') {
        Write-Host "[ARRET] Enregistrez hayaati_alarm comme dependance locale puis relancez." -ForegroundColor Yellow
        exit 1
    }
}

# Verification des fichiers audio a leur nouvel emplacement (assets/sounds/,
# remplace l'ancien hayaati_alarm/android/.../res/raw/)
$sonsOk = $true
foreach ($sonFichier in @("adhan.mp3", "adhan_fajr.mp3")) {
    $sonPath = Join-Path "assets\sounds" $sonFichier
    if (Test-Path $sonPath) {
        Write-Host "    [OK] $sonFichier present dans assets\sounds\" -ForegroundColor Green
    } else {
        Write-Host "    [WARN] $sonFichier absent de assets\sounds\ — l'alarme n'aura pas de son personnalise" -ForegroundColor DarkYellow
        $sonsOk = $false
    }
}

# ============================================================================
# 1. ARRET DES PROCESSUS
# ============================================================================
Write-Host ""
Write-Host "[1/6] Arret des processus..." -ForegroundColor Yellow
Stop-Process -Name "java" -Force -ErrorAction SilentlyContinue
cmd /c "taskkill /F /IM gradle.bat /T >nul 2>nul"
cmd /c "taskkill /F /IM dart.exe /T >nul 2>nul"
cmd /c "taskkill /F /IM python.exe /T >nul 2>nul"
Write-Host "    [OK] Processus arretes" -ForegroundColor Green

# ============================================================================
# 2. NETTOYAGE CONDITIONNEL
# ============================================================================
Write-Host ""
if ($Scratch) {
    Write-Host "[2/6] Nettoyage total (Scratch)..." -ForegroundColor Yellow

    $ggc = "$env:USERPROFILE\.gradle\caches"
    if (Test-Path $ggc) { Remove-Item $ggc -Recurse -Force; Write-Host "    [OK] Cache global Gradle nettoye" -ForegroundColor Green }
    $lgc = "F:\.gradle_cache_hayaati"
    if (Test-Path $lgc) { Remove-Item $lgc -Recurse -Force; Write-Host "    [OK] Cache local Gradle nettoye" -ForegroundColor Green }

    if (Test-Path "build") { Remove-Item "build" -Recurse -Force; Write-Host "    [OK] build/ supprime" -ForegroundColor Green }
    if (Test-Path ".dart_tool") { Remove-Item ".dart_tool" -Recurse -Force; Write-Host "    [OK] .dart_tool supprime" -ForegroundColor Green }

    $pubCache = "F:\.pub-cache-hayaati"
    if (Test-Path $pubCache) { Remove-Item $pubCache -Recurse -Force; Write-Host "    [OK] Pub cache local nettoye" -ForegroundColor Green }
} else {
    Write-Host "[2/6] Nettoyage minimal (Fast mode)..." -ForegroundColor Yellow
    $gradleBuild = "build\flutter\android\app\build"
    if (Test-Path $gradleBuild) { 
        Remove-Item $gradleBuild -Recurse -Force
        Write-Host "    [OK] Gradle build output nettoye" -ForegroundColor Green
    }
    Write-Host "    [INFO] Template Flutter conserve - Build 1/2 saute" -ForegroundColor Gray
}

# >>> FIX : Nettoyer le temp de Windows pour liberer de l'espace sur C:\ <<<
Write-Host "    [CLEAN] Nettoyage du repertoire temporaire Windows..." -ForegroundColor Gray
$tempPaths = @($env:TEMP, "$env:LOCALAPPDATA\Temp", "C:\Windows\Temp")
foreach ($tp in $tempPaths) {
    if (Test-Path $tp) {
        Get-ChildItem $tp -Recurse -ErrorAction SilentlyContinue | 
            Where-Object { $_.CreationTime -lt (Get-Date).AddHours(-1) } | 
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# ============================================================================
# 3. ENVIRONNEMENT
# ============================================================================
Write-Host ""
Write-Host "[3/6] Configuration de l'environnement..." -ForegroundColor Yellow
$env:JAVA_HOME = 'C:\Hayaati_Tools\JDK17\jdk-17.0.20+8'
$env:PATH = 'C:\Users\gebruiker\flutter\3.44.7\bin;' + $env:JAVA_HOME + '\bin;C:\Users\gebruiker\AppData\Local\Programs\Git\cmd;' + $env:PATH
$env:GRADLE_USER_HOME = 'F:\.gradle_cache_hayaati'
$env:GRADLE_OPTS = '-Xmx1536m -XX:MaxMetaspaceSize=512m'
$env:SKIP_JDK_VERSION_CHECK = 'true'

# Pub Cache sur le meme disque que le projet
$env:PUB_CACHE = 'F:\.pub-cache-hayaati'
New-Item -ItemType Directory -Path $env:PUB_CACHE -Force | Out-Null
New-Item -ItemType Directory -Path 'F:\.gradle_cache_hayaati' -Force | Out-Null

# >>> FIX CRITIQUE : Rediriger TEMP vers F:\ pour eviter "Espace insuffisant" sur C:\ <<<
$env:TEMP = 'F:\.temp-hayaati'
$env:TMP = 'F:\.temp-hayaati'
New-Item -ItemType Directory -Path $env:TEMP -Force | Out-Null
Write-Host "    [OK] TEMP redirige vers $env:TEMP" -ForegroundColor Green

if (-not (Test-Path $env:JAVA_HOME)) {
    Write-Host "    [WARN] JAVA_HOME introuvable: $env:JAVA_HOME" -ForegroundColor DarkYellow
}
Write-Host "    [OK] Environnement pret" -ForegroundColor Green
Write-Host "    [INFO] Gradle cache: $env:GRADLE_USER_HOME" -ForegroundColor Gray
Write-Host "    [INFO] Pub cache: $env:PUB_CACHE" -ForegroundColor Gray

# ============================================================================
# 4. DEPENDANCES PYTHON (uniquement en Scratch)
# ============================================================================
if ($Scratch) {
    Write-Host ""
    Write-Host "[4/6] Installation des dependances..." -ForegroundColor Yellow
    py -3.14 -m pip install -r requirements.txt --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "    [WARN] Erreur requirements.txt, tentative pyproject.toml..." -ForegroundColor DarkYellow
        py -3.14 -m pip install . --quiet
    }
    Write-Host "    [OK] Dependances a jour" -ForegroundColor Green

    # [NEW] Confirmation que l'extension locale hayaati_alarm est bien
    # installee dans l'environnement de build (pas juste declaree en texte).
    py -3.14 -m pip show hayaati-alarm 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    [OK] hayaati_alarm installe dans l'environnement de build" -ForegroundColor Green
    } else {
        Write-Host "    [WARN] hayaati_alarm non installe localement" -ForegroundColor DarkYellow
        Write-Host "           Installez-le en mode editable : pip install -e ./hayaati_alarm/hayaati_alarm" -ForegroundColor Gray
    }
} else {
    Write-Host ""
    Write-Host "[4/6] Dependances Python (skip - Fast mode)..." -ForegroundColor Gray
}

# ============================================================================
# 5. BUILD 1 - Template Flutter (uniquement en Scratch)
# ============================================================================
if ($Scratch) {
    Write-Host ""
    Write-Host "[5/6] Build 1/2: Generation du template Flutter..." -ForegroundColor Cyan
    Write-Host "    (Des erreurs desugaring sont normales a cette etape)" -ForegroundColor DarkYellow

    flet build apk -v
    $build1Exit = $LASTEXITCODE

    if ((-not (Test-Path 'build\flutter\android\app\build.gradle.kts')) -and (-not (Test-Path 'build\flutter\android\app\build.gradle'))) {
        Write-Host ""
        Write-Host "    [ERROR] build/flutter n'a pas ete genere correctement." -ForegroundColor Red
        Read-Host "Appuyez sur Entree pour quitter"
        exit 1
    }
    Write-Host "    [OK] Template Flutter genere" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[5/6] Build 1/2: Template Flutter (skip - Fast mode)..." -ForegroundColor Gray
    if ((-not (Test-Path 'build\flutter\android\app\build.gradle.kts')) -and (-not (Test-Path 'build\flutter\android\app\build.gradle'))) {
        Write-Host "    [ERROR] Aucun template Flutter trouve. Lancez d'abord: .\build_android.ps1 -Scratch" -ForegroundColor Red
        Read-Host "Appuyez sur Entree pour quitter"
        exit 1
    }
    Write-Host "    [OK] Template Flutter existant reutilise" -ForegroundColor Green
}

# ============================================================================
# [NEW] 6. PATCH NOTIFICATIONS + BUILD FINAL
# Plus de copie manuelle de hayaati_alarm ici : l'extension est une
# dependance Python/Flutter normale, flet build apk la bundle tout seul,
# exactement comme flet-android-notifications.
# ============================================================================
Write-Host ""
Write-Host "[6/6] Patch notifications + Compilation APK..." -ForegroundColor Cyan

$patchOk = $true
try {
    flet-android-notifications-patch --project-root build/flutter
    $gf = 'build\flutter\android\app\build.gradle'
    if (Test-Path $gf) {
        $gc = Get-Content $gf -Raw
        if ($gc -match 'coreLibraryDesugaring') {
            Write-Host "    [OK] Patch applique (desugaring detecte)" -ForegroundColor Green
        } else {
            Write-Host "    [WARN] Patch peut-etre incomplet" -ForegroundColor Yellow
            $patchOk = $false
        }
    }
} catch {
    Write-Host "    [ERROR] Patch echoue: $_" -ForegroundColor Red
    $patchOk = $false
}

Write-Host ""
Write-Host "    Compilation finale APK..." -ForegroundColor Cyan
flet build apk -v
$buildExit = $LASTEXITCODE

if ($buildExit -ne 0) {
    Write-Host ""
    Write-Host "    [ERROR] flet build apk a echoue (code $buildExit)" -ForegroundColor Red
    Write-Host "    [INFO] Essayez: .\build_android.ps1 -Scratch" -ForegroundColor Yellow
    Read-Host "Appuyez sur Entree pour quitter"
    exit 1
}

# ============================================================================
# VERIFICATION APK
# ============================================================================
Write-Host ""
Write-Host "[VERIF] Verification du APK..." -ForegroundColor Yellow
$apkPaths = @(
    'build\flutter\build\app\outputs\flutter-apk\app-release.apk',
    'build\flutter\build\app\outputs\apk\release\app-release.apk',
    'build\app\outputs\flutter-apk\app-release.apk',
    'build\app\outputs\apk\release\app-release.apk'
)
$found = $false
foreach ($apk in $apkPaths) {
    if (Test-Path $apk) {
        $size = [math]::Round((Get-Item $apk).Length / 1MB, 1)
        Write-Host "    [OK] APK genere: $apk (${size} Mo)" -ForegroundColor Green
        $found = $true
        break
    }
}
if (-not $found) {
    $found2 = Get-ChildItem -Path 'build' -Filter '*.apk' -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found2) {
        $size = [math]::Round((Get-Item $found2.FullName).Length / 1MB, 1)
        Write-Host "    [OK] APK trouve: $($found2.FullName) (${size} Mo)" -ForegroundColor Green
        $found = $true
    } else {
        Write-Host "    [ERROR] Aucun APK trouve!" -ForegroundColor Red
    }
}

# ============================================================================
# BANNER FINAL
# ============================================================================
Write-Host ""
if ($found -and $patchOk -and $alarmExtensionOk -and $sonsOk) {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  BUILD TERMINE AVEC SUCCES!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} elseif ($found) {
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  BUILD TERMINE (avec avertissements)" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
} else {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  BUILD ECHOUE - APK non produit" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
}

# Rappel : aucun script ne peut automatiser ce reglage, il est manuel et
# specifique a chaque telephone.
Write-Host ""
Write-Host "[RAPPEL] Sur le telephone, apres installation :" -ForegroundColor Cyan
Write-Host "  Reglages > Apps > HAYAATI > Alarmes et rappels > Activer" -ForegroundColor Cyan
Write-Host "  Sans cette activation manuelle, l'alarme peut echouer silencieusement." -ForegroundColor Cyan
Write-Host ""

Read-Host "Appuyez sur Entree pour quitter"
