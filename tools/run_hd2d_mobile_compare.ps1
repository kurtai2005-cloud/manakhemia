# Displayed Mobile comparison for Windows. Does not use bash.
# Exit 0 only when both PNGs decode as 1080x2280 and the state records match.
# This script does not run on the Linux review VM. A run here is the GPU proof.
param(
    [Parameter(Mandatory = $true)][string]$GodotExe,
    [Parameter(Mandatory = $true)][string]$Python,
    [Parameter(Mandatory = $true)][string]$Baseline675,
    [Parameter(Mandatory = $true)][string]$DeltaPath,
    [Parameter(Mandatory = $true)][string]$OutputDir,
    [string]$DeltaSha = ""
)
$ErrorActionPreference = 'Stop'
$OutputEncoding = New-Object System.Text.UTF8Encoding $false
$savedConsoleOut = [Console]::OutputEncoding
$savedConsoleIn = [Console]::InputEncoding
$savedPyIO = [Environment]::GetEnvironmentVariable('PYTHONIOENCODING')
$savedPyUtf = [Environment]::GetEnvironmentVariable('PYTHONUTF8')
$envNames = @(
    'HD2D_COMPARE_OUT', 'HD2D_COMPARE_FIXED', 'HD2D_COMPARE_FULL',
    'HD2D_COMPARE_STEPS', 'HD2D_COMPARE_GRAB', 'HD2D_COMPARE_DISPLAY',
    'HD2D_MODE', 'HD2D_VP', 'HD2D_COMPARE_HEADLESS'
)
$savedEnv = @{}
foreach ($name in $envNames) { $savedEnv[$name] = [Environment]::GetEnvironmentVariable($name) }
$children = @()
$outputAccepted = $false
$work = Join-Path $OutputDir 'work'
$pilot = Join-Path $OutputDir 'pilot_project'

function Assert-FreshOutput([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) { throw "OutputDir is required" }
    if (-not (Test-Path -LiteralPath $Path)) { return }
    $item = Get-Item -LiteralPath $Path -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw "OutputDir is not an empty directory: $Path"
    }
    if (-not $item.PSIsContainer) { throw "OutputDir is not an empty directory: $Path" }
    $existing = @(Get-ChildItem -LiteralPath $Path -Force | Select-Object -First 1)
    if ($existing.Count -gt 0) {
        throw "OutputDir is not empty; refusing to delete or reuse $Path"
    }
}

function Restore-Env {
    [Console]::OutputEncoding = $savedConsoleOut
    [Console]::InputEncoding = $savedConsoleIn
    if ($null -eq $savedPyIO) { Remove-Item Env:PYTHONIOENCODING -ErrorAction SilentlyContinue } else { $env:PYTHONIOENCODING = $savedPyIO }
    if ($null -eq $savedPyUtf) { Remove-Item Env:PYTHONUTF8 -ErrorAction SilentlyContinue } else { $env:PYTHONUTF8 = $savedPyUtf }
    foreach ($name in $envNames) {
        if ($null -eq $savedEnv[$name]) { Remove-Item "Env:$name" -ErrorAction SilentlyContinue }
        else { Set-Item "Env:$name" $savedEnv[$name] }
    }
}

function Stop-Owned([System.Diagnostics.Process]$Proc) {
    if ($null -eq $Proc) { return }
    $id = $Proc.Id
    $kids = @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$id" -ErrorAction SilentlyContinue)
    foreach ($kid in $kids) {
        Stop-Process -Id $kid.ProcessId -Force -ErrorAction SilentlyContinue
    }
    if (-not $Proc.HasExited) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }
}

function Write-Override([string]$Project, [string]$Profile) {
    $cfg = Join-Path $Project 'override.cfg'
    $cfgText = @"
[application]
config/use_custom_user_dir=true
config/custom_user_dir_name="$Profile"
"@
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($cfg, ($cfgText -replace "(?<!`r)`n", "`r`n"), $utf8)
}

function Import-Project([string]$Project, [string]$LogPath, [string]$ErrPath) {
    # Asset import only. This is not the displayed comparison and it does not grab.
    $utf8 = New-Object System.Text.UTF8Encoding $false
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $GodotExe
    $psi.WorkingDirectory = $Project
    $psi.UseShellExecute = $false
    $quoted = $Project.Replace('"', '\"')
    $psi.Arguments = "--headless --path `"$quoted`" --import --quit"
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = $utf8
    $psi.StandardErrorEncoding = $utf8
    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    [void]$proc.Start()
    $script:children += $proc
    $outTask = $proc.StandardOutput.ReadToEndAsync()
    $errTask = $proc.StandardError.ReadToEndAsync()
    if (-not $proc.WaitForExit(1200000)) {
        Stop-Owned $proc
        throw "Godot import timed out: $Project"
    }
    $proc.WaitForExit()
    [System.IO.File]::WriteAllText($LogPath, $outTask.Result, $utf8)
    [System.IO.File]::WriteAllText($ErrPath, $errTask.Result, $utf8)
    if ($proc.ExitCode -ne 0) { throw "Godot import failed: $Project ($($proc.ExitCode))" }
}

function Start-Godot([string]$Project, [string]$Script, [string]$LogPath, [string]$ErrPath, [string]$Profile) {
    Write-Override $Project $Profile
    $utf8 = New-Object System.Text.UTF8Encoding $false
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $GodotExe
    $psi.WorkingDirectory = $Project
    $psi.UseShellExecute = $false
    $quoted = $Project.Replace('"', '\"')
    $psi.Arguments = "--path `"$quoted`" --rendering-method mobile --script $Script"
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = $utf8
    $psi.StandardErrorEncoding = $utf8
    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    [void]$proc.Start()
    $script:children += $proc
    $outTask = $proc.StandardOutput.ReadToEndAsync()
    $errTask = $proc.StandardError.ReadToEndAsync()
    if (-not $proc.WaitForExit(1200000)) {
        Stop-Owned $proc
        throw "Godot timed out: $Project"
    }
    $proc.WaitForExit()
    [System.IO.File]::WriteAllText($LogPath, $outTask.Result, $utf8)
    [System.IO.File]::WriteAllText($ErrPath, $errTask.Result, $utf8)
    return $proc.ExitCode
}

try {
    Assert-FreshOutput $OutputDir
    $outputAccepted = $true
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false
    [Console]::InputEncoding = New-Object System.Text.UTF8Encoding $false
    $env:PYTHONIOENCODING = 'utf-8'
    $env:PYTHONUTF8 = '1'
    if (-not (Test-Path -LiteralPath $GodotExe)) { throw "Godot not found: $GodotExe" }
    if (-not (Test-Path -LiteralPath $Python)) { throw "Python not found: $Python" }
    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
    $prepareArgs = @(
        (Join-Path $PSScriptRoot 'hd2d_evidence.py'),
        'prepare', '--baseline', $Baseline675, '--delta', $DeltaPath, '--work', $work, '--pilot', $pilot
    )
    if (-not [string]::IsNullOrWhiteSpace($DeltaSha)) { $prepareArgs += @('--delta-sha', $DeltaSha) }
    & $Python @prepareArgs
    if ($LASTEXITCODE -ne 0) { throw "prepare failed: $LASTEXITCODE" }
    $launch = @{
        displayed = $true
        headless = $false
        os = 'windows'
        rendering_method = 'mobile'
        viewport = @(1080, 2280)
        godot = $GodotExe
        baseline = $Baseline675
        delta = $DeltaPath
    } | ConvertTo-Json
    [System.IO.File]::WriteAllText((Join-Path $OutputDir 'launch.json'), $launch, (New-Object System.Text.UTF8Encoding $false))
    $env:HD2D_COMPARE_OUT = $OutputDir
    $env:HD2D_COMPARE_FIXED = '1'
    $env:HD2D_COMPARE_FULL = '1'
    $env:HD2D_COMPARE_STEPS = '20'
    $env:HD2D_COMPARE_GRAB = '1'
    $env:HD2D_COMPARE_DISPLAY = '1'
    $env:HD2D_MODE = 'low'
    $env:HD2D_VP = '1080x2280'
    Remove-Item Env:HD2D_COMPARE_HEADLESS -ErrorAction SilentlyContinue
    & $Python (Join-Path $work 'tools\stage_hd2d_assets.py')
    if ($LASTEXITCODE -ne 0) { throw "stage failed" }
    $pilotProfile = "vc27_root_adapter_pilot_$PID"
    $rootProfile = "vc27_root_adapter_root_$PID"
    Write-Override $pilot $pilotProfile
    Import-Project $pilot (Join-Path $OutputDir 'pilot.import.log') (Join-Path $OutputDir 'pilot.import.err.log')
    Write-Override $work $rootProfile
    Import-Project $work (Join-Path $OutputDir 'root.import.log') (Join-Path $OutputDir 'root.import.err.log')
    $pilotCode = Start-Godot $pilot 'res://hd2d_pilot_compare_main.gd' (Join-Path $OutputDir 'pilot.log') (Join-Path $OutputDir 'pilot.err.log') $pilotProfile
    $rootCode = Start-Godot $work 'res://tests/hd2d_same_view.gd' (Join-Path $OutputDir 'root.log') (Join-Path $OutputDir 'root.err.log') $rootProfile
    & $Python (Join-Path $PSScriptRoot 'hd2d_evidence.py') check --out $OutputDir --launch (Join-Path $OutputDir 'launch.json')
    $check = $LASTEXITCODE
    if ($pilotCode -ne 0 -or $rootCode -ne 0 -or $check -ne 0) { exit 1 }
    exit 0
}
finally {
    foreach ($proc in $children) { Stop-Owned $proc }
    if ($outputAccepted) {
        foreach ($cfg in @((Join-Path $work 'override.cfg'), (Join-Path $pilot 'override.cfg'))) {
            if (Test-Path -LiteralPath $cfg) { Remove-Item -LiteralPath $cfg -Force -ErrorAction SilentlyContinue }
        }
    }
    Restore-Env
}
