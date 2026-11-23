# Rendered capture for the current Main. Run from the project root.
# Does not use the player profile and does not pass ExecutionPolicy Bypass.
param(
    [Parameter(Mandatory = $true)][string]$GodotExe,
    [Parameter(Mandatory = $true)][string]$OutputDir
)
$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
$projFile = Join-Path $project 'project.godot'
if (-not (Test-Path -LiteralPath $projFile)) { throw "project.godot not found beside tools/" }
if (-not (Test-Path -LiteralPath $GodotExe)) { throw "Godot not found: $GodotExe" }
if (-not [System.IO.Path]::IsPathRooted($OutputDir)) { throw "OutputDir must be an absolute path" }
if (-not (Test-Path -LiteralPath $OutputDir)) { throw "OutputDir must already exist" }
$outFull = [System.IO.Path]::GetFullPath($OutputDir)
$projFull = [System.IO.Path]::GetFullPath($project)
if ($outFull.StartsWith($projFull, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "OutputDir must be outside the project"
}
if ($outFull -match 'vc27_play_36bfd') { throw "OutputDir must not touch the player profile" }
foreach ($rootName in @($env:APPDATA, $env:LOCALAPPDATA)) {
    if ([string]::IsNullOrEmpty($rootName)) { continue }
    $rootFull = [System.IO.Path]::GetFullPath($rootName)
    if ($outFull.StartsWith($rootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "OutputDir must be outside AppData"
    }
}
$existing = @(Get-ChildItem -LiteralPath $outFull -Force)
if ($existing.Count -ne 0) { throw "OutputDir must be empty" }
$cfg = Join-Path $project 'override.cfg'
if (Test-Path -LiteralPath $cfg) { throw "override.cfg already exists; capture will not replace it" }

function Set-CaptureProfile([string]$name) {
    $utf8 = New-Object System.Text.UTF8Encoding $false
    $text = "[application]`r`nconfig/use_custom_user_dir=true`r`nconfig/custom_user_dir_name=`"$name`"`r`n"
    [System.IO.File]::WriteAllText($cfg, $text, $utf8)
}

function Invoke-Capture([string]$stage, [string]$dest) {
    if (-not (Test-Path -LiteralPath $dest)) {
        New-Item -ItemType Directory -Path $dest | Out-Null
    }
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $GodotExe
    $psi.WorkingDirectory = $project
    $psi.UseShellExecute = $false
    $psi.Arguments = "--rendering-method mobile --path `"$project`" --script res://tests/hd2d_capture_harness.gd"
    $psi.EnvironmentVariables["CAPTURE_STAGE"] = $stage
    $psi.EnvironmentVariables["CAPTURE_OUT"] = $dest
    $psi.EnvironmentVariables["CAPTURE_PROJECT"] = $projFull
    $psi.EnvironmentVariables["CAPTURE_MAX_MS"] = "220000"
    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    [void]$proc.Start()
    if (-not $proc.WaitForExit(240000)) {
        try { $proc.Kill() } catch { }
        throw "timeout $stage"
    }
    if ($proc.ExitCode -ne 0) { throw "capture $stage exit $($proc.ExitCode)" }
}

Set-Location -LiteralPath $project
foreach ($name in @('vc27_errand_capture', 'vc27_progress_capture')) {
    $cap = Join-Path $env:APPDATA $name
    if (Test-Path -LiteralPath $cap) { Remove-Item -LiteralPath $cap -Recurse -Force }
}
try {
    Set-CaptureProfile 'vc27_errand_capture'
    $import = Start-Process -FilePath $GodotExe -ArgumentList @('--headless','--rendering-method','mobile','--path',$project,'--import','--quit') -Wait -PassThru -NoNewWindow
    if ($import.ExitCode -ne 0) { throw "import exit $($import.ExitCode)" }
    Invoke-Capture 'errand_out' (Join-Path $outFull 'errand')
    Invoke-Capture 'errand_resume' (Join-Path $outFull 'errand')
    Set-CaptureProfile 'vc27_progress_capture'
    Invoke-Capture 'progress' (Join-Path $outFull 'progress')
    Write-Output "CAPTURE_OK output=$outFull"
    exit 0
} catch {
    Write-Output $_.Exception.Message
    if ($_.Exception.Message -like 'timeout*') { exit 124 }
    exit 1
} finally {
    if (Test-Path -LiteralPath $cfg) { Remove-Item -LiteralPath $cfg -Force }
}
