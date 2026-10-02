# Jura-Kreuzwortbuch: Seiten erzeugen.  Aufruf im Paketordner:
#   .\start_kreuzwort.ps1 1 50          Seiten 1 bis 50 (setzt nach Abbruch fort)
#   .\start_kreuzwort.ps1 7 7 100       Seite 7 mit Seed-Versatz 100 neu bauen
param([int]$Von = 1, [int]$Bis = 50, [int]$Versatz = 0)
$env:PYTHONUTF8 = 1
if ($Versatz -gt 0) { $env:SEED_VERSATZ = $Versatz }
Set-Location $PSScriptRoot
python -u kr_book.py $Von $Bis 2>&1 | Tee-Object -FilePath kr_lauf.txt -Append
