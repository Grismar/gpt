$originalDirectory = Get-Location

$scriptDirectory = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
Set-Location -Path $scriptDirectory

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
    $conda = $true
    & conda activate $envFolder
} else {
    $conda = $false
    & .\.venv\scripts\activate
}

$pythonArgs = @()
foreach ($arg in $args) {
    $pythonArgs += $arg
}

# piped data gets cached, but this is not an issue since it needs to be fully read before passsing it to the API
$pipedData = $input | Out-String
if (-not [string]::IsNullOrEmpty($pipedData)) {
    $pipedData | & python .\gpt.py @pythonArgs
} else {
    & python .\gpt.py @pythonArgs
}

Invoke-Deactivate -conda $conda -silent $true

Set-Location -Path $originalDirectory
