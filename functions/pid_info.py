# get pid source, obsnum, email and instrument
import os
import subprocess
import re

from config_loader import load_config
try :
    config = load_config()
except Exception as e:
    print(f"Error loading configuration: {e}")

python_path = config['path']['python_path']
def get_source(default_work_lmt, pid):
    pid_path = os.path.join(default_work_lmt, 'lmtoy_run', f'lmtoy_{pid}')

    mk_runs_file = os.path.join(pid_path, 'mk_runs.py')
    print(f'mk_runs_file: {mk_runs_file}')
    result = subprocess.run([python_path, mk_runs_file], capture_output=True,
                            text=True, cwd=pid_path)
    # checks if the command ran successfully(return code 0)
    print(f'result: {result}')
    if result.returncode == 0:
        output = result.stdout  # converts the stdout string to a regular string
    else:
        output = result.stderr  # convert the error message to a string
    pattern = r"(\w+)\[\d+/\d+\] : ([\d,]+)"
    matches = re.findall(pattern, output)
    # sources = {name: list(map(int, obsnums.split(','))) for name, obsnums in matches}
    sources = {name: [int(x) for x in obsnums.split(',')] for name, obsnums in matches}
    print(f'sources: {sources}')
    return sources

def get_email(pid):
    email = config[pid]['email']
    print(f'email: {email}')
    return email
def get_instrument(pid):
    instrument = config[pid]['instrument']
    print(f'instrument: {instrument}')
    return instrument
