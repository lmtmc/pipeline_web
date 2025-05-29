import logging
import os
import re
import shutil
# from datetime import time
import time
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

init_session = config['session']['init_session']

hostname = config['ssh']['hostname']
username = config['ssh']['username']


# Define the commands
user = config['pipeline_user']['username']
set_user_command = f'WORK_LMT_USER={user}'
dispatch_command = 'lmtoy_dispatch/lmtoy_dispatch_session.sh'
mk_runs_command = 'lmtoy_dispatch/lmtoy_mk_runs.sh'
make_summary_command = 'lmtoy_dispatch/lmtoy_make_summary.sh'
#ssh lmthelpdesk_umass_edu@unity.rc.umass.edu WORK_LMT_USER=pipeline_web  lmtoy_dispatch/lmtoy_clone_session.sh  projectid session
clone_session_command = 'lmtoy_dispatch/lmtoy_clone_session.sh'


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
                     filename.endswith('x') or
                     filename.endswith('.sh')) and
                os.path.getsize(file_path) > 0  # Check if file has content
        ):
            filtered_files.append(filename)

    return sorted(filtered_files)

def find_runfiles(folder_path, pid):
    matching_files = find_files(folder_path, pid)
    if not matching_files:
        print("No matching files found. Running 'mk_runs.py'")

        matching_files = find_files(folder_path, pid)
        if matching_files:
            print(f"Matching files: {matching_files}")
    return matching_files

# get the session names and their paths in a folder
def get_session_info(default_session, pid_path):
    # Get the PID from the path
    pid = os.path.basename(pid_path)
    default_session_path = os.path.join(os.path.dirname(pid_path), 'lmtoy_run', f'lmtoy_{pid}')
    session_info = [{'name': default_session, 'path': default_session_path}]

    if ensure_path_exists(pid_path):
        new_sessions = [
            {'name': file, 'path': os.path.join(pid_path, file, 'lmtoy_run', f'lmtoy_{pid}')}
            for file in sorted(os.listdir(pid_path))
            if file.startswith('Session')
        ]

        session_info.extend(new_sessions)
    return session_info

def get_runfile_option(session_path,pid):
    matching_files = find_runfiles(session_path, f'{pid}.')
    if not matching_files:
        print(f"No matching files found. Running 'mk_runs.py'")
        full_command = f"{mk_runs_command} {pid}"
        result = execute_ssh_command(full_command, set_user_command=set_user_command)
        print(f"mk_runs.py result: {result}")
        if result["returncode"] == 0:
            matching_files = find_runfiles(session_path, f'{pid}.')
            if matching_files:
                print(f"Matching files: {matching_files}")
            else:
                print(f"No matching files found after running mk_runs.py")
    return [{'label': label, 'value': f'{session_path}/{label}'} for label in matching_files]

def get_session_list(default_session, pid_path,pid):
    session_info = get_session_info(default_session, pid_path)
    session_items = []

    for session in session_info:
        try:
            # Attempt to get runfile options for the session
            options = get_runfile_option(session['path'],pid)
            session_item = dbc.AccordionItem(
                [dbc.RadioItems(
                    id={'type': 'runfile-radio', 'index': session['name']},
                    options=options,
                    inline=True
                )],
                title=session['name'],
                className='mb-2',
                item_id=session['name'],
            )
            session_items.append(session_item)
        except Exception as e:
            # Log the error and skip this session
            logging.error(f"Error processing session {session['name']}: {str(e)}")
            continue  # Skip this session and continue with the next one

    return session_items
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
                if column == 'obsnum':
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
        f.write('\n')

def save_session(pid_path, name):
    pid = current_user.username
    new_session_name = f'Session-{name}'
    session_dir = os.path.join(pid_path, new_session_name)
    full_command = f"{clone_session_command} {pid} {new_session_name}"
    try:
        # Create base session directory
        if os.path.exists(session_dir):
            return f'session-{name} already exists', no_update
        result = execute_ssh_command(full_command, set_user_command=set_user_command)
        if result["returncode"] != 0 and 'Error' in result["stderr"]:
            return f"Failed to save session: {result['stderr']}", no_update

        elif result["returncode"]!=0:
            return f"Successfully created session at {session_dir}", False
    except Exception as e:
        logging.error(f"Error in save_session: {str(e)}")
        return f"Failed to save session {name}: {str(e)}", no_update

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

def is_job_submit_successful(result):
    # Check if the returncode is 0 (success) or there's specific output indicating success
    if result['returncode'] == 0:
        return True

    # Parse stderr to identify critical errors, ignoring non-critical ones
    stderr = result.get('stderr', '')
    # List of non-critical error messages to ignore
    non_critical_errors = [
        "ls: cannot access",
        "Note that 64 GB per node will require a node with more than 64 GB memory",
        "Check https://docs.unity.rc.umass.edu/nodes for an appropriate limit"
    ]

    # Filter out non-critical errors
    critical_errors = [
        line for line in stderr.splitlines()
        if not any(ignore in line for ignore in non_critical_errors)
    ]

    # If no critical errors are left, treat the job as successful
    return len(critical_errors) == 0

def execute_remote_submit(pid, runfile,session):
    # Create the full command to run remotely in the background with nohup
    full_command = f"{dispatch_command} {pid} {runfile} {session}"
    result = execute_ssh_command(full_command, set_user_command=set_user_command)
    # checks if the command ran successfully(return code 0)
    if result["returncode"] == 0:
        print(f"Successfully submitted job for {pid}")
    else:
        print(f"Error in execution: {result['stderr']}")

    success = is_job_submit_successful(result)
    return success

def get_source(pid):
    full_command = f"{mk_runs_command} {pid}"
    result = execute_ssh_command(full_command, set_user_command=set_user_command)
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


# get job id from runfile.jobid
def get_submitted_job_ids(runfile_path):
    job_ids = []
    jobid_file = f"{runfile_path}.jobid"
    if os.path.exists(jobid_file):
        print(f"Reading job IDs from {jobid_file}")
        with open(jobid_file, 'r') as f:
            job_ids = f.read().strip().splitlines()
    print(f"Job IDs: {job_ids}")
    return job_ids
def check_runfile_job_status(runfile_path):
    import os

    # Validate the runfile path
    if not runfile_path or not os.path.exists(runfile_path):
        return "Invalid runfile path.", False

    try:
        # retrieve job IDs
        job_ids = get_submitted_job_ids(runfile_path)
        if not job_ids:
            return "No job IDs found for the runfile.", False

        # Check the status of all jobs in one `squeue` call
        job_ids_str = ",".join(job_ids)
        command = f"squeue --me --jobs={job_ids_str} -o '%A|%j|%T'"
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

        # Determine if all jobs are finished
        running_states = {"PD", "R", "CG", "CF", "CA", "CD", "F", "NF", "TO"}
        if any(job["State"] in running_states for job in job_statuses):
            return job_statuses, False

        return job_statuses, True

    except Exception as e:
        print(f"Unexpected error: {e}")
        return "An unexpected error occurred.", False

def cancel_slurm_job(job_id):
    command = f"scancel {job_id}"
    result = execute_ssh_command(command)
    if result["returncode"] == 0:
        return {"Job ID": "", "Name":job_id, "State": "CANCELLED", "Time Used": "", "Nodes": "", "Reason": ""}, True
    else:
        return f"Error: {result['stderr']}", False

def are_jobs_finished(job_ids):
    command = f"squeue --me --jobs {','.join(job_ids)} -o '%i|%t'"
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
            print('all jobs are fininshed')
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


def get_next_runfile_message(runfile, session):
    """
    Returns the next runfile and corresponding message based on the current runfile.
    """
    file_parts = runfile.split('.')
    if len(file_parts) > 1:
        suffix = file_parts[-1]
        next_runfile = runfile
        next_job_message = ""

        if suffix == 'run1a':
            next_runfile = runfile.replace('1a', '1b')
            next_job_message = f"Please log in to view result, edit and submit the next runfile: '{next_runfile}'"
        elif suffix == 'run1b':
            next_runfile = runfile.replace('1b', '2a')
            next_job_message = f"Please log in to view result, edit and submit the next runfile: '{next_runfile}'"
        elif suffix == 'run2a':
            next_runfile = runfile.replace('2a', '2b')
            next_job_message = f"Please log in to view result, edit and submit the next runfile: '{next_runfile}'"
        elif suffix == 'run2b':
            next_job_message = f"All jobs for session '{session}' have completed."

        return next_runfile, next_job_message
    return runfile, ""
def process_job_submission(pid,selected_runfile, session,email):
    """
    Handles the job submission process asynchronously.
    """
    runfile = os.path.basename(selected_runfile)
    try:
        # Simulate remote submission process (replace with actual logic)
        print(f"Submitting job for '{runfile}'...")
        success = execute_remote_submit(pid, runfile ,session)

        # send email notification
        if email:
            confirmation_message = (
                f"Job for runfile '{runfile}' has been submitted successfully."
                if success
                else f"Failed to submit job for runfile '{runfile}'."
            )
            send_email('Job Submission Confirmation', confirmation_message, email)
        if success:
            #Monitor job status until completion
            job_ids = get_submitted_job_ids(selected_runfile)
            if job_ids:
                print(f"Monitoring job status for '{runfile}'...")
                all_jobs_done = monitor_slurm_jobs(job_ids)
                if all_jobs_done and email:
                    next_runfile, next_job_message= get_next_runfile_message(runfile, session)
                    completion_message = f"All jobs for runfile '{runfile}' have completed. {next_job_message}"
                    send_email('Job Completion Notification', completion_message, email)

    except Exception as e:
        # Log the exception for debugging (could also send an email or update a status)
        print(f"Error during job submission for '{runfile}': {e}")

def make_summary(pid, activate_session):
    full_command = f"{make_summary_command} {pid} {activate_session}"
    result = execute_ssh_command(full_command, set_user_command=set_user_command)
    if result["returncode"] == 0:
        print(f"Successfully made summary for {pid}")
    else:
        print(f"Error in execution: {result['stderr']}")


def generate_result_url(pid, session_name):
    # Validate inputs
    if not pid or not session_name:
        raise ValueError(f"Invalid inputs - pid: {pid}, session: {session_name}")

    # Check if session_name is init_session
    is_init = session_name == init_session

    if is_init:
        url = f"http://taps.lmtgtm.org/lmtslr/{pid}/README.html"
    else:
        url = f"http://taps.lmtgtm.org/lmthelpdesk/pipeline_web/{pid}/{session_name}/{pid}/README.html"
    return url

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

def execute_git_pull(project_path):
    """Execute git pull in the project directory and return status."""
    try:
        # Store the current working directory
        current_dir = os.getcwd()
        
        try:
            # Change to project directory
            os.chdir(project_path)
            
            # Execute git pull
            result = subprocess.run(['git', 'pull'], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Format the success message
                #message = f"Repository: {os.path.basename(project_path)}\n"
                message = "Status: Success\n"
                message += "Output:\n" + result.stdout
                return True, message
            else:
                # Format the error message
                #message = f"Repository: {os.path.basename(project_path)}\n"
                message = "Status: Failed\n"
                message += "Error:\n" + result.stderr
                return False, message
        finally:
            # Always change back to the original directory
            os.chdir(current_dir)
    except Exception as e:
        # Format the exception message
        #message = f"Repository: {os.path.basename(project_path)}\n"
        message = "Status: Error\n"
        message += f"Exception: {str(e)}"
        return False, message

    