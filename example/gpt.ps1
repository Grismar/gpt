$scriptDirectory = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
$gptScript = Join-Path -Path $scriptDirectory -ChildPath "gpt/gpt.ps1"

$pipedData = $input | Out-String
if (-not [string]::IsNullOrEmpty($pipedData)) {
    $pipedData | & $gptScript @args
} else {
    & $gptScript @args
}
