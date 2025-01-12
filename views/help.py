from dash import dcc, html

# Separate markdown content into different parts
login_content = '''
## Help Document 

### **Login**
- Use your Project ID (PID) and password to log in.
    - **Example**: PID = 2021-S1-US-3 | Password = 1234
- If the password for the PID is invalid, an error message will be displayed.
'''

session_management_content = '''
### **Session Management**
- The default session (SESSION-0) and any previously created sessions will be displayed.
- If SESSION-0 is selected, you can clone it:
    1. Click CLONE SESSION.
    2. Enter a number for the new session name.
- If a session other than SESSION-0 is selected, you can:
    1. Clone the session.
    2. Delete the session.
'''

runfile_management_content = '''
### **Runfile Management**
- After selecting a session, all available runfiles within that session will be displayed.
- Select a runfile to view its content in the table.
- The runfile name is shown in the top-left corner of the table.
- If the runfile is not part of SESSION-0, you can:
    1. **SUBMIT JOB**: submit the selected runfile.
    2. **CHECK STATUS**: check the status of running job on UNITY.
    3. **VIEW RESULT**: view the result on the webpage.
'''

table_management_content = '''
### **Table Management**
- For runfiles not in SESSION-0, after selecting a row or multiple rows, you can:
    1. Click CLONE ROW to duplicate rows.
    2. Click DELETE ROW to remove rows.
    3. Click EDIT ROW to modify rows.
'''
single_row_edit_content = '''
#### **Edit a Single Row**
- Select a row, click the EDIT button.
- A modal with all available parameters will appear.
- Modify the data and click the APPLY button to save the changes.
- Click the CANCEL button to close the modal without saving changes.
'''

multiple_row_edit_content = '''
#### **Edit Multiple Rows**
- To edit multiple rows, select the rows and click the EDIT button.
- Select the column you want to edit and input a new value and click the APPLY button to save the changes.
- Click the CANCEL button to close the modal without saving changes.
'''

submit_job_content = '''
### **Submit Job**
- If there is no running jobs for the runfile, the SUBMIT JOB button will be enabled. (to be implemented)
- Enter your email address and click the SUBMIT JOB button to send the job to UNITY.
- Upon successful submission:
    - A notification will be sent to your email (to be implemented).
    - You can log out or continue submitting additional jobs.
- Once the job is finished:
    - You will receive another notification with links to view the results (to be implemented).
'''

job_status_content = '''
### **Job Status**
- Click the "CHECK STATUS" to check the status of current running jobs related to the selected runfile.
'''

# Layout with markdown content and images
layout = html.Div([
    # Login Section

    dcc.Markdown(login_content),
    html.Img(src='./assets/img/app_login.png', style={'width': '30%', 'margin': '10px',}),
    html.Hr(),
    # Session Management Section
    dcc.Markdown(session_management_content),
    html.Img(src='./assets/img/app_session_list.png', style={'width': '30%', 'margin': 'auto'}),
    html.Hr(),
    # Runfile Management Section
    dcc.Markdown(runfile_management_content),
    html.Img(src='./assets/img/app_runfile_edit.png', style={'width': '100%', 'margin': 'auto'}),
    html.Hr(),
    # Table Management Section
    dcc.Markdown(table_management_content),
    html.Img(src='./assets/img/app_edit_row.png', style={'width': '30%', 'margin': 'auto'}),
    html.Hr(),
    # Single Row Edit Section
    dcc.Markdown(single_row_edit_content),
    html.Img(src='./assets/img/app_single_row_parameter.png', style={'width': '50%', 'margin': 'auto'}),
    html.Hr(),
    # Multiple Row Edit Section
    dcc.Markdown(multiple_row_edit_content),
    html.Img(src='./assets/img/app_multi_row_parameter.png', style={'width': '60%', 'margin': 'auto'}),
    html.Hr(),
    # Submit Job Section
    dcc.Markdown(submit_job_content),
    html.Img(src='./assets/img/app_submit_job.png', style={'width': '30%', 'margin': 'auto'}),
    html.Hr(),
    # Job Status Section
    dcc.Markdown(job_status_content),
    html.Img(src='./assets/img/app_job_status.png', style={'width': '100%', 'margin': 'auto'}),
    html.Hr(),
], style={
    'width': '80%',
    'margin': 'auto',
    'text-align': 'left',
    'font-size': '16px',
    'padding-bottom': '50px'  # Adds space at the bottom of the page
})