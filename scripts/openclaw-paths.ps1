function Add-UniquePathCandidate {
    param(
        [System.Collections.Generic.List[string]]$Candidates,
        [string]$Path
    )

    if (-not $Path) {
        return
    }

    $trimmed = $Path.Trim()
    if (-not $trimmed) {
        return
    }

    $normalized = $trimmed.TrimEnd('\', '/')
    if (-not $Candidates.Contains($normalized)) {
        $Candidates.Add($normalized)
    }
}

function Get-FileSystemDriveRoots {
    $roots = New-Object 'System.Collections.Generic.List[string]'
    foreach ($drive in (Get-PSDrive -PSProvider FileSystem | Sort-Object Name)) {
        if ($drive.Root) {
            Add-UniquePathCandidate -Candidates $roots -Path $drive.Root
        }
    }
    return $roots
}

function Resolve-FullPath {
    param(
        [string]$Path
    )

    if (-not $Path) {
        return $null
    }

    $resolved = Resolve-Path -LiteralPath $Path -ErrorAction SilentlyContinue
    if ($resolved) {
        return $resolved.Path
    }

    return [System.IO.Path]::GetFullPath($Path)
}

function Get-DefaultOpenClawRoot {
    param(
        [string]$SeedPath = ''
    )

    if ($SeedPath) {
        $seedFullPath = Resolve-FullPath -Path $SeedPath
        $seedDrive = [System.IO.Path]::GetPathRoot($seedFullPath)
        if ($seedDrive) {
            return Join-Path $seedDrive 'OpenClaw'
        }
    }

    $systemDrive = $env:SystemDrive
    if ($systemDrive) {
        return Join-Path $systemDrive 'OpenClaw'
    }

    foreach ($driveRoot in (Get-FileSystemDriveRoots)) {
        return (Join-Path $driveRoot 'OpenClaw')
    }

    throw 'Unable to determine a default OpenClaw root.'
}

function Get-OpenClawWorkspaceCandidates {
    param(
        [string]$PreferredWorkspace = '',
        [string]$SeedPath = ''
    )

    $candidates = New-Object 'System.Collections.Generic.List[string]'

    Add-UniquePathCandidate -Candidates $candidates -Path $PreferredWorkspace
    Add-UniquePathCandidate -Candidates $candidates -Path $env:OPENCLAW_WORKSPACE

    if ($env:OPENCLAW_ROOT) {
        Add-UniquePathCandidate -Candidates $candidates -Path (Join-Path $env:OPENCLAW_ROOT '.openclaw\workspace')
    }

    if ($env:USERPROFILE) {
        Add-UniquePathCandidate -Candidates $candidates -Path (Join-Path $env:USERPROFILE '.openclaw\workspace')
    }

    foreach ($driveRoot in (Get-FileSystemDriveRoots)) {
        Add-UniquePathCandidate -Candidates $candidates -Path (Join-Path $driveRoot 'OpenClaw\.openclaw\workspace')
    }

    if ($SeedPath) {
        Add-UniquePathCandidate -Candidates $candidates -Path (Join-Path (Get-DefaultOpenClawRoot -SeedPath $SeedPath) '.openclaw\workspace')
    }

    return $candidates
}

function Resolve-OpenClawWorkspacePath {
    param(
        [string]$PreferredWorkspace = '',
        [string]$SeedPath = '',
        [switch]$AllowCreate
    )

    if ($PreferredWorkspace) {
        $preferredFullPath = Resolve-FullPath -Path $PreferredWorkspace
        if ((Test-Path -LiteralPath $preferredFullPath) -or $AllowCreate) {
            if (-not (Test-Path -LiteralPath $preferredFullPath)) {
                New-Item -ItemType Directory -Force -Path $preferredFullPath | Out-Null
            }
            return (Resolve-Path -LiteralPath $preferredFullPath).Path
        }
    }

    $candidates = Get-OpenClawWorkspaceCandidates -PreferredWorkspace $PreferredWorkspace -SeedPath $SeedPath
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    if ($AllowCreate) {
        $target = $PreferredWorkspace
        if (-not $target) {
            $target = $env:OPENCLAW_WORKSPACE
        }
        if (-not $target) {
            $openClawRoot = if ($env:OPENCLAW_ROOT) { $env:OPENCLAW_ROOT } else { Get-DefaultOpenClawRoot -SeedPath $SeedPath }
            $target = Join-Path $openClawRoot '.openclaw\workspace'
        }

        New-Item -ItemType Directory -Force -Path $target | Out-Null
        return (Resolve-Path -LiteralPath $target).Path
    }

    $searched = ($candidates | ForEach-Object { "'$_'" }) -join ', '
    throw "Unable to locate OpenClaw workspace. Searched: $searched"
}

function Resolve-OpenClawRootFromWorkspace {
    param(
        [string]$WorkspacePath
    )

    $workspaceFullPath = Resolve-FullPath -Path $WorkspacePath
    if (-not $workspaceFullPath) {
        throw 'Workspace path is required.'
    }

    return [System.IO.Path]::GetFullPath((Join-Path $workspaceFullPath '..\..'))
}

function Get-OpenClawStateTmpCandidates {
    param(
        [string]$PreferredStateTmp = '',
        [string]$WorkspacePath = '',
        [string]$SeedPath = ''
    )

    $candidates = New-Object 'System.Collections.Generic.List[string]'

    Add-UniquePathCandidate -Candidates $candidates -Path $PreferredStateTmp
    Add-UniquePathCandidate -Candidates $candidates -Path $env:OPENCLAW_STATE_TMP

    if ($WorkspacePath) {
        Add-UniquePathCandidate -Candidates $candidates -Path (Join-Path (Resolve-OpenClawRootFromWorkspace -WorkspacePath $WorkspacePath) 'state\tmp')
    }

    if ($env:OPENCLAW_ROOT) {
        Add-UniquePathCandidate -Candidates $candidates -Path (Join-Path $env:OPENCLAW_ROOT 'state\tmp')
    }

    foreach ($driveRoot in (Get-FileSystemDriveRoots)) {
        Add-UniquePathCandidate -Candidates $candidates -Path (Join-Path $driveRoot 'OpenClaw\state\tmp')
    }

    if ($SeedPath) {
        Add-UniquePathCandidate -Candidates $candidates -Path (Join-Path (Get-DefaultOpenClawRoot -SeedPath $SeedPath) 'state\tmp')
    }

    return $candidates
}

function Resolve-OpenClawStateTmpPath {
    param(
        [string]$PreferredStateTmp = '',
        [string]$WorkspacePath = '',
        [string]$SeedPath = ''
    )

    $candidates = Get-OpenClawStateTmpCandidates -PreferredStateTmp $PreferredStateTmp -WorkspacePath $WorkspacePath -SeedPath $SeedPath
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    if ($PreferredStateTmp) {
        return (Resolve-FullPath -Path $PreferredStateTmp)
    }

    if ($env:OPENCLAW_STATE_TMP) {
        return (Resolve-FullPath -Path $env:OPENCLAW_STATE_TMP)
    }

    if ($WorkspacePath) {
        return (Resolve-FullPath -Path (Join-Path (Resolve-OpenClawRootFromWorkspace -WorkspacePath $WorkspacePath) 'state\tmp'))
    }

    return (Resolve-FullPath -Path (Join-Path (Get-DefaultOpenClawRoot -SeedPath $SeedPath) 'state\tmp'))
}

function Resolve-OpenClawReviewPath {
    param(
        [string]$ReviewDirectoryName,
        [string]$StateTmpPath = ''
    )

    if (-not $ReviewDirectoryName) {
        throw 'ReviewDirectoryName is required.'
    }

    $resolvedStateTmp = if ($StateTmpPath) { Resolve-FullPath -Path $StateTmpPath } else { Resolve-OpenClawStateTmpPath }
    return (Resolve-FullPath -Path (Join-Path $resolvedStateTmp $ReviewDirectoryName))
}

function Test-DirectoryHasContent {
    param(
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return $false
    }

    return $null -ne (Get-ChildItem -LiteralPath $Path -Force -ErrorAction SilentlyContinue | Select-Object -First 1)
}
