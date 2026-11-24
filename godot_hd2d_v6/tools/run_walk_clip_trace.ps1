# r4 evidence fixture. Isolated profile. Does not touch the normal save.
# Without -Movie this is the windowed run. A clamped 1080x1410 window is logged
# separately and is not a 1080x2280 movie-close pass.
# -Movie writes a PNG sequence. The temporary override sets stretch mode viewport
# so the recorded texture is the 1080x2280 viewport. The override is removed on exit.
# project.godot and the camera policy are not changed. Do not pass --display-driver.
# PNG suffix N equals Engine.get_frames_drawn() sampled in _process before that
# frame is drawn, when every loop draws once. select_png_index on stop_end is that N.
# The next leg is armed only after a later drawn frame. process_frames is not a movie frame.
# Usage:
#   .\tools\run_walk_clip_trace.ps1 -Godot "C:\path\Godot_v4.7.2-stable_win64.exe" -RenderingMethod mobile
#   .\tools\run_walk_clip_trace.ps1 -Godot "C:\path\Godot_v4.7.2-stable_win64.exe" -RenderingMethod mobile -Movie "C:\temp\vc27_walkclip.png"
param(
    [string]$Godot = "godot",
    [string]$RenderingMethod = "mobile",
    [string]$Movie = ""
)
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$ProfileName = "vc27_walkclip_$PID"
$LogDir = Join-Path $env:TEMP "vc27_walkclip_$PID"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Override = Join-Path $Root "override.cfg"
$SavedOverride = $null
$HadOverride = $false
if (Test-Path -LiteralPath $Override) {
    $SavedOverride = [System.IO.File]::ReadAllText($Override)
    $HadOverride = $true
}

function Resolve-GodotPath {
    param([string]$Name)
    if (Test-Path -LiteralPath $Name) { return (Resolve-Path -LiteralPath $Name).Path }
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}
function Join-Arguments {
    param([string[]]$Items)
    $out = New-Object System.Collections.Generic.List[string]
    foreach ($item in $Items) {
        if ($item -match '[\s"]') { $out.Add('"' + ($item -replace '"', '\"') + '"') } else { $out.Add($item) }
    }
    return ($out -join ' ')
}
function Invoke-GodotLogged {
    param([string]$FilePath, [string[]]$ArgumentList, [string]$LogPath)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    $psi.Arguments = Join-Arguments $ArgumentList
    $psi.WorkingDirectory = $Root
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    try {
        if (-not $proc.Start()) {
            [System.IO.File]::WriteAllText($LogPath, "FAIL launch: Start returned false`r`n")
            return 127
        }
    } catch {
        [System.IO.File]::WriteAllText($LogPath, ("FAIL launch: " + $_.Exception.Message + "`r`n"))
        return 127
    }
    $outTask = $proc.StandardOutput.ReadToEndAsync()
    $errTask = $proc.StandardError.ReadToEndAsync()
    $proc.WaitForExit()
    $outTask.Wait()
    $errTask.Wait()
    $text = $outTask.Result
    if ($errTask.Result) {
        $text += "`r`n# stderr logged only; warnings are not script failures`r`n"
        $text += $errTask.Result
    }
    [System.IO.File]::WriteAllText($LogPath, $text)
    if ($proc.ExitCode -eq 0 -and ($text -match '(?m)^FAIL ')) { return 1 }
    return $proc.ExitCode
}

$exitCode = 0
try {
    $stretch = ""
    if ($Movie -ne "") { $stretch = "window/stretch/mode=`"viewport`"" }
    @"
[display]
window/size/viewport_width=1080
window/size/viewport_height=2280
$stretch

[application]
config/use_custom_user_dir=true
config/custom_user_dir_name="$ProfileName"
"@ | Set-Content -LiteralPath $Override -Encoding ascii
    Write-Host "movie=$Movie"
    $godotPath = Resolve-GodotPath $Godot
    if (-not $godotPath) {
        Write-Host "FAIL launch: Godot not found: $Godot"
        $exitCode = 127
    } else {
        $importLog = Join-Path $LogDir "import.log"
        $importCode = Invoke-GodotLogged $godotPath @("--headless", "--import", "--path", $Root) $importLog
        Write-Host "import_exit=$importCode"
        if ($importCode -ne 0) {
            Get-Content -LiteralPath $importLog
            $exitCode = $importCode
        } else {
            $env:HD2D_PROFILE_PHASE = "walkclip"
            $env:HD2D_PROFILE_NAME = $ProfileName
            $env:HD2D_MODE = "low"
            $walkLog = Join-Path $LogDir "walkclip.log"
            $godotArgs = @("--rendering-method", $RenderingMethod, "--path", $Root)
            if ($Movie -ne "") { $godotArgs = @("--rendering-method", $RenderingMethod, "--write-movie", $Movie, "--path", $Root) }
            $code = Invoke-GodotLogged $godotPath $godotArgs $walkLog
            Write-Host "walkclip_exit=$code"
            Write-Host "logs=$LogDir"
            Get-Content -LiteralPath $walkLog
            $exitCode = $code
        }
    }
}
finally {
    if ($HadOverride) { [System.IO.File]::WriteAllText($Override, $SavedOverride) }
    elseif (Test-Path -LiteralPath $Override) { Remove-Item -LiteralPath $Override -Force -ErrorAction SilentlyContinue }
    Remove-Item Env:HD2D_PROFILE_PHASE -ErrorAction SilentlyContinue
    Remove-Item Env:HD2D_PROFILE_NAME -ErrorAction SilentlyContinue
    Remove-Item Env:HD2D_MODE -ErrorAction SilentlyContinue
}
exit $exitCode
