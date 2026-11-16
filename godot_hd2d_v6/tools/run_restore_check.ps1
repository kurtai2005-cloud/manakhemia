# Two Godot processes, isolated user dir, 540x1140 override.
# Usage:
#   .\tools\run_restore_check.ps1 -Godot "C:\Godot\Godot_v4.7.2-stable_win64.exe" -RenderingMethod mobile
param(
    [string]$Godot = "godot",
    [string]$RenderingMethod = "mobile"
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Profile = "vc27_care_restore_$PID"
$FakeNow = "1710000000000"
$Expect = Join-Path $Root "user_restore_expect.json"
$LogDir = Join-Path $env:TEMP "vc27_restore_$PID"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Override = Join-Path $Root "override.cfg"
try {
    @"
[display]
window/size/viewport_width=540
window/size/viewport_height=1140

[application]
config/use_custom_user_dir=true
config/custom_user_dir_name="$Profile"
"@ | Set-Content -Path $Override -Encoding ascii
    Write-Host "profile=$Profile"
    Write-Host "project=$Root"
    Write-Host "method=$RenderingMethod"
    $seedLog = Join-Path $LogDir "seed.log"
    $verifyLog = Join-Path $LogDir "verify.log"
    $env:HD2D_PROFILE_PHASE = "seed"
    $env:HD2D_PROFILE_NAME = $Profile
    $env:HD2D_FAKE_NOW_MS = $FakeNow
    $env:HD2D_EXPECT_FILE = $Expect
    $env:HD2D_MODE = "low"
    & $Godot --rendering-method $RenderingMethod --path $Root *> $seedLog
    $seed = $LASTEXITCODE
    Write-Host "seed_exit=$seed"
    if ($seed -ne 0) {
        Get-Content $seedLog
        exit $seed
    }
    $env:HD2D_PROFILE_PHASE = "verify"
    & $Godot --rendering-method $RenderingMethod --path $Root *> $verifyLog
    $verify = $LASTEXITCODE
    Write-Host "verify_exit=$verify"
    Write-Host "logs=$LogDir"
    Get-Content $seedLog
    Write-Host "-----"
    Get-Content $verifyLog
    exit $verify
}
finally {
    Remove-Item -Force -ErrorAction SilentlyContinue $Override
    Remove-Item -Force -ErrorAction SilentlyContinue $Expect
    Remove-Item Env:HD2D_PROFILE_PHASE -ErrorAction SilentlyContinue
    Remove-Item Env:HD2D_PROFILE_NAME -ErrorAction SilentlyContinue
    Remove-Item Env:HD2D_FAKE_NOW_MS -ErrorAction SilentlyContinue
    Remove-Item Env:HD2D_EXPECT_FILE -ErrorAction SilentlyContinue
    Remove-Item Env:HD2D_MODE -ErrorAction SilentlyContinue
}
