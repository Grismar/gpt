# GPT for PowerShell

Calls the OpenAI GPT API from PowerShell.

## Installation

Make sure a virtual environment with the requirements is set up by running

```powershell
scripts\setup.ps1
```

This will create a local Conda environment if you have `conda` available, or try to use `python`  on the path instead to create a virtualenv environment. If you don't want to use Conda, or want to avoid using the Python that happens to be on the path, specifiy the Python you do want to use:

```powershell
scripts\setup.ps1 -python "C:\path\to\python.exe"
``` 

This will create a virtualenv environment.

Once created, the requirements will from [requirements.txt](requirements.txt) will be installed.

Before you can use the script, you need to provide the API key once:
```commandline
PS C:\Users\john.doe> gpt just a test
No API Key found. Please provide an API Key once (`--api_key <my API key>`).

PS C:\Users\john.doe> gpt just a test --api_key <an actual API key here>
Sure, let me know if you need concise answers or examples formatted for PowerShell CLI.

PS C:\Users\john.doe> gpt what is the meaning of life?
The meaning of life is a philosophical question concerning the purpose and significance of human existence.

Example for displaying in PowerShell:

 Write-Output "The meaning of life is a philosophical question concerning the purpose and significance of human
 existence."

PS C:\Users\john.doe>
```
If you want to remove the API key from secure storage, you can delete it easily:
```commandline
PS C:\Users\john.doe> gpt --delete-api-key
```
You can even provide and delete the API key in a single command, to avoid storing it at all, but remember that doing so may have it end up in your command history, so you may need to remove that yourself:
```powershell
PS C:\Users\john.doe> gpt -k <an actual API key here> -dak -q "How do I remove the last command from my command history?"

 Remove-Item -Path (Get-PSReadlineOption).HistorySavePath -ErrorAction SilentlyContinue ; Add-Content -Path
 (Get-PSReadlineOption).HistorySavePath -Value (Get-History -Count (Get-History).Count -PipelineVariable hist |
 Where-Object { $_.ID -ne $hist[$hist.Count-1].ID }) ; Clear-History

PS C:\Users\john.doe>
```

If you want to refer to `gpt.ps1` from other scripts, keep in mind that piping data to the script will require some additional code in the script. Examples are provided in the `example` folder.

## Usage

Once installed, you can simply run `gpt.ps1` to start the script, which will print the help message if you don't provide arguments.

```commandline
PS C:\Users\john.doe> gpt
```

Here's an example interaction with the script:
```none
PS C:\Users\john.doe> gpt how can I upload a file over ssh from powershell?
To upload a file over SSH from PowerShell, use the scp command from OpenSSH:

 scp C:\path\to\localfile.txt user@remotehost:/path/to/remotedir/

PS C:\Users\john.doe> gpt what if I need to use a .pem? -c
To upload a file over SSH from PowerShell using a .pem key, specify the key with the -i option:

 scp -i C:\path\to\keyfile.pem C:\path\to\localfile.txt user@remotehost:/path/to/remotedir/

PS C:\Users\john.doe> gpt how can I tell what executable is started by a command?
You can use the Get-Command cmdlet to determine the executable started by a command.

 Get-Command <command-name>

For instance, to find the executable started by the notepad command:

 Get-Command notepad

PS C:\Users\john.doe> gpt --list
1> how can I upload a file over ssh from powershell?
2> how can I tell what executable is started by a command?
Last conversation: 2
PS C:\Users\jaap.vandervelde> gpt --replay 1
1> "how can I upload a file over ssh from powershell?"
To upload a file over SSH from PowerShell, use the scp command from OpenSSH:

 scp C:\path\to\localfile.txt user@remotehost:/path/to/remotedir/

prompt> "what if I need to use a .pem?"
To upload a file over SSH from PowerShell using a .pem key, specify the key with the -i option:

 scp -i C:\path\to\keyfile.pem C:\path\to\localfile.txt user@remotehost:/path/to/remotedir/

PS C:\Users\john.doe> gpt -c 1 -q "does this also work for downloding files?"
Yes, you can also download files using scp with similar syntax:

 scp -i C:\path\to\keyfile.pem user@remotehost:/path/to/remotefile.txt C:\path\to\localdir\

PS C:\Users\john.doe>
```
