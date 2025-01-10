import logging
import os
import re
import shutil
import subprocess
from datetime import time
from functools import lru_cache
import dash_bootstrap_components as dbc
import paramiko
from dash.exceptions import PreventUpdate
from flask_login import current_user
from dash import no_update, html
import pandas as pd
from config_loader import load_config
import smtplib
from email.message import EmailMessage
import requests

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
user = 'pipeline_web'
set_user_command = f'WORK_LMT_USER={user}'
dispatch_command = 'lmtoy_dispatch/lmtoy_dispatch_session.sh'
mk_runs_command = 'lmtoy_dispatch/lmtoy_mk_runs.sh'


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

# find files with prefix and has content and not ending with x
def find_files(folder_path, prefix):
    if not folder_path:
        raise ValueError("The provided folder path is empty or None.")
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"No such directory: {folder_path}")

    filtered_files = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # Check if it is a file, starts with the prefix, has content, and does not end with excluded patterns
        if (
                os.path.isfile(file_path) and
                filename.startswith(prefix) and
                not (filename.endswith('.jobid') or
                     filename.endswith('x')) and
                os.path.getsize(file_path) > 0  # Check if file has content
        ):
            filtered_files.append(filename)

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
                        if key == 'obsnums':
                            key = 'obsnum'
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
        # Extract filename from the given path
    dir_path = os.path.dirname(runfile_path)
    filename = os.path.basename(runfile_path)

    # Ensure the file is saved with the correct name
    final_path = os.path.join(dir_path, filename)
    with open(final_path, 'w') as f:
        f.write('\n'.join(lines))

# clone a session: input is the path of the session to be cloned and the path of the new session
def save_session(pid_path, name, active_session):
    print(f"pid_path: {pid_path}, name: {name}, active_session: {active_session}")
    try:
        # Create base session directory
        session_dir = os.path.join(pid_path, f'Session-{name}')
        if os.path.exists(session_dir):
            return f'session-{name} already exists', no_update

        # Create required subdirectories
        os.makedirs(session_dir)
        os.makedirs(os.path.join(session_dir, current_user.username))
        os.makedirs(os.path.join(session_dir, 'sbatch'))
        os.makedirs(os.path.join(session_dir, 'tmp'))
        os.makedirs(os.path.join(session_dir, 'lmtoy_run'))
        os.makedirs(os.path.join(session_dir, 'lmtoy_run', f'lmtoy_{current_user.username}'))

        # Clone lmtoy_run repository to the session_dir and move the files from lmtoy_run to session_dir
        temp_clone_dir = os.path.join(session_dir, 'temp_lmtoy_run')
        try:
            subprocess.run(['git', 'clone', 'https://github.com/lmtoy/lmtoy_run.git',
                            temp_clone_dir],
                           check=True,
                           capture_output=True)
            # Move the files from temp_lmtoy_run to session_dir/lmtoy_run
            for file in os.listdir(temp_clone_dir):
                src = os.path.join(temp_clone_dir, file)
                dst = os.path.join(session_dir, file)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                elif os.path.isdir(src) and file != '.git':
                    shutil.copytree(src, dst, dirs_exist_ok=True)
            shutil.rmtree(temp_clone_dir)

        except subprocess.CalledProcessError as e:
            if os.path.exists(temp_clone_dir):
                shutil.rmtree(temp_clone_dir)
            raise Exception(f"Failed to clone lmtoy_run repository: {e.stderr.decode()}")

        # Copy runfiles from old session path to new session path
        new_session_path = os.path.join(session_dir, 'lmtoy_run', f'lmtoy_{current_user.username}')

        if active_session != init_session:
            old_session_path = os.path.join(pid_path, active_session, 'lmtoy_run',
                                            f'lmtoy_{current_user.username}')
        else:
            old_session_path = default_session_prefix + current_user.username

        if os.path.exists(old_session_path):
            runfiles = find_runfiles(old_session_path, f'{current_user.username}.')
            for runfile in runfiles:
                shutil.copy(os.path.join(old_session_path, runfile), new_session_path)
        return f"Successfully created session at {session_dir}", False

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

# Helper function to execute SSH commands
def execute_ssh_command(command, set_user_command=None):
    # Set up SSH client
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to the SSH server
        client.connect(hostname=hostname, username=username)
        print("SSH connection established.")

        # Combine environment variable setup with the actual command
        if set_user_command:
            full_command = f"{set_user_command} {command}"
        else:
            full_command = command
        print(f"Executing command: {full_command}")

        # Execute the command
        stdin, stdout, stderr = client.exec_command(full_command)

        # Get any output or error messages
        output = stdout.read().decode()
        error = stderr.read().decode()
        # print(f"Output: {output}")
        # print(f"Error: {error}")
        return {'returncode': 0 if not error else 1, 'stdout': output, 'stderr': error}

    except paramiko.AuthenticationException:
        return {"returncode": 1, "stdout": "", "stderr": "Authentication failed. Check credentials."}
    except paramiko.SSHException as sshException:
        return {"returncode": 1, "stdout": "", "stderr": f"SSH connection failed: {sshException}"}
    except Exception as e:
        return {"returncode": 1, "stdout": "", "stderr": str(e)}
    finally:
        client.close()
        print("SSH connection closed.")
def execute_remote_submit(pid, runfile,session):
    # Create the full command to run remotely in the background with nohup
    full_command = f"{dispatch_command} {pid} {runfile} {session}"
    result = execute_ssh_command(full_command, set_user_command=set_user_command)
    if result["returncode"] == 0:
        return "Job submitted successfully."
    else:
        return f"Error in submission: {result['stderr']}"

def get_source(pid):
    full_command = f"{mk_runs_command} {pid}"
    result = execute_ssh_command(full_command, set_user_command=set_user_command)
    print(f"Result: {result}")
    # checks if the command ran successfully(return code 0)
    if result["returncode"] == 0:
        output = result["stdout"]
        pattern = r"([\w\-]+)\[\d+/\d+\] : ([\d,]+)"
        matches = re.findall(pattern, output)
        if not matches:
            print("No sources found in output")
            return {}

        sources = {name: [int(x) for x in obsnums.split(',')] for name, obsnums in matches}
        return sources
    else:
        print(f"Error in execution: {result['stderr']}")
        return {}

def check_slurm_job_status(check_option,username):
    if check_option == 'Account':
        command = f"squeue -u {username} -o '%i|%j|%t|%M|%D|%R'"
    elif check_option == 'Job ID':
        command = f"squeue -j {username} -o '%i|%j|%t|%M|%D|%R'"
    elif check_option == 'Job Name':
        command = f"squeue -n {username} -o '%i|%j|%t|%M|%D|%R'"
    result = execute_ssh_command(command)

    if result["returncode"] == 0:
        output = result["stdout"]
        if not output.strip():
            return "No jobs found", False

        lines = output.splitlines()
        if len(lines) <= 1:  # If there are no job lines after the header
            return "No jobs found", False

        headers = ["Job ID", "Name", "State", "Time Used", "Nodes", "Reason"]
        data = lines[1:]  # Skip the header row

        try:
            # Parse all job details into a list of dictionaries
            jobs = [
                {header: value for header, value in zip(headers, line.split("|"))}
                for line in data
            ]
            return jobs, True
        except IndexError:
            return "Error: Malformed data received from SLURM", False
    else:
        return f"Error: {result['stderr']}", False

# TODO get the obsnums from the runfile if the column name is obsnum get the first obsnum and add_1 if column name is obsnums
def check_runfile_job_status(runfile_path):
    import os

    # Validate the runfile path
    if not runfile_path or not os.path.exists(runfile_path):
        return "Invalid runfile path.", False

    try:
        # Parse the runfile
        df, _ = df_runfile(runfile_path)
        if 'obsnum' not in df.columns:
            return "No 'obsnum' column found in runfile.", False

        # Collect all job names from 'obsnum' column
        obsnums = []
        for obsnum in df['obsnum']:
            try:
                obsnums.extend([int(num) for num in obsnum.split(',')])
            except ValueError:
                print(f"Error converting obsnum to integer: {obsnum}")

        # Deduplicate job names
        obsnums = list(set(obsnums))

        # Check the status of all jobs in one `squeue` call
        job_names_str = ",".join(map(str, obsnums))
        command = f"squeue --name={job_names_str} -o '%A|%j|%T'"
        result = execute_ssh_command(command)

        if result["returncode"] != 0:
            return f"Error checking job status: {result['stderr']}", False

        # Parse the output
        output = result["stdout"].strip()
        lines = output.splitlines()[1:]  # Skip header
        job_statuses = []

        for line in lines:
            try:
                job_id, job_name, status = line.split("|")
                job_statuses.append({"Job ID": job_id, "Name": job_name, "State": status})
            except ValueError:
                print(f"Error parsing line: {line}")

        if not job_statuses:
            return "No running jobs found.", False

        return job_statuses, True

    except Exception as e:
        print(f"Unexpected error: {e}")
        return "An unexpected error occurred.", False


# def check_runfile_job_status(runfile_path):
#     print(f'runfile_path: {runfile_path}')
#     # Append .jobid to the file name
#     jobid_file = f"{runfile_path}.jobid"
#
#     if not os.path.exists(jobid_file):
#         return "Runfile does not exist or .jobid file is missing", False
#
#     # Read job IDs from the file
#     with open(jobid_file, 'r') as file:
#         job_ids = file.read().splitlines()
#
#     if not job_ids:
#         return "No job IDs found", False
#
#     # Check the status of each job ID
#     job_statuses = []
#     for job_id in job_ids:
#         command = f"squeue -j {job_id} -o '%i|%t'"
#         result = execute_ssh_command(command)
#
#         if result["returncode"] == 0:
#             output = result["stdout"].strip()
#             lines = output.splitlines()[1:]
#             for line in lines:
#                 job_id, status = line.split("|")
#                 if status == "R":  # Only include running jobs
#                     job_statuses.append({"Job ID": job_id, "State": status})
#         elif "Invalid job id specified" in result["stderr"]:
#             # Skip invalid job IDs
#             continue
#         else:
#             return f"Error checking job status: {result['stderr']}", False
#
#     if not job_statuses:
#         return "No running jobs found.", False
#
#     return job_statuses, True


def cancel_slurm_job(job_id):
    command = f"scancel {job_id}"
    result = execute_ssh_command(command)
    if result["returncode"] == 0:
        return {"Job ID": "", "Name":job_id, "State": "CANCELLED", "Time Used": "", "Nodes": "", "Reason": ""}, True
    else:
        return f"Error: {result['stderr']}", False

def are_jobs_finished(job_ids):
    command = f"squeue -j {','.join(job_ids)} -o '%i|%t'"
    result = execute_ssh_command(command)
    if result["returncode"] == 0:
        output = result["stdout"].strip()
        lines = output.splitlines()[1:]  # Skip the header line
        for line in lines:
            job_id, status = line.split("|")
            if status not in ["CD", "CG"]:  # CD: Completed, CG: Completing
                return False
        return True
    else:
        print(f"Error checking job status: {result['stderr']}")
        return False

def monitor_slurm_jobs(job_ids, check_interval=30):
    while True:
        if are_jobs_finished(job_ids):
            return True
        time.sleep(check_interval)

def send_email(subject, body, to):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['to'] = to

    user = 'xiahuang@umass.edu'
    password = 'youn pktv vqyy mqfe'
    msg['from'] = user

    # Use SMTP_SSL instead of SMTP
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(user, password)
    server.send_message(msg)
    server.quit()
def notify_user(job_ids, recipient_email, method="email",):
    if method == "email":
        send_email("Jobs Completed", f"All jobs {job_ids} have completed.",recipient_email)
    elif method == "app":
        return f"Notification: All jobs {job_ids} have completed."
    else:
        print(f"All jobs {job_ids} have completed.")
# send email to user if the job is finished
def send_email_alert(job_ids, recipient_email):
    notify_user(job_ids, recipient_email, method="email")
    return f"Email sent to {recipient_email}."

def is_valid_email(email):
    """Validate the email format using a regex."""
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(email_regex, email))

def get_source_and_obsnum_options(n, selected_rows, data):
    """Helper function to handle both source and obsnum dropdown options."""
    # Add logic to inspect how rsr and seq data are processed
    # Example:
    if 'RSR' in selected_rows[0]['_io']:
        print("Processing rsr data")
    if 'SEQ' in selected_rows[0]['_io']:
        print("Processing seq data")
    if not n:
        raise PreventUpdate

    # Populate source options and value
    source_options = [{'label': str(s), 'value': str(s)} for s in data.get('source', {}).keys()]
    selected_row_data = selected_rows[0] if selected_rows else {}
    source_value = selected_row_data.get('_s', None)

    return source_options, source_value

def get_obsnum_options(source, selected_rows, data):
    """Helper function to handle obsnum dropdown options."""
    if not source:
        raise PreventUpdate
    # get the obsnum options from data_store based on the source value

    obsnum_options = data.get('source', {}).get(source)
    obsnum_dropdown_options = [{'label': str(o), 'value': str(o)} for o in obsnum_options]

    # Extract and process obsnum values from selected rows
    selected_obsnums = []
    if selected_rows:
        for row in selected_rows:
            obsnum = row.get('obsnum')
            if obsnum:
                # Handle cases where obsnum is a comma-separated string
                if isinstance(obsnum, str):
                    selected_obsnums.extend([v.strip() for v in obsnum.split(',') if v.strip()])
                elif isinstance(obsnum, list):
                    selected_obsnums.extend([str(v).strip() for v in obsnum])

    # Deduplicate and sort selected obsnums
    selected_obsnums = sorted(set(selected_obsnums))

    # Disable dropdowns if at least one row is selected
    disable_dropdowns = len(selected_rows) > 1
    return obsnum_dropdown_options, selected_obsnums, disable_dropdowns, disable_dropdowns

def process_job_submission(pid,runfile, session,email):
    """
    Handles the job submission process asynchronously.
    """
    # todo if session is 0
    # if session==init_session:

    try:
        # Simulate remote submission process (replace with actual logic)
        print(f"Submitting job for '{runfile}'...")
        execute_remote_submit(pid, runfile ,session)

        # Optional: Send confirmation email asynchronously
        if email:
            confirmation_message = f"Job for runfile '{runfile}' has been submitted successfully."
            send_email('Job Submission Confirmation', confirmation_message, email)
    except Exception as e:
        # Log the exception for debugging (could also send an email or update a status)
        print(f"Error during job submission for '{runfile}': {e}")

def generate_result_url(pid, session_name):
    # return http://taps.lmtgtm.org/lmthelpdesk/pipeline_web/2023-S1-US-17/Session-1/2023-S1-US-17/README.html
    return f"http://taps.lmtgtm.org/lmthelpdesk/pipeline_web/{pid}/{session_name}/{pid}/README.html"

def get_parameter_info(url):
    if not url:
        return "No URL provided", False

    # step1: Read the parameters.txt from GitHub
    response = requests.get(url)
    if response.status_code != 200:
        return f"Error: {response.status_code}", False
    parameters_content = response.text

    # step2: Parse the parameters.txt content
    parameters = {}
    lines = parameters_content.split("\n")
    current_section = None

    for line in lines:
        if line.startswith("="):
            # New section
            current_section = line.strip().replace("=", "")
            parameters[current_section] = {}
        elif current_section and ":" in line:
            # Parameter line within a section
            param_name, param_desc = line.split(":", 1)
            parameters[current_section][param_name.strip()] = param_desc.strip()

    return parameters

# parameters = get_parameter_info(url)
# rsr_parameters = parameters['RSR/BS']
# sequoia_parameters = parameters['SEQ/MAP']
