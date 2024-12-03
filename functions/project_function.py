import logging
import os
import re
import shutil
from functools import lru_cache
import dash_bootstrap_components as dbc
import paramiko
from flask_login import current_user
from dash import no_update, html
import pandas as pd
from config_loader import load_config


try :
    config = load_config()
except Exception as e:
    print(f"Error loading configuration: {e}")

default_work_lmt = config['path']['work_lmt']
# default_data_lmt = config['path']['data_lmt']
default_session_prefix = os.path.join(default_work_lmt, 'lmtoy_run/lmtoy_')
init_session = config['session']['init_session']

hostname = config['ssh']['hostname']
username = config['ssh']['username']

# Define the commands
set_user_command = 'export WORK_LMT_USER=pipeline_web'
dispatch_command = './bin/lmtoy_dispatch.sh'
mk_runs_command = './bin/lmtoy_mk_runs.sh'


# Function to get pid options from the given path
@lru_cache(maxsize=None)
def get_pid_option(path):
    result = []
    for folder_name in os.listdir(path):
        full_path = os.path.join(path, folder_name)
        if os.path.isdir(full_path) and folder_name.startswith('lmtoy_'):
            label_value = os.path.basename(folder_name.split('_')[1])
            result.append({'label': label_value, 'value': label_value})

    return result

def get_work_lmt_path(config):
    work_lmt = os.environ.get('WORK_LMT')

    if work_lmt:
        print(f'login: WORK_LMT = {work_lmt}')
    elif 'path' in config and 'work_lmt' in config['path']:
        work_lmt = config['path']['work_lmt']
        print('Environment variable WORK_LMT not exists, get it from config.txt')
    else:
        print('Could not find the value of work_lmt')
        return None
    return work_lmt


def check_user_exists():
    return current_user and current_user.is_authenticated

# check if path exists
def ensure_path_exists(path):
    if not path or not os.path.exists(path):
        print(f"Path {path} does not exist")
        return False
    print(f"Path {path} exists")
    return True

# find files with prefix
def find_files(folder_path, prefix):
    if not folder_path:
        raise ValueError("The provided folder path is empty or None.")
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"No such directory: {folder_path}")

    files = [filename for filename in os.listdir(folder_path) if
             os.path.isfile(os.path.join(folder_path, filename)) and filename.startswith(prefix)]
    # get only the files without the .jobid extension
    filtered_files = [f for f in files if not f.endswith('.jobid')]

    return sorted(filtered_files)

def find_runfiles(folder_path, prefix):
    matching_files = find_files(folder_path, prefix)
    if not matching_files:
        print("No matching files found. Running 'mk_runs.py'")
        matching_files = find_files(folder_path, prefix)
        if matching_files:
            print(f"Matching files: {matching_files}")
    return matching_files

# get the session names and their paths in a folder
def get_session_info(default_session, pid_path):
    default_session_path = os.path.join(os.path.dirname(pid_path), 'lmtoy_run', f'lmtoy_{current_user.username}')
    session_info = [{'name': default_session, 'path': default_session_path}]

    if ensure_path_exists(pid_path):
        new_sessions = [
            {'name': file, 'path': os.path.join(pid_path, file, 'lmtoy_run', f'lmtoy_{current_user.username}')}
            for file in sorted(os.listdir(pid_path))
            if file.startswith('Session')
        ]

        session_info.extend(new_sessions)
    return session_info

def get_runfile_option(session_path):
    matching_files = find_runfiles(session_path, f'{current_user.username}.')
    return [{'label': label, 'value': f'{session_path}/{label}'} for label in matching_files]


def get_session_list(default_session, pid_path):
    session_info = get_session_info(default_session, pid_path)
    return [
        dbc.AccordionItem(
            [dbc.RadioItems(id={'type': 'runfile-radio', 'index': session['name']},
                            options=get_runfile_option(session['path']),
                            # className='my-radio-items',
                            inline=True
                            )],
            title=session['name'], className='mb-2', item_id=session['name'],
        )
        for session in session_info
    ]

def del_runfile(runfile):
    # Check if the file exists
    if os.path.exists(runfile):
        # If it exists, delete the folder and all its contents
        print(f"Deleting the file {runfile}")
        os.remove(runfile)
        return False, f"The file {runfile} has been deleted successfully."
    else:
        print(f"The file {runfile} does not exist.")


def exclude_beams(pix_list):
    if pix_list:
        beams = pix_list.split(',')
        all_strings = [str(i) for i in range(16)]
        exclude_beams = [s for s in all_strings if s not in beams]
        return ','.join(exclude_beams)
    else:
        return pix_list

def create_modal(header_label, body_elements, footer_elements, modal_id):
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.Label(header_label, className='custom-bold')),
            dbc.ModalBody(body_elements),
            dbc.ModalFooter(footer_elements)
        ], id=modal_id, size='lg', centered=True, backdrop='static', scrollable=True
    )

def get_runfile_title(runfile_path, init_session):
    parts = runfile_path.split('/')
    session_string = next((part for part in parts if 'Session' in part), init_session).upper()
    runfile_title = os.path.basename(runfile_path)
    return f'{session_string}: {runfile_title}'

def make_tooltip(content, target):
    return html.Div(dbc.Tooltip(content, target=target, className='large-tooltip', placement='bottom'))

def df_runfile(filename):
    data = []
    content = ''

    if not os.path.exists(filename):
        return pd.DataFrame(), ''

    try:
        with open(filename, 'r') as file:
            content = file.read()
            file.seek(0)
            for line in file:
                commands = line.strip().split()
                row = {}
                for command in commands:
                    if isinstance(command, str) and "=" in command:
                        key, value = command.split('=', 1)
                        row[key] = value
                if row:
                    data.append(row)
        if not data:
            return pd.DataFrame(), content

        df = pd.DataFrame(data)
        df.reset_index(inplace=True)
        return df, content
    except Exception as e:
        return pd.DataFrame(), content
    else:
        return pd.DataFrame(), ''

# save revised data to a runfile
def save_runfile(df, runfile_path):
    print(f"runfile_path: {runfile_path}")
    separator = '='
    lines = []

    # Iterate over DataFrame rows using iterrows, which doesn't include the index
    for _, row in df.iterrows():
        line = 'SLpipeline.sh'
        for column, value in row.items():
            if value is not None and str(value).strip() != '' and column != 'index':
                if isinstance(value, list):
                    value = ','.join(map(str, value))
                if column == 'obsnum(s)':
                    if ',' in value:
                        column = 'obsnums'
                    else:
                        column = 'obsnum'
                if column == 'exclude_beams':
                    column = 'pix_list'
                    value = exclude_beams(value)
                if column == 'px_list':
                    print(f"px_list: {value}")
                line += f" {column}{separator}{value}"
        lines.append(line)

    with open(runfile_path, 'w') as f:
        f.write('\n'.join(lines))


def save_session(pid_path, name, active_session):
    try:
        default_session_path = default_session_prefix + current_user.username
        new_session_path = os.path.join(pid_path, f'Session-{name}', 'lmtoy_run', f'lmtoy_{current_user.username}')
        if os.path.exists(new_session_path):
            return f'session-{name} already exists', no_update

        old_session_path = default_session_path if active_session == init_session \
            else os.path.join(pid_path, active_session, 'lmtoy_run', f'lmtoy_{current_user.username}')

        shutil.copytree(old_session_path, new_session_path)
        logging.info(f"Successfully copied session to {new_session_path}")
        return f"Successfully copied to {new_session_path}", False
    except Exception as e:
        logging.error(f"Error in save_session: {str(e)}")
        return f"Failed to save session: {str(e)}", no_update

def delete_session(pid_path, active_session):
    try:
        session_path = os.path.join(pid_path, active_session)
        if os.path.exists(session_path):
            shutil.rmtree(session_path)
            logging.info(f"Successfully deleted session at {session_path}")
            return f"Successfully deleted {session_path}"
        else:
            logging.warning(f"The folder {session_path} does not exist.")
            return f"The folder {session_path} does not exist."
    except Exception as e:
        logging.error(f"Error in delete_session: {str(e)}")
        return f"Failed to delete session: {str(e)}"

def get_runfile_info(active_session, pid_path):
    if not active_session:
        return [], []

    try:
        default_session_path = default_session_prefix + current_user.username
        session_path = default_session_path if active_session == init_session \
            else os.path.join(pid_path, active_session, 'lmtoy_run', f'lmtoy_{current_user.username}')

        runfile_options = get_runfile_option(session_path)
        default_runfiles = ['run1a', 'run1b', 'run2a', 'run2b']

        runfile_value = [
            option['value'] for option in runfile_options
            if option['label'].split('.')[-1] in default_runfiles
        ]

        if not runfile_value and runfile_options:
            runfile_value = [runfile_options[0]['value']]

        return runfile_options, runfile_value
    except Exception as e:
        logging.error(f"Error in get_runfile_info: {str(e)}")
        return [], []


def check_job_status(session_path):
    if not os.path.exists(session_path):
        return 'not_submitted', False, {'display':'None'}, ''

    files_in_session = os.listdir(session_path)
    if not files_in_session or (len(files_in_session) == 1 and files_in_session[0] == 'lmtoy_run'):
        return 'not_submitted', False, {'display':'None'}, ''

    if 'README.html' in files_in_session:
        return 'finished', False, {'display':'block'}, f'/view_result/{os.path.basename(os.path.dirname(session_path))}/{os.path.basename(session_path)}'

    return 'running', True, {'display':'None'}, ''

def get_session_path(username, active_session):
    if active_session == init_session:
        return default_session_prefix + username
    return os.path.join(default_work_lmt, username, active_session)

def execute_remote_submit(pid, runfile):
    # Set up SSH client
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Create the full command to run remotely in the background with nohup
    full_command = f"{set_user_command} && nohup {dispatch_command} {pid} {runfile}"
    print(f"Full Command: {full_command}")
    try:
        # Connect to the SSH server
        client.connect(hostname=hostname, username=username)
        print("SSH connection established.")

        # Execute the command in the background
        stdin, stdout, stderr = client.exec_command(full_command)

        # Get any initial output or error messages
        output = stdout.read().decode()
        error = stderr.read().decode()

        # Print output and error for debugging
        print("Initial Output:", output)
        print("Initial Error:", error)

        # Inform that the command was sent successfully
        print("Command sent to run in the background.")
        return "Job started in background"
    except paramiko.AuthenticationException:
        print("Authentication failed. Please check your credentials.")
    except paramiko.SSHException as sshException:
        print(f"Unable to establish SSH connection: {sshException}")
    except Exception as e:
        print(f"Exception occurred: {e}")
    finally:
        # Close the connection
        print("Closing SSH connection.")
        client.close()

def execute_mk_runs(pid):
    # Set up SSH client
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Create the full command to run remotely in the background with nohup
    full_command = f"{set_user_command} && nohup {mk_runs_command} {pid}"
    print(f"Full Command: {full_command}")
    try:
        # Connect to the SSH server
        client.connect(hostname=hostname, username=username)
        print("SSH connection established.")

        # Execute the command in the background
        stdin, stdout, stderr = client.exec_command(full_command)

        # Get any initial output or error messages
        output = stdout.read().decode()
        error = stderr.read().decode()

        # Print output and error for debugging
        print("Initial Output:", output)
        print("Initial Error:", error)

        # Inform that the command was sent successfully
        print("Command sent to run in the background.")
        return {"returncode": 0, "stdout": output, "stderr": error}
    except Exception as e:
        print(f"Exception occurred: {e}")
        return {"returncode": 1, "stdout": "", "stderr": str(e)}
    finally:
        client.close()

def get_source(default_work_lmt, pid):
    pid_path = os.path.join(default_work_lmt, 'lmtoy_run', f'lmtoy_{pid}')
    mk_runs_file = os.path.join(pid_path, 'mk_runs.py')
    result = execute_mk_runs(pid)

    # checks if the command ran successfully(return code 0)
    if result["returncode"] == 0:
        output = result["stdout"]
        pattern = r"(\w+)\[\d+/\d+\] : ([\d,]+)"
        matches = re.findall(pattern, output)
        if not matches:
            print("No sources found in output")
            return {}

        sources = {name: [int(x) for x in obsnums.split(',')] for name, obsnums in matches}
        return sources
    else:
        print(f"Error in execution: {result['stderr']}")
        return {}

def get_email(pid):
    email = config[pid]['email']
    return email
def get_instrument(pid):
    instrument = config[pid]['instrument']
    return instrument
