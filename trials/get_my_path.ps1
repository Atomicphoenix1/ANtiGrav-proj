$proc = Get-Process | Where-Object { $_.MainWindowTitle -like "*Antigravity*" } | Select-Object -First 1
if ($proc) {
    Write-Host "PATH:$($proc.Path)"
} else {
    Write-Host "NOT_FOUND"
}
