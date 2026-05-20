$ErrorActionPreference = "Stop"

# Navigate to the repo root
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -Path $RepoRoot

Write-Host "Adding files to Git..."
git add Daily_Notes/
git add .gitignore

# Check if there are any changes staged
$status = git status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "没有发现新的笔记需要推送。"
    Start-Sleep -Seconds 3
    Exit 0
}

$dateStr = Get-Date -Format "yyyy-MM-dd"
$commitMsg = "Add daily notes for $dateStr"

Write-Host "Committing..."
git commit -m $commitMsg

Write-Host "Pushing to remote origin..."
# Please make sure 'origin' and 'main' are your remote name and branch name
git push origin main

Write-Host "推送完成！"
Start-Sleep -Seconds 3
