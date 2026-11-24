# Open ordinary Main on a spare copy. Persistent isolated profile. No capture script.
# Does not edit Play-Main.ps1 and does not change the execution policy.
param(
    [Parameter(Mandatory = $true)][string]$GodotExe,
    [Parameter(Mandatory = $true)][string]$ProjectDir,
    [switch]$Preview
)
$ErrorActionPreference = 'Stop'
$profile = 'vc27_draft_try'
if ($Preview) { $profile = 'vc27_draft_preview' }

function Assert-NotPlayer([string]$path) {
    if ($path -match 'vc27_play_36bfd') { throw "refusing a path that touches the player profile" }
}

if (-not [System.IO.Path]::IsPathRooted($ProjectDir)) { throw "ProjectDir must be an absolute path to the spare project" }
if (-not (Test-Path -LiteralPath $GodotExe)) {
    throw "Godot not found: $GodotExe. Pass -GodotExe. The earlier Windows notes used C:\Users\nasa2\hd2d_test\godot\Godot_v4.7.2-stable_win64.exe. This script does not search for or install Godot."
}
$projFull = [System.IO.Path]::GetFullPath($ProjectDir)
$godotFull = [System.IO.Path]::GetFullPath($GodotExe)
Assert-NotPlayer $projFull
Assert-NotPlayer $godotFull
$projFile = Join-Path $projFull 'project.godot'
if (-not (Test-Path -LiteralPath $projFile)) { throw "project.godot missing in ProjectDir" }

$cfg = Join-Path $projFull 'override.cfg'
if (Test-Path -LiteralPath $cfg) {
    throw "override.cfg already exists. This script will not change or delete it."
}

$utf8 = New-Object System.Text.UTF8Encoding $false
$cfgText = "[application]`r`nconfig/use_custom_user_dir=true`r`nconfig/custom_user_dir_name=`"$profile`"`r`n"
$script:wroteOverride = $false

function Remove-OwnOverride {
    if (-not $script:wroteOverride) { return }
    if (-not (Test-Path -LiteralPath $cfg)) { return }
    $current = [System.IO.File]::ReadAllText($cfg)
    if ($current -ne $cfgText) {
        Write-Output "override.cfg no longer matches the file this script wrote. Leaving it untouched."
        return
    }
    Remove-Item -LiteralPath $cfg -Force
    $script:wroteOverride = $false
}

Write-Output "Spare project: $projFull"
Write-Output "Isolated profile, kept across launches: $env:APPDATA\$profile"
Write-Output "This run does not read, write, or delete vc27_play_36bfd or vc27_draft_try unless that is the profile named above."
if ($Preview) {
    Write-Output "PREVIEW fixture profile. A new save is marked preview_fixture. An existing preview save is not reset."
    $env:VC27_DRAFT_PREVIEW = '1'
} else {
    Remove-Item Env:VC27_DRAFT_PREVIEW -ErrorAction SilentlyContinue
}
Write-Output "Renderer requested: mobile. No editor. No test script. The save is not wiped."
$code = 1
try {
    [System.IO.File]::WriteAllText($cfg, $cfgText, $utf8)
    $script:wroteOverride = $true
    $imp = Start-Process -FilePath $godotFull -ArgumentList @('--headless', '--rendering-method', 'mobile', '--path', $projFull, '--import', '--quit') -PassThru -Wait -NoNewWindow
    if ($imp.ExitCode -ne 0) { throw "import failed: $($imp.ExitCode)" }
    $proc = Start-Process -FilePath $godotFull -ArgumentList @('--rendering-method', 'mobile', '--path', $projFull) -PassThru -Wait
    if ($null -eq $proc.ExitCode) { $code = 0 } else { $code = $proc.ExitCode }
} finally {
    Remove-OwnOverride
    if ($Preview) { Remove-Item Env:VC27_DRAFT_PREVIEW -ErrorAction SilentlyContinue }
}
exit $code
