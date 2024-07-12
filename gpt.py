import os
import sys
import fileinput
import win32cred
import json
from pathlib import Path

from openai import OpenAI
from rich.markdown import Markdown
from rich.console import Console

from conffu import Config


INITIAL_PROMPT = """
Please provide concise answers with a minimum of added explanation, 
keeping in mind that they will be displayed on a text console from a CLI, 
specifically PowerShell. Format responses as a single line description 
if possible, or use only a few, and provide any code or examples on a new line. 
Multiple examples should be on separate lines. If an answer would include 
Get-WmiObject, use Get-CimInstance instead. If additional text is provided,
base your answer on that content.
"""


def print_help():
    print('Usage: gpt.py [query] [options]')
    print('Options:')
    print('  --api_key / --key / -k <key>')
    print('    Provide an OpenAI API key (stored securely).')
    print('  --continue / --c / --cont <conversation_id>')
    print('    Continue a conversation with the given ID.')
    print('  --delete / --del / -d <conversation_id [conversation_id ...]>')
    print('    Delete conversations with given ID(s).')
    print('  --delete_api_key / --dak')
    print('    Delete the stored API key.')
    print('  --file / -f <filename>')
    print('    Attach the contents of the file to the conversation.')
    print('  --help / -h')
    print('    Print this help message.')
    print('  --list / -l')
    print('    List all stored conversations.')
    print('  --model / -m <model>')
    print('    Specify the model to use. Options are: gpt-3.5, gpt-4, gpt-4o')
    print('  --query / -q <query>')
    print('    Provide the query to start or continue a conversation.')
    print('  --replay / -r / -p / <conversation_id>')
    print('    Replay a conversation with the given ID.')
    print('  --reset / -x [<conversation_id [conversation_id ...]>]')
    print('    Reset stored conversations, retain conversations with any given ID(s).')
    print('Examples:')
    print('  gpt how can I upload a file over ssh from powershell?')
    print('  gpt "what if I want to use a .pem?" -c')
    print('  gpt -c -q "how can I get a progress indicator?"')
    print('Note that putting the query at the start is equivalent to using `--query`.')
    print('Quotes are needed to group the query together when it contains spaces.\n')
    exit(0)


def store_api_key(target_name: str, api_key_value: str) -> None:
    credential = {
        'Type': win32cred.CRED_TYPE_GENERIC,
        'TargetName': target_name,
        'CredentialBlob': api_key_value,
        'Persist': win32cred.CRED_PERSIST_LOCAL_MACHINE
    }
    win32cred.CredWrite(credential, 0)


def retrieve_api_key(target_name: str) -> str | None:
    try:
        credential = win32cred.CredRead(target_name, win32cred.CRED_TYPE_GENERIC, 0)
        return credential['CredentialBlob'].decode('utf16')
    except (NameError, Exception) as e:
        if isinstance(e, NameError) or (hasattr(e, 'funcname') and e.funcname == 'CredRead'):
            return None
        raise e


def delete_api_key(target_name: str) -> None:
    try:
        win32cred.CredDelete(target_name, win32cred.CRED_TYPE_GENERIC, 0)
    except NameError:
        pass


def manage_api_key(cfg: Config) -> str:
    if 'api_key' in cfg:
        # use the API key provided on the CLI
        api_key = cfg['api_key']
        # store the provided API key in the credential store, if not asked to delete it
        if 'delete_api_key' not in cfg:
            store_api_key('OpenAI API Key', api_key)
    else:
        # try to retrieve API key from the credential store
        api_key = retrieve_api_key('OpenAI API Key')

    # remove the API key from the credential store, if it's there
    if 'delete_api_key' in cfg:
        delete_api_key('OpenAI API Key')

    if api_key is None:
        print('No API Key found. Please provide an API Key once (`--api_key <my API key>`).')
        exit(1)

    return api_key


def main(cfg: Config):
    console = Console()

    # print help text if requested, or if no arguments are provided
    if 'help' in cfg or not cfg.parameters and not cfg.from_arguments:
        print_help()

    # reload previous conversations from file in user profile
    conversations_path = Path('~/gpt_conversations.txt').expanduser()
    if conversations_path.exists():
        with open(conversations_path, 'r') as f:
            conversations = json.loads(f.read())
    else:
        conversations = {}

    # if the --list switch is provided, list stored conversations and terminate
    if 'list' in cfg:
        for tag, conversation in conversations.items():
            # assumes all keys are conversation tags, except 'last'
            if tag == 'last':
                continue
            # display the first user prompt (skipping the initial)
            # noinspection PyTypeChecker
            console.print(Markdown(f'**{tag}**> {conversation[1]["content"]}'))
        if 'last' in conversations:
            console.print(Markdown(f'Last conversation: **{conversations["last"]}**'))
        else:
            console.print('No conversation marked as last.')
        exit(0)

    # if the --replay switch is provided, replay the conversation and terminate
    # replay the last with no argument, or the one with the given tag
    if 'replay' in cfg:
        if cfg['replay'] is True:
            if 'last' in conversations:
                cfg['replay'] = conversations['last']
            else:
                print('No recent conversation to replay.')
                exit(1)
        if cfg['replay'] not in conversations:
            print(f'No conversation "{cfg["replay"]}" found.')
            exit(1)
        else:
            conversation = conversations[cfg['replay']]
            interactions = iter(conversation)
            next(interactions)  # skip the standard instruction
            prompt = cfg['replay']
            for interaction in interactions:
                if interaction['role'] == 'user':
                    console.print(Markdown(f'**{prompt}**> "{interaction["content"]}"'))
                else:
                    console.print(Markdown(interaction["content"]))
                prompt = 'prompt'
            exit(0)

    # select a specific conversation to continue base on the --continue switch
    # or start a new one with the INITIAL_PROMPT
    if 'continue' in cfg:
        if cfg['continue'] is True:
            if 'last' in conversations:
                cfg['continue'] = conversations['last']
            else:
                print('No recent conversation to continue (omit `--continue` to start a new conversation).')
                exit(1)
        if cfg['continue'] not in conversations:
            print(f'No conversation "{cfg["continue"]}" found.')
            exit(1)
        else:
            conversation = conversations[cfg['continue']]
    else:
        conversation = [
            {
                "role": "user",
                "content": ' '.join(INITIAL_PROMPT.split())
            }
        ]

    # obtain the query from parameters passed before switches, or as arguments to --query
    if cfg.parameters and 'query' in cfg:
        print('Both switch-less query and `--query` are provided. Please provide only one.')
        exit(1)
    if cfg.parameters:
        query = ' '.join(cfg.parameters)
    else:
        if 'query' in cfg:
            query = cfg.query
        else:
            query = None

    # set the model to use from --model, defaulting to gpt-4o
    if 'model' in cfg:
        models = ['gpt-3.5', 'gpt-4', 'gpt-4o']
        model = cfg['model']
        if model not in models:
            print(f'Invalid model "{model}". Options are:', ', '.join(models))
            exit(1)
    else:
        model = 'gpt-4o'

    # define a file_query, if a filename was passed
    # the file query will be passed as a second user query after the main query, if any
    if 'file' in cfg:
        if isinstance(cfg['file'], str):
            cfg['file'] = [cfg['file']]
        # keep all filenames except stdin '-'
        cfg['file'] = [fn for fn in cfg['file'] if fn != '-']
        # if there is data, add stdin to the list
        if not sys.stdin.isatty():
            cfg['file'] = cfg['file'] + ['-']
    else:
        # if there is data set 'file' to stdin
        if not sys.stdin.isatty():
            cfg['file'] = ['-']

    # read all files, including stdin if provided
    file_query = ''
    if cfg['file']:
        for line in fileinput.input(files=cfg['file'], encoding="utf-8"):
            file_query += line
    if not file_query:
        file_query = None

    # retrieve the API key (or store if provided, or delete/forget if specified)
    api_key = manage_api_key(cfg)

    # if there is an actual query to pose to GPT, make the interaction
    if query is not None or file_query is not None:
        conversation.append({
            "role": "user",
            "content": query,
        })

        if file_query is not None:
            conversation.append({
                "role": "user",
                "content": file_query,
            })

        client = OpenAI(
            api_key=api_key,
        )

        chat_completion = client.chat.completions.create(
            messages=conversation,
            model=model,
        )

        response = chat_completion.choices[0].message.content

        console = Console()
        console.print(Markdown(response))

        conversation.append({
            "role": "assistant",
            "content": response,
        })

    # if --reset is specified, convert it to a list of tags to delete
    if 'reset' in cfg:
        if 'delete' in cfg:
            print('Both `--reset` and `--delete` are provided. Delete will be ignored.')
            cfg.pop('delete')
        if cfg['reset'] is True:
            conversations = {}
        elif isinstance(cfg['reset'], str):
            cfg['reset'] = [cfg['reset']]
        if isinstance(cfg['reset'], list):
            delete = []
            # support retaining 'last'
            if 'last' in cfg['reset']:
                cfg['reset'].remove('last')
                if 'last' in conversations and conversations['last'] in conversations:
                    cfg['reset'].append(conversations['last'])
            # create the inverse list in delete
            for tag in conversations:
                if tag not in cfg['reset']:
                    delete.append(tag)
            if delete:
                cfg['delete'] = delete

    # if --delete is specified, or set by --reset, delete those conversation(s)
    if 'delete' in cfg:
        if cfg['delete'] is True:
            print('Specify conversation to delete.')
        elif isinstance(cfg['delete'], str) or isinstance(cfg['delete'], list):
            # turn single tag into a list
            if isinstance(cfg['delete'], str):
                cfg['delete'] = [cfg['delete']]
            # support deleting 'last'
            if 'last' in cfg['delete']:
                cfg['delete'].remove('last')
                if 'last' in conversations and conversations['last'] in conversations:
                    cfg['delete'].append(conversations['last'])
            for tag in cfg['delete']:
                if tag in conversations:
                    conversations.pop(tag)
                else:
                    print(f'No conversation "{tag}" to delete.')
            if 'last' in conversations and conversations['last'] not in conversations:
                conversations.pop('last')

    # save the current conversation if any
    if query is not None:
        if 'continue' in cfg:
            last = cfg['continue']
        else:
            n = 1
            while str(n) in conversations:
                n += 1
            last = str(n)
        conversations[last] = conversation
        conversations['last'] = last

    with open(conversations_path, 'w') as f:
        f.write(json.dumps(conversations))


if __name__ == '__main__':
    # load configuration passed with -cfg / --config or from the command line
    # aliases defined here will be resolved before the main function is called
    main(Config.startup(aliases={
        'c': 'continue', 'cont': 'continue', 'k': 'api_key', 'key': 'api_key', 'd': 'delete',
        'del': 'delete', 'q': 'query', 'r': 'replay', 'm': 'model', 'l': 'list', 'x': 'reset',
        'h': 'help', 'f': 'file', 'dak': 'delete_api_key'
    }))
