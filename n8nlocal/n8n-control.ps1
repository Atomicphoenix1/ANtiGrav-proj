# n8n Local Controller — Windows Task Scheduler edition
# Senior DevOps & Automation Engineering Standard

param (
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet("install","start","stop","restart","status","uninstall","test","logs")]
    [string]$Action
)

$RootDir      = Split-Path -Parent $MyInvocation.MyCommand.Path
$TaskName     = "n8n-local-autostart"
$LaunchScript = Join-Path $RootDir "launch-n8n.ps1"
$LogDir       = Join-Path $RootDir "logs"
$LogFile      = Join-Path $LogDir  "n8n-task.log"
$ErrFile      = Join-Path $LogDir  "n8n-task-error.log"
$PidFile      = Join-Path $LogDir  "n8n.pid"

if (!(Test-Path $LogDir)) { New-Item -ItemType Directory -Force -Path $LogDir | Out-Null }

Set-Location $RootDir

switch ($Action) {

    "install" {
        Write-Host "[+] Registering n8n-local-autostart in Task Scheduler..." -ForegroundColor Cyan

        $action = New-ScheduledTaskAction `
            -Execute "powershell.exe" `
            -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$LaunchScript`"" `
            -WorkingDirectory $RootDir

        $trigger   = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
        $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
        $settings  = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 0) -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
        Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "Self-hosted n8n — starts at user logon" | Out-Null

        Write-Host "[+] Task '$TaskName' installed. n8n will auto-start on next Windows login." -ForegroundColor Green
        Write-Host "[+] To start n8n RIGHT NOW, run: .\n8n-control.ps1 start" -ForegroundColor Yellow
    }

    "start" {
        Write-Host "[+] Starting n8n (background, hidden window)..." -ForegroundColor Cyan

        # Kill any existing n8n processes
        if (Test-Path $PidFile) {
            $oldPid = (Get-Content $PidFile -ErrorAction SilentlyContinue) -as [int]
            if ($oldPid) { Stop-Process -Id $oldPid -Force -ErrorAction SilentlyContinue }
        }
        # Kill any stray n8n node processes
        Get-WmiObject Win32_Process -Filter "Name='node.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -like "*n8n*" } |
            ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

        Start-Sleep -Milliseconds 500

        # Launch the launcher as a fully detached hidden process
        $proc = Start-Process -FilePath "powershell.exe" `
            -ArgumentList "-ExecutionPolicy","Bypass","-WindowStyle","Hidden","-File","`"$LaunchScript`"" `
            -WorkingDirectory $RootDir `
            -PassThru

        Write-Host "[+] Launcher started (PID: $($proc.Id)). Waiting 10s for n8n to initialize..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10

        # Check result
        if (Test-Path $PidFile) {
            $n8nPid = Get-Content $PidFile -ErrorAction SilentlyContinue
            $running = Get-Process -Id ([int]$n8nPid) -ErrorAction SilentlyContinue
            if ($running) {
                Write-Host "[+] n8n is RUNNING — PID: $n8nPid" -ForegroundColor Green
            } else {
                Write-Host "[-] n8n process (PID $n8nPid) is NOT found. Check logs:" -ForegroundColor Red
                Write-Host "    $ErrFile" -ForegroundColor Red
            }
        } else {
            Write-Host "[-] PID file not found yet — n8n may still be booting." -ForegroundColor Yellow
        }

        # HTTP probe
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:5679/healthz" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
            Write-Host "[+] HTTP HEALTHY — http://localhost:5679 is responding!" -ForegroundColor Green
        } catch {
            Write-Host "[-] HTTP probe: n8n not yet responding on port 5679 (may still be loading)." -ForegroundColor Yellow
        }
    }

    "stop" {
        Write-Host "[-] Stopping n8n..." -ForegroundColor Yellow
        if (Test-Path $PidFile) {
            $n8nPid = (Get-Content $PidFile -ErrorAction SilentlyContinue) -as [int]
            if ($n8nPid) {
                Stop-Process -Id $n8nPid -Force -ErrorAction SilentlyContinue
                Write-Host "[-] Killed PID: $n8nPid" -ForegroundColor Yellow
            }
            Remove-Item $PidFile -ErrorAction SilentlyContinue
        }
        Get-WmiObject Win32_Process -Filter "Name='node.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -like "*n8n*" } |
            ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
        Write-Host "[-] n8n stopped." -ForegroundColor Yellow
    }

    "restart" {
        & $PSCommandPath stop; Start-Sleep -Seconds 2; & $PSCommandPath start
    }

    "status" {
        Write-Host "[n8n Status Check]" -ForegroundColor Cyan

        # PID check
        if (Test-Path $PidFile) {
            $n8nPid = (Get-Content $PidFile -ErrorAction SilentlyContinue) -as [int]
            if ($n8nPid) {
                $proc = Get-Process -Id $n8nPid -ErrorAction SilentlyContinue
                if ($proc) {
                    $uptime = (Get-Date) - $proc.StartTime
                    Write-Host "[+] RUNNING — PID: $n8nPid | Mem: $([math]::Round($proc.WorkingSet64/1MB,1))MB | Up: $([math]::Round($uptime.TotalMinutes,1))min" -ForegroundColor Green
                } else {
                    Write-Host "[-] PID $n8nPid not found — n8n has stopped." -ForegroundColor Red
                }
            }
        } else {
            Write-Host "[-] No PID file. Run: .\n8n-control.ps1 start" -ForegroundColor Yellow
        }

        # HTTP probe
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:5679/healthz" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
            Write-Host "[+] HTTP: HEALTHY on http://localhost:5679" -ForegroundColor Green
        } catch {
            Write-Host "[-] HTTP: No response on port 5679" -ForegroundColor Red
        }

        # Task Scheduler status
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($task) {
            Write-Host "[+] Task Scheduler: $TaskName is $($task.State)" -ForegroundColor Green
        } else {
            Write-Host "[-] Task Scheduler: not installed. Run: .\n8n-control.ps1 install" -ForegroundColor Yellow
        }
    }

    "logs" {
        Write-Host "[n8n Logs — last 60 lines]" -ForegroundColor Cyan
        if (Test-Path $LogFile)  { Write-Host "--- STDOUT ---" -ForegroundColor Gray; Get-Content $LogFile -Tail 60 }
        if (Test-Path $ErrFile)  { Write-Host "--- STDERR ---" -ForegroundColor Gray; Get-Content $ErrFile -Tail 30 }
    }

    "uninstall" {
        & $PSCommandPath stop
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
        Write-Host "[-] Task '$TaskName' uninstalled." -ForegroundColor Yellow
    }

    "test" {
        node "$RootDir\test-env-verification.js"
    }
}
