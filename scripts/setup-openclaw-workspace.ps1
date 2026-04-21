param(
    [string]$WorkspacePath = '',
    [string]$RepoUrl = '',
    [switch]$SkipSetup,
    [switch]$SkipCheck
)

$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'openclaw-paths.ps1')

function Resolve-GitCommand {
    $git = Get-Command git -ErrorAction SilentlyContinue
    if ($git) {
        return $git.Source
    }

    throw 'git is not available in PATH.'
}

function Resolve-PythonCommand {
    $supportedVersions = @('3.12', '3.11')
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        foreach ($version in $supportedVersions) {
            try {
                $resolved = & $pyLauncher.Source "-$version" -c "import sys; print(sys.executable)" 2>$null
                if ($LASTEXITCODE -eq 0 -and $resolved) {
                    return $resolved.Trim()
                }
            }
            catch {
            }
        }
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        $version = (& $python.Source -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')" 2>$null).Trim()
        if ($LASTEXITCODE -eq 0 -and ($supportedVersions -contains $version)) {
            return $python.Source
        }
    }

    throw 'A supported Python runtime was not found. Install Python 3.11 or 3.12, or make it available through `py -3.11` / `py -3.12`.'
}

function Resolve-PowerShellCommand {
    $pwsh = Get-Command pwsh -ErrorAction SilentlyContinue
    if ($pwsh) {
        return $pwsh.Source
    }

    $powershell = Get-Command powershell -ErrorAction SilentlyContinue
    if ($powershell) {
        return $powershell.Source
    }

    throw 'Neither pwsh nor powershell is available in PATH.'
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

function Get-GitOriginUrl {
    param(
        [string]$GitExe,
        [string]$RepoPath
    )

    if (-not (Test-Path -LiteralPath (Join-Path $RepoPath '.git'))) {
        return ''
    }

    try {
        $origin = & $GitExe -C $RepoPath remote get-url origin 2>$null
    }
    catch {
        return ''
    }

    if ($LASTEXITCODE -eq 0) {
        return $origin.Trim()
    }

    return ''
}

function Remove-EmptyDirectoryIfPresent {
    param(
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }

    if (-not (Test-DirectoryHasContent -Path $Path)) {
        Remove-Item -LiteralPath $Path -Force
    }
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$gitExe = Resolve-GitCommand
$pythonExe = Resolve-PythonCommand
$powerShellExe = Resolve-PowerShellCommand

if (-not $RepoUrl) {
    $RepoUrl = Get-GitOriginUrl -GitExe $gitExe -RepoPath $repoRoot
    if (-not $RepoUrl) {
        $RepoUrl = $repoRoot
    }
}

$repoParent = Split-Path -Parent $repoRoot
$isCurrentRepoWorkspace = ((Split-Path -Leaf $repoRoot) -eq 'workspace') -and ((Split-Path -Leaf $repoParent) -eq '.openclaw')

if ($isCurrentRepoWorkspace) {
    $targetWorkspace = $repoRoot
    Write-Host "Current repository is already inside an OpenClaw workspace: $targetWorkspace"
}
else {
    $targetWorkspace = Resolve-OpenClawWorkspacePath -PreferredWorkspace $WorkspacePath -SeedPath $repoRoot -AllowCreate
    Write-Host "Resolved OpenClaw workspace: $targetWorkspace"
}

$repoRootFull = Resolve-FullPath -Path $repoRoot
$targetWorkspaceFull = Resolve-FullPath -Path $targetWorkspace
$workspaceInUse = $targetWorkspaceFull

if ($repoRootFull -ne $targetWorkspaceFull) {
    $targetOrigin = Get-GitOriginUrl -GitExe $gitExe -RepoPath $targetWorkspaceFull

    if ($targetOrigin -and ($targetOrigin -eq $RepoUrl)) {
        Write-Host "Existing workspace already points to the same repository, reusing checkout."
        $workspaceInUse = $targetWorkspaceFull
    }
    else {
        if (Test-DirectoryHasContent -Path $targetWorkspaceFull) {
            $backupName = 'workspace_backup_{0}' -f (Get-Date -Format 'yyyyMMdd-HHmmss')
            $backupPath = Join-Path (Split-Path -Parent $targetWorkspaceFull) $backupName
            Write-Host "Backing up existing workspace to: $backupPath"
            Move-Item -LiteralPath $targetWorkspaceFull -Destination $backupPath
        }
        else {
            Remove-EmptyDirectoryIfPresent -Path $targetWorkspaceFull
        }

        Write-Host "Cloning $RepoUrl into $targetWorkspaceFull"
        Invoke-CheckedCommand -Command $gitExe -Arguments @('clone', $RepoUrl, $targetWorkspaceFull) -Label 'git clone'
        $workspaceInUse = $targetWorkspaceFull
    }
}

if (-not $SkipSetup) {
    $setupScript = Join-Path $workspaceInUse 'scripts\setup-new-machine.ps1'
    Write-Host "Running workspace setup: $setupScript"
    Invoke-CheckedCommand -Command $powerShellExe -Arguments @('-ExecutionPolicy', 'Bypass', '-File', $setupScript, '-WorkspaceRoot', $workspaceInUse) -Label 'workspace setup'
}

if (-not $SkipCheck) {
    $checkScript = Join-Path $workspaceInUse 'skills\xhs-trend-to-publish\scripts\check_environment.py'
    Write-Host "Running environment check: $checkScript"
    Invoke-CheckedCommand -Command $pythonExe -Arguments @($checkScript) -Label 'environment check'
}

Write-Host "OpenClaw workspace is ready at: $workspaceInUse"
