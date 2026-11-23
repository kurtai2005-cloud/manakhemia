# Read-only window census for one already-running Godot process.
# Does not launch the game, does not send WM_CLOSE, does not read saves.
# Optional -IncludeBareWindow starts a separate empty project in its own profile.
param(
    [Parameter(Mandatory = $true)][int]$GamePid,
    [int]$WrapperPid = 0,
    [Parameter(Mandatory = $true)][string]$OutputDir,
    [string]$GodotExe = '',
    [switch]$IncludeBareWindow
)
$ErrorActionPreference = 'Stop'
$started = Get-Date
if ([string]::IsNullOrWhiteSpace($OutputDir)) { throw 'OutputDir is required' }
if (Test-Path -LiteralPath $OutputDir) {
    $item = Get-Item -LiteralPath $OutputDir -Force
    if (-not $item.PSIsContainer) { throw "OutputDir is not a directory: $OutputDir" }
    $existing = @(Get-ChildItem -LiteralPath $OutputDir -Force | Select-Object -First 1)
    if ($existing.Count -gt 0) { throw "OutputDir is not empty: $OutputDir" }
} else {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}
$gameRoot = 'C:\Users\nasa2\hd2d_test\vc27_play_main_2092'
$saveHint = 'C:\Users\nasa2\AppData\Roaming\vc27_play_36bfd'
if ($OutputDir.TrimEnd('\') -eq $gameRoot -or $OutputDir.TrimEnd('\') -eq $saveHint) {
    throw 'OutputDir must not be the game folder or the play profile'
}

Add-Type -TypeDefinition @"
using System;
using System.Text;
using System.Runtime.InteropServices;
using System.Collections.Generic;
public class Vc27Win {
    public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr lp);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool IsHungAppWindow(IntPtr hWnd);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr hWnd, StringBuilder s, int n);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr hWnd, StringBuilder s, int n);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT r);
    [DllImport("user32.dll")] public static extern IntPtr GetParent(IntPtr hWnd);
    [DllImport("user32.dll", EntryPoint="SendMessageTimeoutW")] public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam, uint flags, uint timeout, out IntPtr result);
    public struct RECT { public int Left, Top, Right, Bottom; }
    public static List<IntPtr> Tops() {
        List<IntPtr> found = new List<IntPtr>();
        EnumWindows(delegate(IntPtr h, IntPtr l) { found.Add(h); return true; }, IntPtr.Zero);
        return found;
    }
}
"@

function Text-Of([IntPtr]$h) {
    $b = New-Object System.Text.StringBuilder 512
    [void][Vc27Win]::GetWindowText($h, $b, $b.Capacity)
    return $b.ToString()
}
function Class-Of([IntPtr]$h) {
    $b = New-Object System.Text.StringBuilder 256
    [void][Vc27Win]::GetClassName($h, $b, $b.Capacity)
    return $b.ToString()
}

$collector = Get-Process -Id $PID
$note = New-Object System.Collections.Generic.List[string]
$note.Add('Read-only. No WM_CLOSE. No save read. No full-game launch.')
$note.Add('SendMessageTimeout is WM_NULL, 500 ms, SMTO_ABORTIFHUNG. A timeout is a measurement, not a repair.')
$note.Add('inputs=0 in the game log was required by the no-click protocol. This script does not click.')

$game = $null
$wrap = $null
try { $game = Get-Process -Id $GamePid -ErrorAction Stop } catch { $note.Add("Game PID $GamePid is not running. Stop. Do not relaunch the game.") }
if ($WrapperPid -ne 0) {
    try { $wrap = Get-Process -Id $WrapperPid -ErrorAction Stop } catch { $note.Add("Wrapper PID $WrapperPid is not running.") }
}
if ($null -eq $game) {
    $out = @{ collected_at = (Get-Date).ToString('o'); game_pid = $GamePid; game_alive = $false; notes = @($note); windows = @() }
    $out | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDir 'hwnd_diag.json') -Encoding UTF8
    Write-Output 'game process absent'
    exit 2
}

$targets = @{}
$targets[$GamePid] = $true
if ($null -ne $wrap) { $targets[$WrapperPid] = $true }
$interest = New-Object System.Collections.Generic.List[object]
$seen = 0
foreach ($h in [Vc27Win]::Tops()) {
    $seen++
    if ($seen -gt 400) { $note.Add('Stopped enumerating after 400 top-level windows.'); break }
    $opid = [uint32]0
    $tid = [Vc27Win]::GetWindowThreadProcessId($h, [ref]$opid)
    $title = Text-Of $h
    $cls = Class-Of $h
    $keep = $targets.ContainsKey([int]$opid) -or $cls -eq 'Ghost' -or $title.Contains([string][char]0x5FAE + [char]0x5149)
    if (-not $keep) { continue }
    if ($interest.Count -ge 30) { $note.Add('Stopped message probes after 30 matching windows.'); break }
    $rect = New-Object Vc27Win+RECT
    [void][Vc27Win]::GetWindowRect($h, [ref]$rect)
    $result = [IntPtr]::Zero
    $sm = [Vc27Win]::SendMessageTimeout($h, 0, [IntPtr]::Zero, [IntPtr]::Zero, 2, 500, [ref]$result)
    $answered = ($sm -ne [IntPtr]::Zero)
    $interest.Add([ordered]@{
        hwnd = ('0x{0:X}' -f $h.ToInt64())
        pid = [int]$opid
        thread_id = [int]$tid
        class_name = $cls
        title = $title
        visible = [bool]([Vc27Win]::IsWindowVisible($h))
        is_hung_app_window = [bool]([Vc27Win]::IsHungAppWindow($h))
        wm_null_answered = $answered
        wm_null_timeout_ms = 500
        parent = ('0x{0:X}' -f ([Vc27Win]::GetParent($h).ToInt64()))
        rect = @( $rect.Left, $rect.Top, $rect.Right, $rect.Bottom )
        width = ($rect.Right - $rect.Left)
        height = ($rect.Bottom - $rect.Top)
        ghost_class = ($cls -eq 'Ghost')
    })
}

function Proc-Info($p) {
    if ($null -eq $p) { return $null }
    $cmd = ''
    try {
        $w = Get-CimInstance Win32_Process -Filter "ProcessId=$($p.Id)" -ErrorAction Stop
        $cmd = [string]$w.CommandLine
    } catch { $cmd = "command line unreadable: $($_.Exception.Message)" }
    return [ordered]@{
        pid = $p.Id
        name = $p.ProcessName
        session_id = $p.SessionId
        start_time = $(try { $p.StartTime.ToString('o') } catch { '' })
        cpu_seconds = $(try { [math]::Round($p.CPU, 3) } catch { $null })
        working_set = $p.WorkingSet64
        main_window_handle = ('0x{0:X}' -f $p.MainWindowHandle.ToInt64())
        main_window_title = [string]$p.MainWindowTitle
        command_line = $cmd
        thread_ids = $(try { @($p.Threads | ForEach-Object { $_.Id }) } catch { @() })
    }
}

$bare = $null
if ($IncludeBareWindow) {
    if ([string]::IsNullOrWhiteSpace($GodotExe) -or -not (Test-Path -LiteralPath $GodotExe)) {
        $note.Add('IncludeBareWindow skipped: GodotExe missing.')
    } else {
        $bareDir = Join-Path $env:TEMP ('vc27_hwnd_bare_' + $PID)
        New-Item -ItemType Directory -Force -Path $bareDir | Out-Null
        $utf8 = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText((Join-Path $bareDir 'project.godot'), @"
config_version=5
[application]
config/name="Vc27 Hwnd Bare"
run/main_scene="res://bare.tscn"
config/features=PackedStringArray("4.7")
[display]
window/size/viewport_width=640
window/size/viewport_height=360
"@, $utf8)
        [System.IO.File]::WriteAllText((Join-Path $bareDir 'bare.tscn'), "[gd_scene format=3]`n`n[node name=`"Bare`" type=`"Node`"]`n", $utf8)
        [System.IO.File]::WriteAllText((Join-Path $bareDir 'override.cfg'), "[application]`r`nconfig/use_custom_user_dir=true`r`nconfig/custom_user_dir_name=`"vc27_hwnd_bare_$PID`"`r`n", $utf8)
        $bp = Start-Process -FilePath $GodotExe -ArgumentList @('--path', $bareDir) -PassThru
        $deadline = (Get-Date).AddSeconds(12)
        $bareHwnd = @()
        while ((Get-Date) -lt $deadline) {
            Start-Sleep -Milliseconds 400
            if ($bp.HasExited) { break }
            $got = $false
            foreach ($h in [Vc27Win]::Tops()) {
                $opid = [uint32]0
                $tid = [Vc27Win]::GetWindowThreadProcessId($h, [ref]$opid)
                if ([int]$opid -ne $bp.Id) { continue }
                $got = $true
                $result = [IntPtr]::Zero
                $sm = [Vc27Win]::SendMessageTimeout($h, 0, [IntPtr]::Zero, [IntPtr]::Zero, 2, 500, [ref]$result)
                $rect = New-Object Vc27Win+RECT
                [void][Vc27Win]::GetWindowRect($h, [ref]$rect)
                $bareHwnd += [ordered]@{
                    hwnd = ('0x{0:X}' -f $h.ToInt64())
                    pid = [int]$opid
                    thread_id = [int]$tid
                    class_name = (Class-Of $h)
                    title = (Text-Of $h)
                    visible = [bool]([Vc27Win]::IsWindowVisible($h))
                    is_hung_app_window = [bool]([Vc27Win]::IsHungAppWindow($h))
                    wm_null_answered = ($sm -ne [IntPtr]::Zero)
                    width = ($rect.Right - $rect.Left)
                    height = ($rect.Bottom - $rect.Top)
                }
            }
            if ($got) { break }
        }
        if (-not $bp.HasExited) {
            [void]$bp.CloseMainWindow()
            if (-not $bp.WaitForExit(3000)) { Stop-Process -Id $bp.Id -Force -ErrorAction SilentlyContinue }
        }
        Remove-Item -LiteralPath (Join-Path $bareDir 'override.cfg') -Force -ErrorAction SilentlyContinue
        $bare = [ordered]@{ pid = $bp.Id; profile = "vc27_hwnd_bare_$PID"; windows = @($bareHwnd); note = 'Separate empty project. Not the game. Closed after the probe.' }
        $note.Add('Bare window comparison ran in a disposable profile. The game PID was not closed.')
    }
}

$report = [ordered]@{
    collected_at = (Get-Date).ToString('o')
    elapsed_ms = [int]((Get-Date) - $started).TotalMilliseconds
    collector_pid = $PID
    collector_session = $collector.SessionId
    game = (Proc-Info $game)
    wrapper = (Proc-Info $wrap)
    same_session_as_game = ($(if ($null -ne $game) { $collector.SessionId -eq $game.SessionId } else { $false }))
    windows = @($interest)
    bare_window = $bare
    limits = [ordered]@{
        enum_cap = 400
        probe_cap = 30
        wm_null_timeout_ms = 500
        smto_abort_if_hung = $true
        no_click = $true
        no_wm_close_to_game = $true
        no_save_read = $true
    }
    notes = @($note)
    how_to_read = @(
        'A Ghost class or a title that already says Not Responding, plus another HWND of the game PID that answers WM_NULL: the reported hung window is a ghost. The render window answered.',
        'Every visible HWND of the game PID fails IsHungAppWindow or WM_NULL: the render window itself is not dispatching. Do not treat frame pulses as proof the pump ran.',
        'No HWND belongs to the game PID: the earlier title match was a different process.',
        'collector_session differs from game.session_id: this script is not in the interactive session of that process.',
        'Bare window answers and the game window does not: the hang is specific to the open game, not to every Godot window on this desktop.',
        'Bare window also fails WM_NULL: a Godot window on this desktop is not answering. Still not a cause for the garden scene.'
    )
}
$jsonPath = Join-Path $OutputDir 'hwnd_diag.json'
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $jsonPath -Encoding UTF8
Write-Output "wrote $jsonPath"
Write-Output ("windows=" + $interest.Count + " game_alive=true same_session=" + $report.same_session_as_game)
exit 0
