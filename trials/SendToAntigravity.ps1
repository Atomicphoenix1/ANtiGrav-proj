param (
    [Parameter(Mandatory=$true)]
    [string]$Message,
    [string]$Model = "",
    [string]$Mode = ""
)

# The path to the Antigravity application
$AppPath = "C:\Users\saif_\AppData\Local\Programs\Antigravity\Antigravity.exe"

# Prepare the final prompt with instructions
$FinalPrompt = ""
if ($Model) { $FinalPrompt += "[SYSTEM: SWITCH TO MODEL $Model] " }
if ($Mode) { $FinalPrompt += "[SYSTEM: USE $Mode MODE] " }
$FinalPrompt += $Message

# Load UI libraries
Add-Type -AssemblyName System.Windows.Forms
Set-Clipboard -Value $FinalPrompt

# Check if the window is already open
$wshell = New-Object -ComObject WScript.Shell
$process = Get-Process | Where-Object { $_.MainWindowTitle -like "*Antigravity*" } | Select-Object -First 1

# If not open, launch the application
if (-not $process) {
    Write-Host "Launching Antigravity..."
    Start-Process $AppPath
    Start-Sleep -Seconds 8 # Wait for the app to initialize
    $process = Get-Process | Where-Object { $_.MainWindowTitle -like "*Antigravity*" } | Select-Object -First 1
}

# Focus and Paste
if ($process) {
    Write-Host "Activating Antigravity window (PID: $($process.Id))..."
    $wshell.AppActivate($process.Id)
    Start-Sleep -Milliseconds 1500 # Give it time to focus
    
    # Paste (Ctrl+V) and Send (Enter)
    [System.Windows.Forms.SendKeys]::SendWait("^v")
    Start-Sleep -Milliseconds 500
    [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
    Write-Host "Message sent successfully."
} else {
    Write-Error "Could not launch or find the Antigravity application window."
}
