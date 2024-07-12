@echo off
powershell -Command "$inputData = [Console]::In.ReadToEnd(); if (-not [string]::IsNullOrEmpty($inputData)) { $inputData | . '%~dp0/gpt/gpt.ps1' %* } else { . '%~dp0/gpt/gpt.ps1' %* }"
