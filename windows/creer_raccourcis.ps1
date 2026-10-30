# Cree les raccourcis "Apollo Car" (ouvrir) et "Apollo Car - Arreter" sur le Bureau,
# ainsi qu'un raccourci "Apollo Car" dans le menu Demarrer.
# Usage : powershell -ExecutionPolicy Bypass -File windows\creer_raccourcis.ps1 [-Destination <dossier>] [-SansMenuDemarrer]
param(
    [string]$Destination = [Environment]::GetFolderPath('Desktop'),
    [string]$Nom = 'Apollo Car',
    [switch]$SansMenuDemarrer
)

$ErrorActionPreference = 'Stop'
$appDir = Split-Path -Parent $PSScriptRoot
$wscript = Join-Path $env:WINDIR 'System32\wscript.exe'
$icon = Join-Path $PSScriptRoot 'apollo.ico'
$shell = New-Object -ComObject WScript.Shell

function New-AppShortcut($folder, $fileName, $script, $description) {
    $link = $shell.CreateShortcut((Join-Path $folder $fileName))
    $link.TargetPath = $wscript
    $link.Arguments = '"' + (Join-Path $PSScriptRoot $script) + '"'
    $link.WorkingDirectory = $appDir
    $link.IconLocation = "$icon,0"
    $link.Description = $description
    $link.Save()
}

New-AppShortcut $Destination "$Nom.lnk" 'lancer.vbs' "Ouvrir l'application de gestion de location"
New-AppShortcut $Destination "$Nom - Arreter.lnk" 'arreter.vbs' "Arreter l'application de gestion de location"
if (-not $SansMenuDemarrer) {
    New-AppShortcut ([Environment]::GetFolderPath('Programs')) "$Nom.lnk" 'lancer.vbs' "Ouvrir l'application de gestion de location"
}
Write-Host "Raccourcis crees dans : $Destination"
