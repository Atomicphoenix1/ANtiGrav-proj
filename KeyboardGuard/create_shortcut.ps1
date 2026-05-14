$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.IO.Path]::Combine($env:USERPROFILE, "Desktop")
$Shortcut = $WshShell.CreateShortcut("$DesktopPath\Keyboard Guard.lnk")
$Shortcut.TargetPath = "c:\Users\saif_\Desktop\downs\حاليًا\يومي\Lectures\ANtiGrav\KeyboardGuard\run.bat"
$Shortcut.WorkingDirectory = "c:\Users\saif_\Desktop\downs\حاليًا\يومي\Lectures\ANtiGrav\KeyboardGuard\"
$Shortcut.WindowStyle = 7 # Minimized
$Shortcut.Save()

Write-Host "Desktop shortcut created successfully!"
