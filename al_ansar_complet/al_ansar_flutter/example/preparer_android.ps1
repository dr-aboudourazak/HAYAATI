# Prépare le manifeste Android de l'application d'essai (une seule fois, relançable sans danger).
#   cd ...\al_ansar_flutter\example
#   powershell -ExecutionPolicy Bypass -File .\preparer_android.ps1
# Sans ces lignes, Android n'accorde aucune permission à l'application et le relevé GPS échoue
# (le module affiche alors : « permissions non déclarées dans le manifeste »).
$m = (Resolve-Path "android\app\src\main\AndroidManifest.xml").Path
$x = [System.IO.File]::ReadAllText($m)
if ($x -match "ACCESS_FINE_LOCATION") {
    Write-Host "Manifeste déjà préparé."
    exit 0
}
$ajout = '    <uses-permission android:name="android.permission.INTERNET"/>' + "`r`n" +
         '    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>' + "`r`n" +
         '    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION"/>' + "`r`n" +
         '    <queries>' + "`r`n" +
         '        <intent><action android:name="android.intent.action.VIEW"/><data android:scheme="https"/></intent>' + "`r`n" +
         '        <intent><action android:name="android.intent.action.VIEW"/><data android:scheme="geo"/></intent>' + "`r`n" +
         '    </queries>' + "`r`n"
$x = $x.Replace("<application", $ajout + "    <application")
$x = $x.Replace('android:label="al_ansar_example"', 'android:label="HAYAATI"')
[System.IO.File]::WriteAllText($m, $x, (New-Object System.Text.UTF8Encoding($false)))
Write-Host "Manifeste préparé : permissions de localisation et d'Internet ajoutées. Relancez : flutter run -d <identifiant>"
