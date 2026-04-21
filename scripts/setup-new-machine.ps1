param(
    [string]$WorkspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
)

$ErrorActionPreference = 'Stop'

function Resolve-PythonCommand {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return $python.Source
    }

    throw 'python is not available in PATH.'
}

function Resolve-BunCommand {
    $bun = Get-Command bun -ErrorAction SilentlyContinue
    if ($bun) {
        return @{
            Command = $bun.Source
            Arguments = @()
        }
    }

    $npx = Get-Command npx -ErrorAction SilentlyContinue
    if ($npx) {
        return @{
            Command = $npx.Source
            Arguments = @('-y', 'bun')
        }
    }

    throw 'Neither bun nor npx is available in PATH.'
}

function Invoke-CheckedCommand {
    param(
        [string]$Command,
        [string[]]$Arguments,
        [string]$Label
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE."
    }
}

function Get-PipInstallArgs {
    param(
        [string]$PythonExe,
        [string]$RequirementsFile,
        [string[]]$SkipPatterns = @()
    )

    $effectiveRequirements = $RequirementsFile
    if ($SkipPatterns.Count -gt 0) {
        $filtered = Get-Content $RequirementsFile | Where-Object {
            $line = $_.Trim()
            if (!$line) {
                return $true
            }
            foreach ($pattern in $SkipPatterns) {
                if ($line -match $pattern) {
                    return $false
                }
            }
            return $true
        }

        $effectiveRequirements = Join-Path ([System.IO.Path]::GetTempPath()) ("codex-reqs-{0}.txt" -f [guid]::NewGuid().ToString('N'))
        Set-Content -Path $effectiveRequirements -Value $filtered -Encoding UTF8
    }

    $isVirtualEnv = (& $PythonExe -c "import sys; print('1' if sys.prefix != getattr(sys, 'base_prefix', sys.prefix) else '0')").Trim()
    $args = @('-m', 'pip', 'install')
    if ($isVirtualEnv -ne '1') {
        $args += '--user'
    }
    $args += @('-r', $effectiveRequirements)
    return @{
        Arguments = $args
        EffectiveRequirements = $effectiveRequirements
        UsedTempFile = $effectiveRequirements -ne $RequirementsFile
    }
}

function Install-PythonRequirements {
    param(
        [string]$PythonExe,
        [string]$RequirementsFile,
        [string]$Label,
        [string[]]$SkipPatterns = @()
    )

    if (!(Test-Path $RequirementsFile)) {
        Write-Host "$Label requirements not found, skipping."
        return
    }

    $pipPlan = Get-PipInstallArgs -PythonExe $PythonExe -RequirementsFile $RequirementsFile -SkipPatterns $SkipPatterns
    Write-Host "Installing $Label Python dependencies..."
    try {
        Invoke-CheckedCommand -Command $PythonExe -Arguments $pipPlan.Arguments -Label "$Label pip install"
    }
    finally {
        if ($pipPlan.UsedTempFile -and (Test-Path $pipPlan.EffectiveRequirements)) {
            Remove-Item $pipPlan.EffectiveRequirements -Force
        }
    }
}

function Install-PythonPlaywrightChromium {
    param(
        [string]$PythonExe,
        [string]$Label
    )

    Write-Host "Installing Chromium browser for $Label..."
    Invoke-CheckedCommand -Command $PythonExe -Arguments @('-m', 'playwright', 'install', 'chromium') -Label "$Label playwright install"
}

function Ensure-WorkspaceDirectories {
    param(
        [string]$WorkspaceRoot
    )

    $paths = @(
        'skills\xhs-trend-to-publish\data\briefs',
        'skills\xhs-trend-to-publish\data\douyin\detail-cache',
        'skills\xhs-trend-to-publish\data\douyin\enriched',
        'skills\xhs-trend-to-publish\data\douyin\json',
        'skills\xhs-trend-to-publish\data\douyin\raw',
        'skills\xhs-trend-to-publish\data\drafts',
        'skills\xhs-trend-to-publish\data\merged',
        'skills\xhs-trend-to-publish\data\metrics',
        'skills\xhs-trend-to-publish\data\publish-results',
        'skills\xhs-trend-to-publish\data\reading-pool',
        'skills\xhs-trend-to-publish\data\renders',
        'skills\xhs-trend-to-publish\data\runs',
        'skills\xhs-trend-to-publish\data\trends\enriched',
        'skills\xhs-trend-to-publish\data\trends\home-feeds',
        'skills\xhs-trend-to-publish\data\trends\raw',
        'skills\xhs-trend-to-publish\data\trends\scored',
        'skills\xhs-trend-to-publish\data\wechat-drafts'
    )

    foreach ($relativePath in $paths) {
        $fullPath = Join-Path $WorkspaceRoot $relativePath
        New-Item -ItemType Directory -Force -Path $fullPath | Out-Null
    }
}

$pythonExe = Resolve-PythonCommand
$autoRedbookRequirements = Join-Path $WorkspaceRoot 'skills\xhs-trend-to-publish\vendor\Auto-Redbook-Skills\requirements.txt'
$xhsSkillsRequirements = Join-Path $WorkspaceRoot 'skills\xhs-trend-to-publish\vendor\XiaohongshuSkills\requirements.txt'
$mediaCrawlerRoot = Join-Path $WorkspaceRoot 'skills\xhs-trend-to-publish\vendor\MediaCrawler'
$wechatScriptsRoot = Join-Path $WorkspaceRoot 'skills\baoyu-post-to-wechat\scripts'

Ensure-WorkspaceDirectories -WorkspaceRoot $WorkspaceRoot
Write-Host "Skipping upstream-only Auto-Redbook dependency xhs>=0.4.0; current workflow publishes through XiaohongshuSkills."
Install-PythonRequirements -PythonExe $pythonExe -RequirementsFile $autoRedbookRequirements -Label 'Auto-Redbook-Skills' -SkipPatterns @('^xhs>=0\.4\.0$')
Install-PythonRequirements -PythonExe $pythonExe -RequirementsFile $xhsSkillsRequirements -Label 'XiaohongshuSkills'
Install-PythonPlaywrightChromium -PythonExe $pythonExe -Label 'workspace Python environment'

if (Test-Path $mediaCrawlerRoot) {
    Write-Host "Installing MediaCrawler dependencies with uv sync..."
    Push-Location $mediaCrawlerRoot
    try {
        Invoke-CheckedCommand -Command 'uv' -Arguments @('sync') -Label 'MediaCrawler uv sync'
        Write-Host "Installing Chromium browser for MediaCrawler..."
        Invoke-CheckedCommand -Command 'uv' -Arguments @('run', 'python', '-m', 'playwright', 'install', 'chromium') -Label 'MediaCrawler playwright install'
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Host "MediaCrawler not found, skipping uv sync."
}

if (Test-Path $wechatScriptsRoot) {
    $bunCommand = Resolve-BunCommand
    Write-Host "Installing baoyu-post-to-wechat dependencies..."
    Push-Location $wechatScriptsRoot
    try {
        Invoke-CheckedCommand -Command $bunCommand.Command -Arguments @($bunCommand.Arguments + @('install')) -Label 'baoyu-post-to-wechat bun install'
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Host "baoyu-post-to-wechat scripts not found, skipping bun install."
}

Write-Host "Setup complete. Next step: python skills/xhs-trend-to-publish/scripts/check_environment.py"
