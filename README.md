# LMT Web

## Introduction

This web application serves as an interface for managing pipeline jobs and configurations. The sections below provide instructions on setting up and running the application.

## Setup

### Environment and Dependencies

Follow these steps to set up your environment and install necessary dependencies:

1. **Create a virtual environment and install the dependencies:**
    ```shell
    python3 -m venv env
    pip install -r requirements.txt
    ```

2. **Activate the virtual environment:**
    ```shell
    source env/bin/activate
    ```

3. **Modify the configuration file:**
    - Modify the `config.yaml` file to specify the file directories for the application.
    - path:
      - `work_lmt`: The directory where the file located for the user. For example: /nese/toltec/dataprod_lmtslr/work_lmt_helpdesk/pipeline_web.
      - `python_path`: the virtual enviroment python path. For example: /home/lmtmc_umass_edu/pipeline_web/env/bin/python3
    - ssh:
      - `username`: The username for the remote server. For example: lmthelpdesk_umass_edu.
      - `hostname`: The host of the remote server. For example: unity.rc.umass.edu.
      
4. **Modify the database:**
    - The repository includes a `users.db`. If you wish to create a new `users.db`
   or add a user, consider revising and running the code in `users_mgt.py`. Further enhancements for the database organization may be required.

## Running the Application

1. **Start the application:**
    ```shell
    python3 app.py --port 8080
    ```
    The application will be accessible at [http://127.0.0.1:8080](http://127.0.0.1:8080). If you don't specify a port, the default address will be [http://127.0.0.1:8000](http://127.0.0.1:8000).

2. **Setting up on a remote server:**
    - If you are running the application on a remote server, consider using local port forwarding. Add the following configuration to your `.ssh/config`:
        ```shell
        LocalForward 5000 127.0.0.1:8000
        ```
    - This configuration forwards the local port 5000 to port 8000 on your remote server. You can then access the application using [http://127.0.0.1:5000](http://127.0.0.1:5000) in your local web browser.

## Usage

### **Login**
Use the Project Id (PID) to login. 
- Example: 'PID = '2023-S1-US-17' | Password = '1234''
- If the password for the PID is not valid, an error message will be displayed.


### **Session Management**
Default session (`session-0`) and previous sessions will be displayed.
- If `session-0` is selected, you can clone it:
    1. Click `CLONE SESSION`.
    2. Input a number for the new session name.
- If other session is selected, you can clone or delete it.

### **Runfile Management**
- After selecting a session, available runfiles in this session will be displayed.
- Choose a runfile to view its content.
- Click `DELETE` to delete the runfile.
- Click `CLONE` to clone the runfile.
    
### **Table Management**
- After selecting a row or multiply row of the table, you can edit delete or clone the row(s).

### **Job Submit**
- After selecting a runfile and typing a vaild email, you can submit the job by clicking `SUBMIT JOB`.

### **Job Status**
- After submitting a job, you can check the job status by clicking `JOB STATUS`.

### **FLOW CHART**
[Flow Chart](./Pipeline_web_slide.pdf)