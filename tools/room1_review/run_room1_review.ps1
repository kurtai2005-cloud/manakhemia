# Isolated room1 review capture for Godot 4.7.2 on Windows.
# Open scenes/room1_review.tscn in this folder to look. This script grabs four frames.
# It does not edit the project, the 675 tree, or the exterior candidate.
# Exit 0 only when all four PNGs decode as 1080x2280.
param(
    [Parameter(Mandatory = $true)][string]$GodotExe,
    [Parameter(Mandatory = $true)][string]$OutputDir
)
$ErrorActionPreference = 'Stop'
$OutputEncoding = New-Object System.Text.UTF8Encoding $false
$savedConsoleOut = [Console]::OutputEncoding
$savedConsoleIn = [Console]::InputEncoding
$savedOut = [Environment]::GetEnvironmentVariable('ROOM1_OUT')
$savedGrab = [Environment]::GetEnvironmentVariable('ROOM1_GRAB')
$savedCap = [Environment]::GetEnvironmentVariable('ROOM1_CAPTURE')
$savedIso = [Environment]::GetEnvironmentVariable('ROOM1_REQUIRE_ISOLATED')
$project = $PSScriptRoot
$outputAccepted = $false
$children = @()

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

function Stop-Owned([System.Diagnostics.Process]$Proc) {
    if ($null -eq $Proc) { return }
    $id = $Proc.Id
    $kids = @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$id" -ErrorAction SilentlyContinue)
    foreach ($kid in $kids) {
        Stop-Process -Id $kid.ProcessId -Force -ErrorAction SilentlyContinue
    }
    if (-not $Proc.HasExited) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }
}

function Save-Streams($Proc, $OutTask, $ErrTask, [string]$LogPath, [string]$ErrPath) {
    try { [void]$Proc.WaitForExit(15000) } catch {}
    foreach ($task in @($OutTask, $ErrTask)) {
        try { [void]$task.Wait(15000) } catch {}
    }
    $utf8 = New-Object System.Text.UTF8Encoding $false
    $outText = "stream was not readable after stop`r`n"
    $errText = "stream was not readable after stop`r`n"
    if ($OutTask.IsCompleted -and -not $OutTask.IsFaulted -and -not $OutTask.IsCanceled) { $outText = [string]$OutTask.Result }
    if ($ErrTask.IsCompleted -and -not $ErrTask.IsFaulted -and -not $ErrTask.IsCanceled) { $errText = [string]$ErrTask.Result }
    [System.IO.File]::WriteAllText($LogPath, $outText, $utf8)
    [System.IO.File]::WriteAllText($ErrPath, $errText, $utf8)
}

function Assert-Png1080([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { throw "missing PNG $Path" }
    $fs = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
    try {
        if ($fs.Length -lt 33) { throw "PNG too small $Path" }
        $buf = New-Object byte[] 24
        [void]$fs.Read($buf, 0, 24)
    } finally { $fs.Close() }
    $sig = @(0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A)
    for ($i = 0; $i -lt 8; $i++) {
        if ($buf[$i] -ne $sig[$i]) { throw "PNG signature failed $Path" }
    }
    $width = ($buf[16] -shl 24) -bor ($buf[17] -shl 16) -bor ($buf[18] -shl 8) -bor $buf[19]
    $height = ($buf[20] -shl 24) -bor ($buf[21] -shl 16) -bor ($buf[22] -shl 8) -bor $buf[23]
    if ($width -ne 1080 -or $height -ne 2280) { throw "PNG is ${width}x${height}, want 1080x2280: $Path" }
}

function Invoke-Godot([string]$Arguments, [string]$LogPath, [string]$ErrPath, [int]$TimeoutMs) {
    $utf8 = New-Object System.Text.UTF8Encoding $false
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $GodotExe
    $psi.WorkingDirectory = $project
    $psi.UseShellExecute = $false
    $psi.Arguments = $Arguments
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
    if (-not $proc.WaitForExit($TimeoutMs)) {
        Stop-Owned $proc
        Save-Streams $proc $outTask $errTask $LogPath $ErrPath
        throw "Godot timed out"
    }
    Save-Streams $proc $outTask $errTask $LogPath $ErrPath
    return $proc.ExitCode
}

try {
    Assert-FreshOutput $OutputDir
    $outputAccepted = $true
    if (-not (Test-Path -LiteralPath $GodotExe)) { throw "Godot not found: $GodotExe" }
    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
    $quoted = $project.Replace('"', '\"')
    $importCode = Invoke-Godot "--headless --path `"$quoted`" --import --quit" (Join-Path $OutputDir 'import.log') (Join-Path $OutputDir 'import.err.log') 1200000
    if ($importCode -ne 0) { throw "import failed: $importCode" }
    $profile = "room1_review_$PID"
    $cfg = Join-Path $project 'override.cfg'
    $utf8 = New-Object System.Text.UTF8Encoding $false
    $cfgText = "[application]`r`nconfig/use_custom_user_dir=true`r`nconfig/custom_user_dir_name=`"$profile`"`r`n"
    [System.IO.File]::WriteAllText($cfg, $cfgText, $utf8)
    $env:ROOM1_OUT = $OutputDir
    $env:ROOM1_GRAB = '1'
    $env:ROOM1_CAPTURE = '1'
    $env:ROOM1_REQUIRE_ISOLATED = '1'
    $runCode = Invoke-Godot "--path `"$quoted`" --rendering-method mobile --script res://scripts/room1_capture.gd" (Join-Path $OutputDir 'room1.log') (Join-Path $OutputDir 'room1.err.log') 1200000
    $names = @('day_fullroom.png', 'night_fullroom.png', 'day_closeup.png', 'night_closeup.png')
    $pngOk = $true
    $reasons = @()
    if ($runCode -ne 0) {
        $pngOk = $false
        $reasons += "godot exit $runCode"
    }
    foreach ($name in $names) {
        $png = Join-Path $OutputDir $name
        try { Assert-Png1080 $png } catch {
            $pngOk = $false
            $reasons += $_.Exception.Message
        }
    }
    $statePath = Join-Path $OutputDir 'room1_review_state.json'
    if (-not (Test-Path -LiteralPath $statePath)) {
        $pngOk = $false
        $reasons += 'state json missing'
    }
    $result = @{
        ok = $pngOk
        windows_review = $true
        mobile_acceptance = $false
        pixel_compared = $false
        integrated = $false
        pngs = $names
        reasons = $reasons
        godot_exit = $runCode
    } | ConvertTo-Json
    [System.IO.File]::WriteAllText((Join-Path $OutputDir 'result.json'), $result, $utf8)
    if (-not $pngOk) { throw "room1 review failed: $($reasons -join '; ')" }
    exit 0
} finally {
    if ($null -eq $savedOut) { Remove-Item Env:ROOM1_OUT -ErrorAction SilentlyContinue } else { $env:ROOM1_OUT = $savedOut }
    if ($null -eq $savedGrab) { Remove-Item Env:ROOM1_GRAB -ErrorAction SilentlyContinue } else { $env:ROOM1_GRAB = $savedGrab }
    if ($null -eq $savedCap) { Remove-Item Env:ROOM1_CAPTURE -ErrorAction SilentlyContinue } else { $env:ROOM1_CAPTURE = $savedCap }
    if ($null -eq $savedIso) { Remove-Item Env:ROOM1_REQUIRE_ISOLATED -ErrorAction SilentlyContinue } else { $env:ROOM1_REQUIRE_ISOLATED = $savedIso }
    [Console]::OutputEncoding = $savedConsoleOut
    [Console]::InputEncoding = $savedConsoleIn
    $cfg = Join-Path $project 'override.cfg'
    if ($outputAccepted -and (Test-Path -LiteralPath $cfg)) { Remove-Item -LiteralPath $cfg -Force }
}
