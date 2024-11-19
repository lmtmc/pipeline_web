import logging
import os
import shutil
import threading
from functools import lru_cache
from pathlib import Path
import dash_bootstrap_components as dbc
import paramiko
from flask_login import current_user
from dash import no_update, html
import subprocess
import ast
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


def make_tooltip(content, target):
    return html.Div(dbc.Tooltip(content, target=target, className='large-tooltip', placement='bottom'))


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

def clone_runfile(runfile, name):
    if not name:
        return False, "Please input a name!"
    new_name_path = os.path.join(Path(runfile).parent, name)
    print(f'new_name_path: {new_name_path}')
    # Check if the session directory already exists
    if os.path.exists(new_name_path):
        # If the directory not exist, create it
        return True, f'Runfile {name} already exists', True
    shutil.copy(runfile, new_name_path)
    return False, f"Runfile {name} created successfully!", False


def del_session(folder_path):
    # Check if the folder exists
    if os.path.exists(folder_path):
        # If it exists, delete the folder and all its contents
        shutil.rmtree(folder_path)
        return False, f"The folder {folder_path} has been deleted successfully."
    else:
        print(f"The folder {folder_path} does not exist.")


# helper function for session display
def handle_new_session():
    return True, ''

def handle_delete_session(pid_path, active_session):
    session_path = os.path.join(pid_path, active_session)
    del_session(session_path)
    return "Session deleted successfully!"


def handle_delete_runfile(stored_data):
    del_runfile(stored_data['runfile'])
    return "Runfile deleted successfully"



def del_runfile(runfile):
    # Check if the file exists
    if os.path.exists(runfile):
        # If it exists, delete the folder and all its contents
        print(f"Deleting the file {runfile}")
        os.remove(runfile)
        return False, f"The file {runfile} has been deleted successfully."
    else:
        print(f"The file {runfile} does not exist.")


def add_runfile(runfile_path, name):
    new_runfile_path = os.path.join(runfile_path, name)
    # Attempt to create the new runfile
    try:
        open(new_runfile_path, 'x').close()
        return True, f"Runfile {name} has been created successfully."
    except FileExistsError:
        # If the runfile already exists, inform the user
        return False, f'Runfile {name} already exists at {runfile_path}'


def update_df_with_state_values(df, selected_rows, state_values, table_column):
    # Log or print the DataFrame and selected rows for debugging
    print("Before update:")
    print(df)
    print("Selected rows:", selected_rows)

    for i, column in enumerate(table_column[2:]):
        if state_values[i + 2] is not None and state_values[i + 2] != []:
            value = state_values[i + 2]
            if i == 1:  # Special handling for beam values
                filtered_beam = filter(bool, value)
                sorted_beam = sorted(filtered_beam, key=int)
                value = ",".join(sorted_beam)
            elif i == 2:
                value = str(value)

            # Ensure that the selected_rows exist in the DataFrame
            if all(row in df.index for row in selected_rows):
                df.loc[selected_rows, column] = value
            else:
                print(f"Selected rows not found in DataFrame: {selected_rows}")
    return df


def create_new_row(state_values, table_column):
    new_row = {key: None for key in table_column}
    for i, column in enumerate(table_column):
        if state_values[i] is not None:
            value = state_values[i]
            # Special handling for specific columns
            if i == 1:
                value = '.'.join(value)
            if i == 3:
                filtered_beam = filter(bool, value)
                sorted_beam = sorted(filtered_beam, key=int)
                value = ",".join(sorted_beam)
            elif i == 4:
                value = f'[{value}]'
            new_row[column] = value
    return new_row

# save revised data to a runfile
def save_runfile(df, runfile_path):
    separator = '='
    lines = []
    for row in df:
        line = 'SLpipeline.sh'
        for column, value in row.items():
            if value is not None and str(value).strip() != '':
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


def exclude_beams(pix_list):
    if pix_list:
        beams = pix_list.split(',')
        all_strings = [str(i) for i in range(16)]
        exclude_beams = [s for s in all_strings if s not in beams]
        return ','.join(exclude_beams)
    else:
        return pix_list


def table_layout(table_data):
    output = table_data
    output[1] = table_data[1].split(',')
    # 1,2,3 to ['1', '2', '3']
    if output[3]:
        output[3] = table_data[3].split(',')
    if output[4]:
        output[4] = ast.literal_eval(output[4])

    return output

def layout_table(layout_data):
    output = layout_data
    output[1] = ",".join(layout_data[1])

    if output[3]:
        filtered_beam = filter(bool, layout_data[3])
        sorted_beam = sorted(filtered_beam, key=int)

        output[3] = ",".join(sorted_beam)
    else:
        output[3] = ''
    if output[4]:
        output[4] = f'[{layout_data[4]}]'

    return output


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


def get_selected_runfile(ctx):
    """Determine the selected runfile based on trigger."""
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if 'runfile-radio' in trigger_id:
        return ctx.triggered[0]['value']
    # elif data_store.get('runfile') and os.path.exists(data_store['runfile']):
    #     return data_store['runfile']
    return None

# def run_job_background(pid, runfiles):
#     if isinstance(runfiles, str):
#         runfiles = [runfiles]
#     results = []
#
#     # Define a helper function to capture and append results
#     def job_runner(runfile):
#         result = submit_job(pid, runfile)
#         results.append(result)
#
#     # Start a new thread for each runfile
#     for runfile in runfiles:
#         job_thread = threading.Thread(target=job_runner, args=(runfile,), daemon=True)
#         job_thread.start()
#
#     return results
#
#
# def submit_job(pid, runfile):
#     try:
#         # Connect via SSH
#         ssh_process = subprocess.run(
#             ssh_command.split(),
#             input=f'{set_user_command}; {dispatch_command} {pid} {runfile}',
#             capture_output=True, text=True, shell=True
#         )
#
#         # Check for successful execution
#         if ssh_process.returncode == 0:
#             return ssh_process.stdout
#         else:
#             return ssh_process.stderr
#     except Exception as e:
#         return str(e)


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
        return df, content
    except Exception as e:
        return pd.DataFrame(), content
    else:
        return pd.DataFrame(), ''

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

def execute_remote_command(pid, runfile):
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