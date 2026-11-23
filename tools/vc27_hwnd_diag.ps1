# Read-only window census. Windows PowerShell 5.1 compatible.
# Does not launch the game, does not send WM_CLOSE, does not read saves.
# Every exit writes hwnd_diag.json, including failures.
param(
    [int]$GamePid = 0,
    [int]$WrapperPid = 0,
    [string]$OutputDir = '',
    [switch]$SelfTest
)
$ErrorActionPreference = 'Stop'
$stage = 'init'
$diagPath = $null

function Escape-JsonText([string]$Value) {
    if ($null -eq $Value) { return '' }
    $s = $Value.Replace('\', '\\').Replace('"', '\"').Replace("`r", '\r').Replace("`n", '\n').Replace("`t", '\t')
    return $s
}

function Write-DiagFile($Path, $Object) {
    $json = $null
    try {
        $json = $Object | ConvertTo-Json -Depth 8 -Compress:$false
    } catch {
        $msg = Escape-JsonText ([string]$_.Exception.Message)
        $json = "{`r`n  `"ok`": false,`r`n  `"stage`": `"json_convert`",`r`n  `"exception`": `"System.Management.Automation.ErrorRecord`",`r`n  `"message`": `"$msg`"`r`n}`r`n"
    }
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($Path, $json, $utf8)
}

function Write-Failure($Path, $StageName, $Record) {
    $ex = $null
    $msg = ''
    $stack = ''
    $typeName = 'System.Exception'
    if ($null -ne $Record) {
        if ($null -ne $Record.Exception) {
            $ex = $Record.Exception
            $typeName = $ex.GetType().FullName
            $msg = [string]$ex.Message
        } else {
            $msg = [string]$Record
        }
        $stack = [string]$Record.ScriptStackTrace
        if ([string]::IsNullOrEmpty($stack) -and $null -ne $ex) { $stack = [string]$ex.ToString() }
    }
    $safe = [ordered]@{
        ok = $false
        stage = [string]$StageName
        exception = $typeName
        message = $msg
        stack = $stack
    }
    Write-DiagFile $Path $safe
}

if ($SelfTest) {
    if ([string]::IsNullOrWhiteSpace($OutputDir)) { throw 'SelfTest requires OutputDir' }
    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
    $sample = [ordered]@{
        ok = $true
        stage = 'self_test'
        game_pid = 4748
        windows = @(
            [ordered]@{
                hwnd = '0x14C0ACE'
                pid = 4748
                thread_id = 1
                class_name = 'Engine'
                title = 'sample'
                visible = $true
                is_hung_app_window = $false
                wm_null_answered = $true
                ghost_class = $false
            }
        )
    }
    $okPath = Join-Path $OutputDir 'self_test_success.json'
    Write-DiagFile $okPath $sample
    $bad = New-Object System.Management.Automation.ErrorRecord (
        (New-Object System.ArgumentException 'Argument types do not match'),
        'SelfTest',
        'InvalidArgument',
        $null
    )
    $badPath = Join-Path $OutputDir 'self_test_failure.json'
    Write-Failure $badPath 'enumerate' $bad
    $a = Get-Content -LiteralPath $okPath -Raw | ConvertFrom-Json
    $b = Get-Content -LiteralPath $badPath -Raw | ConvertFrom-Json
    if ($a.ok -ne $true -or $a.windows[0].hwnd -ne '0x14C0ACE') { throw 'success json did not round-trip' }
    if ($b.ok -ne $false -or $b.stage -ne 'enumerate' -or $b.exception -ne 'System.ArgumentException') { throw 'failure json did not round-trip' }
    if ($b.message -notlike '*Argument types do not match*') { throw 'failure message missing' }
    Write-Output 'self_test_ok'
    exit 0
}

try {
    $stage = 'output_dir'
    if ($GamePid -le 0) { throw 'GamePid is required' }
    if ([string]::IsNullOrWhiteSpace($OutputDir)) { throw 'OutputDir is required' }
    $gameRoot = 'C:\Users\nasa2\hd2d_test\vc27_play_main_2092'
    $saveHint = 'C:\Users\nasa2\AppData\Roaming\vc27_play_36bfd'
    $fullOut = [System.IO.Path]::GetFullPath($OutputDir)
    if ($fullOut.TrimEnd('\') -eq $gameRoot -or $fullOut.TrimEnd('\') -eq $saveHint) {
        throw 'OutputDir must not be the game folder or the play profile'
    }
    if (Test-Path -LiteralPath $fullOut) {
        $item = Get-Item -LiteralPath $fullOut -Force
        if (-not $item.PSIsContainer) { throw "OutputDir is not a directory: $fullOut" }
        $existing = @(Get-ChildItem -LiteralPath $fullOut -Force | Select-Object -First 1)
        if ($existing.Count -gt 0) { throw "OutputDir is not empty: $fullOut" }
    } else {
        New-Item -ItemType Directory -Path $fullOut | Out-Null
    }
    $diagPath = Join-Path $fullOut 'hwnd_diag.json'
    Write-DiagFile $diagPath ([ordered]@{ ok = $false; stage = 'started'; message = 'census started' })

    $stage = 'resolve_process'
    $game = $null
    $wrap = $null
    $notes = New-Object System.Collections.Generic.List[string]
    $notes.Add('Read-only. No WM_CLOSE. No save read. No new game process.')
    $notes.Add('WM_NULL uses SendMessageTimeout 500 ms with SMTO_ABORTIFHUNG.')
    try { $game = Get-Process -Id $GamePid -ErrorAction Stop } catch {
        $notes.Add("Game PID $GamePid is not running. Stop. Do not relaunch the game.")
    }
    if ($WrapperPid -gt 0) {
        try { $wrap = Get-Process -Id $WrapperPid -ErrorAction Stop } catch {
            $notes.Add("Wrapper PID $WrapperPid is not running.")
        }
    }
    $collector = Get-Process -Id $PID

    function Proc-Info($Proc) {
        if ($null -eq $Proc) { return $null }
        $cmd = ''
        try {
            $w = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $Proc.Id) -ErrorAction Stop
            $cmd = [string]$w.CommandLine
        } catch { $cmd = 'command line unreadable' }
        $startedAt = ''
        try { $startedAt = $Proc.StartTime.ToString('o') } catch { $startedAt = '' }
        $cpu = $null
        try { $cpu = [math]::Round($Proc.CPU, 3) } catch { $cpu = $null }
        $threads = @()
        try { $threads = @($Proc.Threads | ForEach-Object { $_.Id }) } catch { $threads = @() }
        return [ordered]@{
            pid = $Proc.Id
            name = [string]$Proc.ProcessName
            session_id = $Proc.SessionId
            start_time = $startedAt
            cpu_seconds = $cpu
            working_set = $Proc.WorkingSet64
            main_window_handle = ('0x{0:X}' -f $Proc.MainWindowHandle.ToInt64())
            main_window_title = [string]$Proc.MainWindowTitle
            command_line = $cmd
            thread_ids = $threads
        }
    }

    if ($null -eq $game) {
        $stage = 'write_absent'
        Write-DiagFile $diagPath ([ordered]@{
            ok = $false
            stage = 'resolve_process'
            game_pid = $GamePid
            game_alive = $false
            notes = @($notes)
        })
        Write-Output 'game process absent'
        exit 2
    }

    $stage = 'add_type'
    if (-not ('Vc27WinCensus' -as [type])) {
        Add-Type -TypeDefinition @"
using System;
using System.Text;
using System.Runtime.InteropServices;
using System.Collections.Generic;
public class Vc27WinRow {
    public string Hwnd;
    public int Pid;
    public int ThreadId;
    public string ClassName;
    public string Title;
    public bool Visible;
    public bool IsHung;
    public bool WmNullAnswered;
    public string ProbeError;
    public int Left;
    public int Top;
    public int Right;
    public int Bottom;
    public string ParentHwnd;
    public bool GhostClass;
}
public class Vc27WinCensus {
    public int EnumCount;
    public bool EnumCapped;
    public bool ProbeCapped;
    public List<Vc27WinRow> Windows = new List<Vc27WinRow>();
    delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc cb, IntPtr lp);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
    [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] static extern bool IsHungAppWindow(IntPtr hWnd);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern int GetWindowText(IntPtr hWnd, StringBuilder s, int n);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern int GetClassName(IntPtr hWnd, StringBuilder s, int n);
    [DllImport("user32.dll")] static extern bool GetWindowRect(IntPtr hWnd, out RECT r);
    [DllImport("user32.dll")] static extern IntPtr GetParent(IntPtr hWnd);
    [DllImport("user32.dll", EntryPoint="SendMessageTimeoutW")] static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam, uint flags, uint timeout, out IntPtr result);
    struct RECT { public int Left, Top, Right, Bottom; }
    static string Txt(IntPtr h) {
        StringBuilder b = new StringBuilder(512);
        GetWindowText(h, b, b.Capacity);
        return b.ToString();
    }
    static string Cls(IntPtr h) {
        StringBuilder b = new StringBuilder(256);
        GetClassName(h, b, b.Capacity);
        return b.ToString();
    }
    public static Vc27WinCensus Collect(int[] watchPids, int maxEnum, int maxProbe, uint timeoutMs) {
        Vc27WinCensus bag = new Vc27WinCensus();
        List<IntPtr> all = new List<IntPtr>();
        EnumWindows(delegate(IntPtr h, IntPtr l) { all.Add(h); return true; }, IntPtr.Zero);
        foreach (IntPtr h in all) {
            bag.EnumCount++;
            if (bag.EnumCount > maxEnum) { bag.EnumCapped = true; break; }
            uint opid;
            uint tid = GetWindowThreadProcessId(h, out opid);
            string title = "";
            string cls = "";
            try { title = Txt(h); cls = Cls(h); } catch (Exception ex) { title = ex.GetType().FullName; }
            bool wanted = false;
            if (watchPids != null) {
                for (int i = 0; i < watchPids.Length; i++) {
                    if (watchPids[i] == (int)opid) { wanted = true; break; }
                }
            }
            if (!wanted && cls == "Ghost") wanted = true;
            if (!wanted && title != null && title.IndexOf("\u5FAE\u5149") >= 0) wanted = true;
            if (!wanted) continue;
            if (bag.Windows.Count >= maxProbe) { bag.ProbeCapped = true; break; }
            Vc27WinRow row = new Vc27WinRow();
            row.Hwnd = "0x" + h.ToInt64().ToString("X");
            row.Pid = (int)opid;
            row.ThreadId = (int)tid;
            row.ClassName = cls;
            row.Title = title;
            row.GhostClass = cls == "Ghost";
            try {
                row.Visible = IsWindowVisible(h);
                row.IsHung = IsHungAppWindow(h);
                RECT rect;
                GetWindowRect(h, out rect);
                row.Left = rect.Left; row.Top = rect.Top; row.Right = rect.Right; row.Bottom = rect.Bottom;
                row.ParentHwnd = "0x" + GetParent(h).ToInt64().ToString("X");
                IntPtr result;
                IntPtr sm = SendMessageTimeout(h, 0, IntPtr.Zero, IntPtr.Zero, 2, timeoutMs, out result);
                row.WmNullAnswered = sm != IntPtr.Zero;
            } catch (Exception ex) {
                row.ProbeError = ex.GetType().FullName + ": " + ex.Message;
            }
            bag.Windows.Add(row);
        }
        return bag;
    }
}
"@
    }

    $stage = 'enumerate'
    $pids = New-Object int[] 2
    $pids[0] = $GamePid
    $pids[1] = $WrapperPid
    $bag = [Vc27WinCensus]::Collect($pids, 400, 30, [uint32]500)
    $rows = New-Object System.Collections.Generic.List[object]
    foreach ($row in $bag.Windows) {
        $rows.Add([ordered]@{
            hwnd = [string]$row.Hwnd
            pid = [int]$row.Pid
            thread_id = [int]$row.ThreadId
            class_name = [string]$row.ClassName
            title = [string]$row.Title
            visible = [bool]$row.Visible
            is_hung_app_window = [bool]$row.IsHung
            wm_null_answered = [bool]$row.WmNullAnswered
            wm_null_timeout_ms = 500
            parent = [string]$row.ParentHwnd
            rect = @([int]$row.Left, [int]$row.Top, [int]$row.Right, [int]$row.Bottom)
            width = ([int]$row.Right - [int]$row.Left)
            height = ([int]$row.Bottom - [int]$row.Top)
            ghost_class = [bool]$row.GhostClass
            probe_error = [string]$row.ProbeError
        })
    }

    $stage = 'write_json'
    $gameInfo = Proc-Info $game
    $wrapInfo = Proc-Info $wrap
    Write-DiagFile $diagPath ([ordered]@{
        ok = $true
        stage = 'done'
        game_alive = $true
        game_pid = $GamePid
        wrapper_pid = $WrapperPid
        collector_pid = $PID
        collector_session = $collector.SessionId
        same_session_as_game = ($collector.SessionId -eq $game.SessionId)
        game = $gameInfo
        wrapper = $wrapInfo
        enum_count = $bag.EnumCount
        enum_capped = [bool]$bag.EnumCapped
        probe_capped = [bool]$bag.ProbeCapped
        windows = @($rows)
        limits = [ordered]@{
            enum_cap = 400
            probe_cap = 30
            wm_null_timeout_ms = 500
            smto_abort_if_hung = $true
            no_click = $true
            no_wm_close = $true
            no_save_read = $true
            no_new_process = $true
        }
        notes = @(
            'Read-only. No WM_CLOSE. No save read. No new process.',
            'WM_NULL uses SendMessageTimeout 500 ms with SMTO_ABORTIFHUNG.',
            'A Ghost class window that is hung, plus another HWND of the game PID that answers WM_NULL: the earlier title was a ghost.',
            'Every visible HWND of the game PID fails IsHungAppWindow or WM_NULL: that window is not dispatching. Frame pulses are not a pump.',
            'No HWND has the game PID: the title belonged to another process.',
            'same_session_as_game false: this PowerShell is not on that process desktop.'
        )
    })
    Write-Output ("wrote " + $diagPath)
    Write-Output ("windows=" + $rows.Count)
    exit 0
} catch {
    if ($null -ne $diagPath) {
        Write-Failure $diagPath $stage $_
        Write-Output ("wrote failure " + $diagPath)
    } else {
        Write-Output ("failed before output file stage=" + $stage + " " + $_.Exception.Message)
    }
    exit 1
}
