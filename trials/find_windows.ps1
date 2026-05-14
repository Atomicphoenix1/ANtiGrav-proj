Get-Process | Where-Object { $_.MainWindowTitle } | Select-Object MainWindowTitle | Format-Table -AutoSize
