# OpenClaw Local Gateway Setup (Agent-Friendly V3)
$LogFile = "C:\Users\saif_\gateway_setup.log"
"Starting Setup..." | Out-File -FilePath $LogFile -Encoding utf8

# 1. Install OpenClaw
if (!(Get-Command openclaw -ErrorAction SilentlyContinue)) {
    "Installing OpenClaw..." | Out-File -FilePath $LogFile -Append -Encoding utf8
    npm install -g openclaw@latest >> $LogFile 2>&1
}

# 2. Configure Gateway
"Configuring Gateway..." | Out-File -FilePath $LogFile -Append -Encoding utf8
openclaw gateway install >> $LogFile 2>&1
openclaw config set gateway.mode local >> $LogFile 2>&1

# Set a fresh token
$token = -join ((48..57) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
openclaw config set gateway.auth.token $token >> $LogFile 2>&1
"TOKEN: $token" | Out-File -FilePath $LogFile -Append -Encoding utf8

# 3. Setup Tunnel
if (!(Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    "Downloading Cloudflared..." | Out-File -FilePath $LogFile -Append -Encoding utf8
    Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.msi" -OutFile "cloudflared.msi"
    Start-Process msiexec.exe -ArgumentList "/i cloudflared.msi /quiet /qn /norestart" -Wait
    Remove-Item "cloudflared.msi"
}

# Run tunnel in background and log output
"Starting Tunnel..." | Out-File -FilePath $LogFile -Append -Encoding utf8
$TunnelLog = "C:\Users\saif_\tunnel.log"
Start-Job -Name "CloudflareTunnel" -ScriptBlock {
    param($LogPath)
    cloudflared tunnel --url http://localhost:18789 2>&1 | Out-File -FilePath $LogPath -Encoding utf8
} -ArgumentList $TunnelLog
"Tunnel process started in background." | Out-File -FilePath $LogFile -Append -Encoding utf8
