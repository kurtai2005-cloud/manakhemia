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
    $json = '{"ok":false,"stage":"' + (Escape-JsonText $StageName) + '","exception":"' + (Escape-JsonText $typeName) + '","message":"' + (Escape-JsonText $msg) + '","stack":"' + (Escape-JsonText $stack) + '"}'
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($Path, $json, $utf8)
}

if ($SelfTest -and [string]::IsNullOrWhiteSpace($OutputDir)) { throw 'SelfTest requires OutputDir' }

try {
    $stage = 'output_dir'
    if (-not $SelfTest -and $GamePid -le 0) { throw 'GamePid is required' }
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

    if ($SelfTest) {
        $stage = 'add_type'
    } elseif ($null -eq $game) {
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
    static string E(string s) {
        if (s == null) return "";
        StringBuilder b = new StringBuilder();
        foreach (char c in s) {
            if (c == '\\' || c == '"') { b.Append('\\'); b.Append(c); }
            else if (c == '\r') b.Append("\\r");
            else if (c == '\n') b.Append("\\n");
            else if (c == '\t') b.Append("\\t");
            else if (c < 32) b.Append(' ');
            else b.Append(c);
        }
        return b.ToString();
    }
    public static string FailureJson(string stage, string exception, string message, string stack) {
        return "{\"ok\":false,\"stage\":\"" + E(stage) + "\",\"exception\":\"" + E(exception) + "\",\"message\":\"" + E(message) + "\",\"stack\":\"" + E(stack) + "\"}";
    }
    public static Vc27WinCensus Sample(int count) {
        Vc27WinCensus bag = new Vc27WinCensus();
        bag.EnumCount = count;
        for (int i = 0; i < count; i++) {
            Vc27WinRow row = new Vc27WinRow();
            row.Hwnd = "0x" + (0x14C0ACE + i).ToString("X");
            row.Pid = (i % 2 == 0) ? 4748 : 9132;
            row.ThreadId = 1000 + i;
            row.ClassName = (i == 2) ? "Ghost" : "Engine";
            row.Title = "sample-" + i.ToString();
            row.Visible = true;
            row.IsHung = (i == 2);
            row.WmNullAnswered = (i != 2);
            row.Left = 0; row.Top = 0; row.Right = 275; row.Bottom = 600;
            row.ParentHwnd = "0x0";
            row.GhostClass = row.ClassName == "Ghost";
            row.ProbeError = "";
            bag.Windows.Add(row);
        }
        return bag;
    }
    public static string ToJson(Vc27WinCensus bag, int gamePid, int wrapperPid, int collectorPid, int collectorSession, bool sameSession, string gameName, int gameSession, string gameStart, string gameMainHwnd, string gameTitle, string gameCmd, string wrapName, int wrapSession, string wrapMainHwnd, string wrapTitle) {
        StringBuilder b = new StringBuilder();
        b.Append("{\"ok\":true,\"stage\":\"done\",\"game_alive\":true,\"game_pid\":");
        b.Append(gamePid);
        b.Append(",\"wrapper_pid\":");
        b.Append(wrapperPid);
        b.Append(",\"collector_pid\":");
        b.Append(collectorPid);
        b.Append(",\"collector_session\":");
        b.Append(collectorSession);
        b.Append(",\"same_session_as_game\":");
        b.Append(sameSession ? "true" : "false");
        b.Append(",\"game\":{\"name\":\"");
        b.Append(E(gameName));
        b.Append("\",\"session_id\":");
        b.Append(gameSession);
        b.Append(",\"start_time\":\"");
        b.Append(E(gameStart));
        b.Append("\",\"main_window_handle\":\"");
        b.Append(E(gameMainHwnd));
        b.Append("\",\"main_window_title\":\"");
        b.Append(E(gameTitle));
        b.Append("\",\"command_line\":\"");
        b.Append(E(gameCmd));
        b.Append("\"},\"wrapper\":{\"name\":\"");
        b.Append(E(wrapName));
        b.Append("\",\"session_id\":");
        b.Append(wrapSession);
        b.Append(",\"main_window_handle\":\"");
        b.Append(E(wrapMainHwnd));
        b.Append("\",\"main_window_title\":\"");
        b.Append(E(wrapTitle));
        b.Append("\"},\"enum_count\":");
        b.Append(bag == null ? 0 : bag.EnumCount);
        b.Append(",\"enum_capped\":");
        b.Append(bag != null && bag.EnumCapped ? "true" : "false");
        b.Append(",\"probe_capped\":");
        b.Append(bag != null && bag.ProbeCapped ? "true" : "false");
        b.Append(",\"windows\":[");
        if (bag != null) {
            for (int i = 0; i < bag.Windows.Count; i++) {
                Vc27WinRow w = bag.Windows[i];
                if (i > 0) b.Append(',');
                b.Append("{\"hwnd\":\"");
                b.Append(E(w.Hwnd));
                b.Append("\",\"pid\":");
                b.Append(w.Pid);
                b.Append(",\"thread_id\":");
                b.Append(w.ThreadId);
                b.Append(",\"class_name\":\"");
                b.Append(E(w.ClassName));
                b.Append("\",\"title\":\"");
                b.Append(E(w.Title));
                b.Append("\",\"visible\":");
                b.Append(w.Visible ? "true" : "false");
                b.Append(",\"is_hung_app_window\":");
                b.Append(w.IsHung ? "true" : "false");
                b.Append(",\"wm_null_answered\":");
                b.Append(w.WmNullAnswered ? "true" : "false");
                b.Append(",\"wm_null_timeout_ms\":500,\"parent\":\"");
                b.Append(E(w.ParentHwnd));
                b.Append("\",\"rect\":[");
                b.Append(w.Left); b.Append(','); b.Append(w.Top); b.Append(','); b.Append(w.Right); b.Append(','); b.Append(w.Bottom);
                b.Append("],\"width\":");
                b.Append(w.Right - w.Left);
                b.Append(",\"height\":");
                b.Append(w.Bottom - w.Top);
                b.Append(",\"ghost_class\":");
                b.Append(w.GhostClass ? "true" : "false");
                b.Append(",\"probe_error\":\"");
                b.Append(E(w.ProbeError));
                b.Append("\"}");
            }
        }
        b.Append("],\"limits\":{\"enum_cap\":400,\"probe_cap\":30,\"wm_null_timeout_ms\":500,\"smto_abort_if_hung\":true,\"no_click\":true,\"no_wm_close\":true,\"no_save_read\":true,\"no_new_process\":true}}");
        return b.ToString();
    }
}
"@
    }

    if ($SelfTest) {
        $stage = 'self_test'
        $utf8 = New-Object System.Text.UTF8Encoding $false
        foreach ($count in @(0, 1, 3)) {
            $sample = [Vc27WinCensus]::Sample([int]$count)
            $json = [Vc27WinCensus]::ToJson($sample, 4748, 9132, 1, 2, $true, 'Godot', 2, '2026-11-23T07:59:54.229+08:00', '0x14C0ACE', 'sample', '--rendering-method mobile --path game', 'powershell', 2, '0x0', 'wrapper')
            $path = Join-Path $fullOut ("self_test_success_" + $count + ".json")
            [System.IO.File]::WriteAllText($path, $json, $utf8)
            $parsed = $json | ConvertFrom-Json
            if ($parsed.ok -ne $true -or $parsed.stage -ne 'done') { throw "success json header $count" }
            if ($count -eq 0 -and $json.Contains('"windows":[]') -eq $false) { throw 'zero-row json' }
            if ($count -eq 1 -and $parsed.windows.hwnd -ne '0x14C0ACE') { throw 'one-row hwnd' }
            if ($count -gt 1 -and $parsed.windows.Count -ne $count) { throw 'many-row count' }
            if ($count -eq 3 -and $parsed.windows[2].ghost_class -ne $true) { throw 'ghost row' }
            if ($count -eq 3 -and $parsed.windows[2].wm_null_answered -ne $false) { throw 'ghost wm_null' }
        }
        $fail = [Vc27WinCensus]::FailureJson('write_json', 'System.ArgumentException', 'Argument types do not match', 'line 304')
        $failPath = Join-Path $fullOut 'self_test_failure.json'
        [System.IO.File]::WriteAllText($failPath, $fail, $utf8)
        $bf = $fail | ConvertFrom-Json
        if ($bf.ok -ne $false -or $bf.stage -ne 'write_json' -or $bf.exception -ne 'System.ArgumentException') { throw 'failure json' }
        Write-Output 'self_test_ok'
        exit 0
    }

    $stage = 'enumerate'
    $pids = New-Object int[] 2
    $pids[0] = $GamePid
    $pids[1] = $WrapperPid
    $bag = [Vc27WinCensus]::Collect($pids, 400, 30, [uint32]500)

    $stage = 'write_json'
    $gameCmd = ''
    try {
        $w = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $game.Id) -ErrorAction Stop
        $gameCmd = [string]$w.CommandLine
    } catch { $gameCmd = '' }
    $gameStart = ''
    try { $gameStart = $game.StartTime.ToString('o') } catch { $gameStart = '' }
    $wrapName = ''
    $wrapSession = 0
    $wrapHwnd = '0x0'
    $wrapTitle = ''
    if ($null -ne $wrap) {
        $wrapName = [string]$wrap.ProcessName
        $wrapSession = [int]$wrap.SessionId
        $wrapHwnd = ('0x{0:X}' -f $wrap.MainWindowHandle.ToInt64())
        $wrapTitle = [string]$wrap.MainWindowTitle
    }
    $json = [Vc27WinCensus]::ToJson(
        $bag,
        [int]$GamePid,
        [int]$WrapperPid,
        [int]$PID,
        [int]$collector.SessionId,
        [bool]($collector.SessionId -eq $game.SessionId),
        [string]$game.ProcessName,
        [int]$game.SessionId,
        [string]$gameStart,
        ('0x{0:X}' -f $game.MainWindowHandle.ToInt64()),
        [string]$game.MainWindowTitle,
        [string]$gameCmd,
        [string]$wrapName,
        [int]$wrapSession,
        [string]$wrapHwnd,
        [string]$wrapTitle
    )
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($diagPath, $json, $utf8)
    Write-Output ("wrote " + $diagPath)
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
