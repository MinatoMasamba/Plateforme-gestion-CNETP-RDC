param([string]$Version = '1.0.0-beta.1+4')
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$release = Join-Path $root 'flutter_app/build/windows/x64/runner/Release'
$stage = Join-Path $root '.private_build/w'
$output = Join-Path $root 'external_redaction/releases'
if (!(Test-Path (Join-Path $release 'cnetp_app.exe'))) { throw 'Compilation Windows release absente.' }
New-Item -ItemType Directory -Force $stage, $output | Out-Null
$payload = Join-Path $stage "payload-$Version"
New-Item -ItemType Directory -Force $payload | Out-Null
Copy-Item -Path (Join-Path $release '*') -Destination $payload -Recurse -Force
$runtime = Get-ChildItem 'C:/Program Files/Microsoft Visual Studio/18/Community/VC/Redist/MSVC/*/x64/Microsoft.VC145.CRT' -Directory | Select-Object -First 1
if (!$runtime) { throw 'Bibliotheques redistribuables Visual C++ introuvables.' }
Copy-Item -Path (Join-Path $runtime.FullName '*.dll') -Destination $payload -Force
Compress-Archive -Path (Join-Path $payload '*') -DestinationPath (Join-Path $stage 'application.zip') -Force
@'
$ErrorActionPreference = 'Stop'
$target = Join-Path $env:LOCALAPPDATA 'CNE-ITP/Expert'
New-Item -ItemType Directory -Force $target | Out-Null
Expand-Archive -LiteralPath (Join-Path $PSScriptRoot 'application.zip') -DestinationPath $target -Force
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Programs')) 'CNE-ITP Expert.lnk'))
$shortcut.TargetPath = Join-Path $target 'cnetp_app.exe'
$shortcut.WorkingDirectory = $target
$shortcut.Save()
'@ | Set-Content -LiteralPath (Join-Path $stage 'install.ps1') -Encoding UTF8
'@powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "%~dp0install.ps1"' | Set-Content -LiteralPath (Join-Path $stage 'install.cmd') -Encoding Ascii
$destination = Join-Path $output "cne-itp-expert-$Version-windows-x64-setup.exe"
$temporaryInstaller = Join-Path $root '.private_build/setup.exe'
@"
[Version]
Class=IEXPRESS
SEDVersion=3
[Options]
PackagePurpose=InstallApp
ShowInstallProgramWindow=0
HideExtractAnimation=0
UseLongFileName=1
InsideCompressed=0
CAB_FixedSize=0
CAB_ResvCodeSigning=0
RebootMode=N
InstallPrompt=Installer CNE-ITP Expert pour votre compte Windows ?
DisplayLicense=
FinishMessage=Installation terminee. Ouvrez CNE-ITP Expert depuis le menu Demarrer.
TargetName=$temporaryInstaller
FriendlyName=CNE-ITP Expert $Version
AppLaunched=cmd.exe /c install.cmd
PostInstallCmd=<None>
AdminQuietInstCmd=cmd.exe /c install.cmd
UserQuietInstCmd=cmd.exe /c install.cmd
SourceFiles=SourceFiles
[Strings]
FILE0=application.zip
FILE1=install.ps1
FILE2=install.cmd
[SourceFiles]
SourceFiles0=$stage\
[SourceFiles0]
%FILE0%=
%FILE1%=
%FILE2%=
"@ | Set-Content -LiteralPath (Join-Path $stage 'installer.sed') -Encoding Ascii
$process = Start-Process -FilePath "$env:WINDIR/system32/iexpress.exe" -ArgumentList @('/N', '/Q', 'installer.sed') -WorkingDirectory $stage -WindowStyle Hidden -Wait -PassThru
if ($process.ExitCode -ne 0 -or !(Test-Path $temporaryInstaller)) { throw "Creation de l installateur impossible (code $($process.ExitCode))." }
Move-Item -LiteralPath $temporaryInstaller -Destination $destination -Force
$file = Get-Item -LiteralPath $destination
@{version=$Version; platform='windows'; architecture='x64'; file=$destination; bytes=$file.Length; sha256=(Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLower(); api_base_url='https://workalldomain.pythonanywhere.com'} | ConvertTo-Json | Set-Content -LiteralPath ($destination + '.json') -Encoding UTF8
Write-Output $destination
