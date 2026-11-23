# Windowed play capture, or the narrow headless wake check.
# Run from the project folder. Does not use the player profile.
# Does not change the execution policy.
param(
    [Parameter(Mandatory = $true)][string]$GodotExe,
    [Parameter(Mandatory = $true)][string]$OutputDir,
    [ValidateSet('Picture', 'Wake', 'Motion')]
    [string]$Mode = 'Picture'
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
$godotFull = [System.IO.Path]::GetFullPath($GodotExe)

function Assert-NotPlayer([string]$path) {
    if ($path -match 'vc27_play_36bfd') { throw "refusing a path that touches the player profile" }
}
Assert-NotPlayer $outFull
Assert-NotPlayer $projFull
Assert-NotPlayer $godotFull
if ($outFull.StartsWith($projFull, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "OutputDir must be outside the project"
}
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
if (Test-Path -LiteralPath $cfg) {
    throw "override.cfg already exists. Close Play-Main normally first. This script will not delete that file."
}
$script:wroteOverride = $false

if ($Mode -eq 'Wake') {
    $profile = 'vc27_rest_wake'
    $scriptPath = 'res://tests/hd2d_rest_wake.gd'
    $headless = $true
    $timeoutMs = 120000
} elseif ($Mode -eq 'Motion') {
    $profile = 'vc27_motion_capture'
    $scriptPath = 'res://tests/hd2d_motion_capture.gd'
    $headless = $false
    $timeoutMs = 420000
} else {
    $profile = 'vc27_play_usable'
    $scriptPath = 'res://tests/hd2d_play_usable.gd'
    $headless = $false
    $timeoutMs = 480000
}
if ($profile -ne 'vc27_play_usable' -and $profile -ne 'vc27_rest_wake' -and $profile -ne 'vc27_motion_capture') {
    throw "refusing profile $profile"
}

function Clear-IsolatedProfile([string]$name) {
    if ($name -ne 'vc27_play_usable' -and $name -ne 'vc27_rest_wake' -and $name -ne 'vc27_motion_capture') { throw "refusing profile $name" }
    $roots = @()
    if (-not [string]::IsNullOrEmpty($env:APPDATA)) {
        $roots += (Join-Path $env:APPDATA $name)
        $roots += (Join-Path (Join-Path $env:APPDATA 'Godot\app_userdata') $name)
    }
    foreach ($cap in $roots) {
        Assert-NotPlayer $cap
        if (Test-Path -LiteralPath $cap) { Remove-Item -LiteralPath $cap -Recurse -Force }
    }
}

function Set-IsolatedProfile([string]$name) {
    $utf8 = New-Object System.Text.UTF8Encoding $false
    $text = "[application]`r`nconfig/use_custom_user_dir=true`r`nconfig/custom_user_dir_name=`"$name`"`r`n"
    [System.IO.File]::WriteAllText($cfg, $text, $utf8)
    $script:wroteOverride = $true
}

$script:wantMp4 = $false
if ($Mode -eq 'Motion') {
    $ffmpegPre = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if ($ffmpegPre) {
        $script:wantMp4 = $true
        Write-Output "PREFLIGHT ffmpeg=$($ffmpegPre.Source). After the capture this run will also write motion.mp4."
    } else {
        Write-Output "PREFLIGHT ffmpeg is not on PATH. No install will be attempted. Success is frames\f_####.jpg plus trace.jsonl and result.json. motion.mp4 will not be created."
    }
}
Set-Location -LiteralPath $project
$logDir = Join-Path $outFull 'logs'
New-Item -ItemType Directory -Path $logDir | Out-Null
$stdoutPath = Join-Path $logDir 'stdout.txt'
$stderrPath = Join-Path $logDir 'stderr.txt'
$exitPath = Join-Path $logDir 'exit_code.txt'
$code = 1
try {
    Clear-IsolatedProfile $profile
    Set-IsolatedProfile $profile
    $args = "--rendering-method mobile --path `"$project`" --script $scriptPath"
    if ($headless) { $args = "--headless $args" }
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $GodotExe
    $psi.WorkingDirectory = $project
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $headless
    $psi.Arguments = $args
    if ($Mode -eq 'Motion') {
        $psi.EnvironmentVariables["VC27_MOTION_OUT"] = $outFull
    } elseif (-not $headless) {
        $psi.EnvironmentVariables["VC27_USABLE_OUT"] = $outFull
    }
    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    [void]$proc.Start()
    $outTask = $proc.StandardOutput.ReadToEndAsync()
    $errTask = $proc.StandardError.ReadToEndAsync()
    $finished = $proc.WaitForExit($timeoutMs)
    if (-not $finished) {
        try { $proc.Kill() } catch { }
        try { [void]$proc.WaitForExit(10000) } catch { }
        $code = 124
    } else {
        $code = $proc.ExitCode
    }
    try { [void]$outTask.Wait(10000) } catch { }
    try { [void]$errTask.Wait(10000) } catch { }
    $utf8 = New-Object System.Text.UTF8Encoding $false
    $outText = ''
    $errText = ''
    if ($outTask.IsCompleted) { $outText = [string]$outTask.Result }
    if ($errTask.IsCompleted) { $errText = [string]$errTask.Result }
    [System.IO.File]::WriteAllText($stdoutPath, $outText, $utf8)
    [System.IO.File]::WriteAllText($stderrPath, $errText, $utf8)
    [System.IO.File]::WriteAllText($exitPath, "$code`r`n", $utf8)
    if ($code -eq 124) { throw "timeout $Mode" }
    if ($Mode -eq 'Picture' -and $code -eq 0) {
        $trace = Join-Path $outFull 'trace.jsonl'
        $result = Join-Path $outFull 'result.json'
        $pngs = @(Get-ChildItem -LiteralPath $outFull -Filter '*.png' -File)
        if (-not (Test-Path -LiteralPath $trace) -or -not (Test-Path -LiteralPath $result) -or $pngs.Count -lt 1) {
            $code = 1
            [System.IO.File]::WriteAllText($exitPath, "$code`r`n", $utf8)
            throw "expected png, trace.jsonl, and result.json"
        }
        Write-Output "PLAY_USABLE_CAPTURE mode=Picture exit=$code pngs=$($pngs.Count) output=$outFull"
        Write-Output "Picture run is window input plus fixture hunger and energy. It is not a full manual pass."
    } elseif ($Mode -eq 'Wake' -and $code -eq 0) {
        if ($outText -notmatch 'REST_WAKE_OK') {
            $code = 1
            [System.IO.File]::WriteAllText($exitPath, "$code`r`n", $utf8)
            throw "wake stdout missing REST_WAKE_OK"
        }
        Write-Output "PLAY_USABLE_CAPTURE mode=Wake exit=$code output=$outFull"
        Write-Output "SYNTHETIC. enter_house and the energy write are fixture setup. Not a manual play pass."
    } elseif ($Mode -eq 'Motion' -and $code -eq 0) {
        $trace = Join-Path $outFull 'trace.jsonl'
        $result = Join-Path $outFull 'result.json'
        $clip = Join-Path $outFull 'motion.mp4'
        $frames = Join-Path $outFull 'frames'
        if (-not (Test-Path -LiteralPath $trace) -or -not (Test-Path -LiteralPath $result) -or -not (Test-Path -LiteralPath $frames)) {
            $code = 1
            [System.IO.File]::WriteAllText($exitPath, "$code`r`n", $utf8)
            throw "expected frames, trace.jsonl, and result.json"
        }
        $jpgs = @(Get-ChildItem -LiteralPath $frames -Filter 'f_*.jpg' -File)
        if ($jpgs.Count -lt 8) {
            $code = 1
            [System.IO.File]::WriteAllText($exitPath, "$code`r`n", $utf8)
            throw "too few frames"
        }
        if ($script:wantMp4) {
            $ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
            & $ffmpeg.Source -y -framerate 8 -i (Join-Path $frames 'f_%04d.jpg') -c:v libx264 -pix_fmt yuv420p -crf 26 $clip
            if (-not (Test-Path -LiteralPath $clip)) {
                $code = 1
                [System.IO.File]::WriteAllText($exitPath, "$code`r`n", $utf8)
                throw "ffmpeg did not write motion.mp4"
            }
            Write-Output "PLAY_USABLE_CAPTURE mode=Motion evidence=mp4 exit=$code frames=$($jpgs.Count) output=$outFull"
        } else {
            Write-Output "PLAY_USABLE_CAPTURE mode=Motion evidence=frames exit=$code frames=$($jpgs.Count) output=$outFull"
        }
        Write-Output "Playback 8 fps is a review rate. Care holds repeat the same game frame. Not wall-clock realtime. Not an RTX or phone pass."
    } else {
        throw "godot exit $code"
    }
    exit 0
} catch {
    Write-Output $_.Exception.Message
    if (-not (Test-Path -LiteralPath $exitPath)) {
        $utf8b = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($exitPath, "$code`r`n", $utf8b)
    }
    if ($_.Exception.Message -like 'timeout*') { exit 124 }
    exit 1
} finally {
    if ($script:wroteOverride -and (Test-Path -LiteralPath $cfg)) {
        Remove-Item -LiteralPath $cfg -Force
    }
}
