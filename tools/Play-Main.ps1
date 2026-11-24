# Open the current game on the Mobile renderer. Isolated save. No test script, no auto-exit.
param(
    [Parameter(Mandatory = $true)][string]$GodotExe
)
$ErrorActionPreference = 'Stop'
$project = $PSScriptRoot
if (-not (Test-Path -LiteralPath $GodotExe)) { throw "Godot not found: $GodotExe" }
$proj = Join-Path $project 'project.godot'
if (-not (Test-Path -LiteralPath $proj)) { throw "project.godot missing beside this script" }
$profile = 'vc27_play_36bfd'
$cfg = Join-Path $project 'override.cfg'
$utf8 = New-Object System.Text.UTF8Encoding $false
$cfgText = "[application]`r`nconfig/use_custom_user_dir=true`r`nconfig/custom_user_dir_name=`"$profile`"`r`n"
[System.IO.File]::WriteAllText($cfg, $cfgText, $utf8)
$names = @('HD2D_COMPARE_FIXED','HD2D_COMPARE_GRAB','HD2D_COMPARE_OUT','HD2D_COMPARE_STEPS','HD2D_VP','HD2D_COMPARE_FULL','ROOM1_GRAB','ROOM1_CAPTURE','ROOM1_OUT','ROOM1_REQUIRE_ISOLATED')
$saved = @{}
foreach ($name in $names) {
    $saved[$name] = [Environment]::GetEnvironmentVariable($name)
    Remove-Item "Env:$name" -ErrorAction SilentlyContinue
}
Write-Output "Isolated profile: $env:APPDATA\$profile"
Write-Output "Default Godot project saves are not used."
Write-Output "Renderer requested: mobile"
Write-Output "Importing once, then Main stays open until you close the window."
try {
    $imp = Start-Process -FilePath $GodotExe -ArgumentList @('--headless','--rendering-method','mobile','--path',$project,'--import','--quit') -PassThru -Wait -NoNewWindow
    if ($imp.ExitCode -ne 0) { throw "import failed: $($imp.ExitCode)" }
    $proc = Start-Process -FilePath $GodotExe -ArgumentList @('--rendering-method','mobile','--path',$project) -PassThru -Wait
    if ($null -eq $proc.ExitCode) { exit 0 }
    exit $proc.ExitCode
} finally {
    foreach ($name in $names) {
        if ($null -eq $saved[$name]) { Remove-Item "Env:$name" -ErrorAction SilentlyContinue }
        else { Set-Item "Env:$name" $saved[$name] }
    }
    if (Test-Path -LiteralPath $cfg) { Remove-Item -LiteralPath $cfg -Force }
}
