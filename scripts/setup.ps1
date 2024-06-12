param(
    [Parameter(Mandatory=$false)]
    [string]$python = $null
)

$originalWorkingDirectory = Get-Location

$scriptDirectory = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
$parentDirectory = Split-Path -Path $scriptDirectory -Parent
Set-Location -Path $parentDirectory

# configuration
$envFolder = ".\.venv"
$requirementsFile = "requirements.txt"

# check if a command exists
function Test-Command {
    param (
        [string]$Command
    )
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

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

# check if conda is available
if ((-not $python) -and (Test-Command "conda")) {
    Write-Host "Conda is available."
    # check if the conda environment exists and is valid
    if (-not (Test-Path "$envFolder") -or -not (Test-CondaEnv $envFolder)) {
        Write-Host "Conda environment not found or invalid. Creating..."
        Write-Host "> conda create --yes --prefix $envFolder python=3.10"
        conda create --yes --prefix $envFolder python=3.10
    } else {
        Write-Host "Conda environment found and valid."
    }
    # activate the conda environment
    Write-Host "> conda activate $envFolder"
    conda activate $envFolder
    $conda = $true
} else {
    if ($null -eq $python) {
        Write-Host "Conda is not available, looking for Python."
        $python = "python"
    }
    # check if python is available
    if (Test-Command $python) {
        # check if Python is not the MS Store app
        $pythonPath = (Get-Command $python).Source
        if ($pythonPath -notlike "*Microsoft*") {
            Write-Host "Python is available as $python."
            # check if the venv exists and is valid
            if (-Not (Test-Path "$envFolder") -or -Not (Test-Venv $envFolder)) {
                Write-Host "Virtual environment not found or invalid. Creating..."
                Write-Host "> $python -m venv $envFolder"
                & $python -m venv $envFolder
            } else {
                Write-Host "Virtual environment found and valid."
            }
            # activate the venv
            Write-Host "> $envFolder\Scripts\activate"
            & $envFolder\Scripts\activate
            $conda = $false
        } else {
            Write-Error "Python command leads to the Microsoft Store app."
            Write-Error "Either install Conda (install miniforge and run ``conda init powershell``) or install Python (add it to the path, or pass it on the command line, e.g. ``setup.ps -python c:\path\python.exe``)" -ErrorAction Stop
        }
    } else {
        Write-Error "Error: Neiter Conda nor Python is available."
        Write-Error "Either install Conda (install miniforge and run ``conda init powershell``) or install Python (add it to the path, or pass it on the command line, e.g. ``setup.ps -python c:\path\python.exe``)" -ErrorAction Stop
    }
}

# install requirements
if (Test-Path $requirementsFile) {
    Write-Host "Installing requirements..."
    Write-Host "> pip install -r $requirementsFile"
    pip install -r $requirementsFile
} else {
    Invoke-Deactivate -conda $conda
    Write-Error "Requirements file not found." -ErrorAction Stop
}

Invoke-Deactivate -conda $conda

Set-Location $originalWorkingDirectory
