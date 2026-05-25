# Patch an installed Trustable MSIX in place by overwriting its launcher
# executable with ./Trustable-v0.3.7.exe (current directory). If that file
# is missing, fetch it from the public release URL first.
#
# WindowsApps install locations are TrustedInstaller-owned, so this script
# must run elevated (it takes ownership of the target file before copying).
#
# Invocation:
#   powershell.exe -ExecutionPolicy Bypass -File .\support\patch-v0.3.7.ps1

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Version     = 'v0.3.7'
$ExeName     = "Trustable-$Version.exe"
$PackageName = 'NuvolarisInc.Trustable'
$Source      = Join-Path (Get-Location).Path $ExeName
$DownloadUrl = "https://github.com/trustable-ai/.github/raw/main/$ExeName"

# 1. Look for ./Trustable-$VER.exe in the current directory; download if absent.
if (-not (Test-Path -LiteralPath $Source)) {
    Write-Host "Fetching $ExeName from $DownloadUrl"
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $Source -UseBasicParsing
} else {
    Write-Host "Using existing $Source"
}

# 2. If the launcher is currently running, terminate it — Windows holds
#    a file lock on the running .exe and the copy below would fail.
$ProcessName = "Trustable-$Version"
$running = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
if ($running) {
    Write-Host "Stopping running $ExeName (pid $($running.Id -join ', '))"
    $running | Stop-Process -Force
    $running | Wait-Process -ErrorAction SilentlyContinue
}

# 3. Locate the installed MSIX. The package identity name is unversioned
#    (see windows/spec.md "## Identity") so it survives across releases.
$pkg = Get-AppxPackage -Name $PackageName -ErrorAction SilentlyContinue
if (-not $pkg) {
    Write-Error "$PackageName is not installed; nothing to patch. Sideload the MSIX first."
    exit 1
}

$InstallLocation = $pkg.InstallLocation
$Target          = Join-Path $InstallLocation $ExeName

Write-Host "Install location: $InstallLocation"

if (-not (Test-Path -LiteralPath $Target)) {
    Write-Error "Target $Target not found. The installed package version may not match $Version."
    exit 1
}

# 4. WindowsApps ACLs deny write to everyone except TrustedInstaller. Take
#    ownership and grant Administrators full control on this single file.
& takeown.exe /F "$Target" | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Error "takeown.exe failed (exit $LASTEXITCODE). Re-run elevated (Run as Administrator)."
    exit 1
}
& icacls.exe "$Target" /grant "*S-1-5-32-544:F" | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Error "icacls.exe failed (exit $LASTEXITCODE)."
    exit 1
}

Write-Host "Copying $Source -> $Target"
Copy-Item -LiteralPath $Source -Destination $Target -Force

Write-Host "Patched $ExeName in $InstallLocation"
