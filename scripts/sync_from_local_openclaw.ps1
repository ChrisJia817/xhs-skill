param(
    [string]$SourceWorkspace = '',
    [string]$DestinationWorkspace = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path,
    [string]$SkillName = 'xhs-trend-to-publish',
    [string]$MediaCrawlerRoot = '',
    [string]$BaoyuSkillsRoot = ''
)

$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'openclaw-paths.ps1')

$SourceWorkspace = Resolve-OpenClawWorkspacePath -PreferredWorkspace $SourceWorkspace -SeedPath $DestinationWorkspace
$resolvedStateTmp = Resolve-OpenClawStateTmpPath -WorkspacePath $SourceWorkspace -SeedPath $DestinationWorkspace

if (-not $MediaCrawlerRoot) {
    $MediaCrawlerRoot = Resolve-OpenClawReviewPath -ReviewDirectoryName 'mediacrawler-review' -StateTmpPath $resolvedStateTmp
}
elseif (Test-Path -LiteralPath $MediaCrawlerRoot) {
    $MediaCrawlerRoot = (Resolve-Path -LiteralPath $MediaCrawlerRoot).Path
}
else {
    $MediaCrawlerRoot = Resolve-FullPath -Path $MediaCrawlerRoot
}

if (-not $BaoyuSkillsRoot) {
    $BaoyuSkillsRoot = Resolve-OpenClawReviewPath -ReviewDirectoryName 'baoyu-skills-review' -StateTmpPath $resolvedStateTmp
}
elseif (Test-Path -LiteralPath $BaoyuSkillsRoot) {
    $BaoyuSkillsRoot = (Resolve-Path -LiteralPath $BaoyuSkillsRoot).Path
}
else {
    $BaoyuSkillsRoot = Resolve-FullPath -Path $BaoyuSkillsRoot
}

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

$mediaCrawlerDestination = Join-Path $destinationSkill 'vendor\MediaCrawler'
if (Test-Path $MediaCrawlerRoot) {
    if (Test-Path $mediaCrawlerDestination) {
        Remove-Item -Path $mediaCrawlerDestination -Recurse -Force
    }

    New-Item -ItemType Directory -Force -Path $mediaCrawlerDestination | Out-Null
    Copy-Item -Path (Join-Path $MediaCrawlerRoot '*') -Destination $mediaCrawlerDestination -Recurse -Force

    $mediaCrawlerRemovePaths = @(
        (Join-Path $mediaCrawlerDestination '.git'),
        (Join-Path $mediaCrawlerDestination '.venv'),
        (Join-Path $mediaCrawlerDestination 'browser_data')
    )

    foreach ($path in $mediaCrawlerRemovePaths) {
        if (Test-Path $path) {
            Remove-Item -Path $path -Recurse -Force
        }
    }

    Get-ChildItem -Path $mediaCrawlerDestination -Recurse -Directory -Force |
        Where-Object { $_.Name -eq '__pycache__' } |
        Remove-Item -Recurse -Force

    Get-ChildItem -Path $mediaCrawlerDestination -Recurse -File -Force -Include '*.pyc', '*.pyo', '*.pyd' |
        Remove-Item -Force
}

$baoyuSkillSource = Join-Path $BaoyuSkillsRoot 'skills\baoyu-post-to-wechat'
$baoyuSkillDestination = Join-Path $DestinationWorkspace 'skills\baoyu-post-to-wechat'

if (Test-Path $baoyuSkillSource) {
    if (Test-Path $baoyuSkillDestination) {
        Remove-Item -Path $baoyuSkillDestination -Recurse -Force
    }

    New-Item -ItemType Directory -Force -Path (Join-Path $baoyuSkillDestination 'scripts\vendor') | Out-Null
    Copy-Item -Path (Join-Path $baoyuSkillSource '*') -Destination $baoyuSkillDestination -Recurse -Force

    $baoyuVendorPackages = @(
        @{ Source = (Join-Path $BaoyuSkillsRoot 'packages\baoyu-chrome-cdp'); Destination = (Join-Path $baoyuSkillDestination 'scripts\vendor\baoyu-chrome-cdp') },
        @{ Source = (Join-Path $BaoyuSkillsRoot 'packages\baoyu-md'); Destination = (Join-Path $baoyuSkillDestination 'scripts\vendor\baoyu-md') }
    )

    foreach ($pkg in $baoyuVendorPackages) {
        if (Test-Path $pkg.Source) {
            if (Test-Path $pkg.Destination) {
                Remove-Item -Path $pkg.Destination -Recurse -Force
            }
            New-Item -ItemType Directory -Force -Path $pkg.Destination | Out-Null
            Copy-Item -Path (Join-Path $pkg.Source '*') -Destination $pkg.Destination -Recurse -Force
        }
    }

    $baoyuPackageJson = Join-Path $baoyuSkillDestination 'scripts\package.json'
    if (Test-Path $baoyuPackageJson) {
        $packageJson = Get-Content $baoyuPackageJson -Raw | ConvertFrom-Json
        $packageJson.dependencies.'baoyu-chrome-cdp' = 'file:./vendor/baoyu-chrome-cdp'
        $packageJson.dependencies.'baoyu-md' = 'file:./vendor/baoyu-md'
        $packageJson | ConvertTo-Json -Depth 10 | Set-Content $baoyuPackageJson
    }
}

Write-Host "Synced skill '$SkillName' from '$SourceWorkspace' to '$DestinationWorkspace'."
