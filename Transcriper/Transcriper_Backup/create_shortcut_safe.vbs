Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
Set folder = fso.GetFolder(currentDir)

shortPath = folder.ShortPath
shortBatch = shortPath & "\run_formatter.bat"
shortIcon = shortPath & "\app_icon.ico"

desktop = shell.SpecialFolders("Desktop")
Set shortcut = shell.CreateShortcut(desktop & "\AI Studio Formatter.lnk")
shortcut.TargetPath = shortBatch
shortcut.WorkingDirectory = shortPath
shortcut.IconLocation = shortIcon & ", 0"
shortcut.Save

WScript.Echo "Success! Shortcut created using safe paths."
