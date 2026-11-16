# Isolated seed then a new verify process.
# Native Godot stderr is captured and logged. It does not stop this script.
# A missing executable, a nonzero Godot exit, or a line starting with "FAIL " fails the run.
# Windows PowerShell 5.1 and PowerShell 7 both use System.Diagnostics.Process.
# Usage:
#   .\tools\run_restore_check.ps1 -Godot "C:\path\Godot_v4.7.2-stable_win64.exe" -RenderingMethod mobile
param(
    [string]$Godot = "godot",
    [string]$RenderingMethod = "mobile"
)
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$ProfileName = "vc27_care_restore_$PID"
$FakeNow = "1710000000000"
$Expect = Join-Path $Root "user_restore_expect.json"
$LogDir = Join-Path $env:TEMP "vc27_restore_$PID"
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
    if (Test-Path -LiteralPath $Name) {
        return (Resolve-Path -LiteralPath $Name).Path
    }
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

function Join-Arguments {
    param([string[]]$Items)
    $out = New-Object System.Collections.Generic.List[string]
    foreach ($item in $Items) {
        if ($item -match '[\s"]') {
            $out.Add('"' + ($item -replace '"', '\"') + '"')
        } else {
            $out.Add($item)
        }
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
    $code = $proc.ExitCode
    if ($code -eq 0 -and ($text -match '(?m)^FAIL ')) {
        return 1
    }
    return $code
}

$exitCode = 0
try {
    @"
[display]
window/size/viewport_width=540
window/size/viewport_height=1140

[application]
config/use_custom_user_dir=true
config/custom_user_dir_name="$ProfileName"
"@ | Set-Content -LiteralPath $Override -Encoding ascii
    Write-Host "profile=$ProfileName"
    Write-Host "project=$Root"
    Write-Host "method=$RenderingMethod"
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
            $env:HD2D_PROFILE_NAME = $ProfileName
            $env:HD2D_FAKE_NOW_MS = $FakeNow
            $env:HD2D_EXPECT_FILE = $Expect
            $env:HD2D_MODE = "low"
            $seedLog = Join-Path $LogDir "seed.log"
            $env:HD2D_PROFILE_PHASE = "seed"
            $seedCode = Invoke-GodotLogged $godotPath @("--rendering-method", $RenderingMethod, "--path", $Root) $seedLog
            Write-Host "seed_exit=$seedCode"
            if ($seedCode -ne 0) {
                Get-Content -LiteralPath $seedLog
                $exitCode = $seedCode
            } else {
                $verifyLog = Join-Path $LogDir "verify.log"
                $env:HD2D_PROFILE_PHASE = "verify"
                $verifyCode = Invoke-GodotLogged $godotPath @("--rendering-method", $RenderingMethod, "--path", $Root) $verifyLog
                Write-Host "verify_exit=$verifyCode"
                Write-Host "logs=$LogDir"
                Get-Content -LiteralPath $seedLog
                Write-Host "-----"
                Get-Content -LiteralPath $verifyLog
                $exitCode = $verifyCode
            }
        }
    }
}
finally {
    if ($HadOverride) {
        [System.IO.File]::WriteAllText($Override, $SavedOverride)
    } elseif (Test-Path -LiteralPath $Override) {
        Remove-Item -LiteralPath $Override -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path -LiteralPath $Expect) {
        Remove-Item -LiteralPath $Expect -Force -ErrorAction SilentlyContinue
    }
    Remove-Item Env:HD2D_PROFILE_PHASE -ErrorAction SilentlyContinue
    Remove-Item Env:HD2D_PROFILE_NAME -ErrorAction SilentlyContinue
    Remove-Item Env:HD2D_FAKE_NOW_MS -ErrorAction SilentlyContinue
    Remove-Item Env:HD2D_EXPECT_FILE -ErrorAction SilentlyContinue
    Remove-Item Env:HD2D_MODE -ErrorAction SilentlyContinue
}
exit $exitCode
