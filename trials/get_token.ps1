$token = -join ((48..57) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
openclaw config set gateway.auth.token $token
Write-Output $token
