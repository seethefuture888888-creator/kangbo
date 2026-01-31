# 推送到 GitHub: https://github.com/seethefuture888888-creator/kangbo
# 在项目根目录执行: .\push_to_github.ps1

$ErrorActionPreference = "Stop"
$repoUrl = "https://github.com/seethefuture888888-creator/kangbo.git"

if (-not (Test-Path ".git")) {
    Write-Host "初始化 Git 仓库..."
    git init
    git branch -M main
}

$hasOrigin = (git remote 2>$null) -match "origin"
if (-not $hasOrigin) {
    Write-Host "添加远程仓库 origin -> $repoUrl"
    git remote add origin $repoUrl
} else {
    $remote = git remote get-url origin 2>$null
    if ($remote -and $remote -ne $repoUrl) {
        Write-Host "设置远程仓库 origin -> $repoUrl"
        git remote set-url origin $repoUrl
    }
}

Write-Host "添加所有文件..."
git add -A
$status = git status --short
if (-not $status) {
    Write-Host "没有需要提交的更改。若尚未推送过，请执行: git push -u origin main"
    exit 0
}

Write-Host "提交..."
git commit -m "feat: 康波周期仪表盘 - 宏观+行情多源抓取、dataStatus、部署与风险清单"

Write-Host "推送到 origin main..."
git push -u origin main
Write-Host "完成: https://github.com/seethefuture888888-creator/kangbo"
