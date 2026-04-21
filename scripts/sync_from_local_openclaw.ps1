param(
    [string]$SourceWorkspace = 'D:\OpenClaw\.openclaw\workspace',
    [string]$DestinationWorkspace = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path,
    [string]$SkillName = 'xhs-trend-to-publish'
)

$ErrorActionPreference = 'Stop'

function Copy-RelativePath {
    param(
        [string]$SourceRoot,
        [string]$DestinationRoot,
        [string]$RelativePath
    )

    $sourcePath = Join-Path $SourceRoot $RelativePath
    if (-not (Test-Path $sourcePath)) {
        throw "Missing source path: $sourcePath"
    }

    $destinationPath = Join-Path $DestinationRoot $RelativePath
    $destinationParent = Split-Path -Parent $destinationPath
    if ($destinationParent) {
        New-Item -ItemType Directory -Force -Path $destinationParent | Out-Null
    }

    Copy-Item -Path $sourcePath -Destination $destinationPath -Recurse -Force
}

$sourceSkill = Join-Path $SourceWorkspace "skills\$SkillName"
$destinationSkill = Join-Path $DestinationWorkspace "skills\$SkillName"

if (-not (Test-Path $sourceSkill)) {
    throw "Skill source not found: $sourceSkill"
}

if (Test-Path $destinationSkill) {
    Remove-Item -Path $destinationSkill -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $destinationSkill | Out-Null

$skillPaths = @(
    '.gitignore',
    'README.md',
    'SKILL.md',
    'config',
    'references',
    'scripts',
    'vendor'
)

foreach ($relativePath in $skillPaths) {
    Copy-RelativePath -SourceRoot $sourceSkill -DestinationRoot $destinationSkill -RelativePath $relativePath
}

$removePaths = @(
    (Join-Path $destinationSkill 'data'),
    (Join-Path $destinationSkill 'temp'),
    (Join-Path $destinationSkill 'vendor\Auto-Redbook-Skills\demos'),
    (Join-Path $destinationSkill 'vendor\XiaohongshuSkills\tmp')
)

foreach ($path in $removePaths) {
    if (Test-Path $path) {
        Remove-Item -Path $path -Recurse -Force
    }
}

Get-ChildItem -Path $destinationSkill -Recurse -Directory -Force |
    Where-Object { $_.Name -in @('__pycache__', '.git') } |
    Remove-Item -Recurse -Force

Get-ChildItem -Path $destinationSkill -Recurse -File -Force -Include '*.pyc', '*.pyo', '*.pyd' |
    Remove-Item -Force

$vendorRoot = Join-Path $destinationSkill 'vendor'
if (Test-Path $vendorRoot) {
    Get-ChildItem -Path $vendorRoot -Recurse -File -Force -Filter '.gitignore' |
        Remove-Item -Force
}

$accountsTemplate = Join-Path $destinationSkill 'config\accounts.template.json'
$vendorAccounts = Join-Path $destinationSkill 'vendor\XiaohongshuSkills\config\accounts.json'

if ((Test-Path $accountsTemplate) -and (Test-Path (Split-Path -Parent $vendorAccounts))) {
    Copy-Item -Path $accountsTemplate -Destination $vendorAccounts -Force
}

Write-Host "Synced skill '$SkillName' from '$SourceWorkspace' to '$DestinationWorkspace'."
