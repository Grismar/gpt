$originalWorkingDirectory = Get-Location

$scriptDirectory = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
$parentDirectory = Split-Path -Path $scriptDirectory -Parent
Set-Location -Path $parentDirectory

# configuration
$envFolder = ".\.venv"

# check if a folder is a Conda virtual environment
function Test-CondaEnv {
    param (
        [string]$EnvPath
    )
    Test-Path "$EnvPath\conda-meta"
}

# check if a folder is a virtualenv virtual environment
function Test-Venv {
    param (
        [string]$EnvPath
    )
    (Test-Path "$EnvPath\Scripts\Activate") -and (Test-Path "$EnvPath\pyvenv.cfg")
}

function Invoke-Deactivate {
    param (
        [Boolean]$conda,
        [Boolean]$silent = $false
    )
    if ($conda)
    {
        # deactivate the conda environment
        if (-not $silent)
        {
            Write-Host "> conda deactivate"
        }
        & conda deactivate
    }
    else
    {
        # deactivate the venv
        if (-not $silent)
        {
            Write-Host "> deactivate"
        }
        & deactivate
    }
}


if ((Test-Path "$envFolder") -and (Test-CondaEnv $envFolder)) {
    # deactivate the conda environment
    Invoke-Deactivate -conda $true

    Write-Host "Conda environment found. Removing..."
    Write-Host "> conda env remove --yes --prefix $envFolder"
    conda env remove --yes --prefix $envFolder
}

if ((Test-Path "$envFolder") -and (Test-Venv $envFolder)) {
    # deactivate the virtualenv environment
    Invoke-Deactivate -conda $false

    Write-Host "Virtualenv environment found. Removing..."
    Write-Host "> Remove-Item $envFolder -Recurse -Force -Confirm:`$false"
    Remove-Item $envFolder -Recurse -Force -Confirm:$false
}

Set-Location $originalWorkingDirectory
