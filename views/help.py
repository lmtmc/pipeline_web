from dash import dcc, html

markdown_content = '''
## Help Document 

### **Login**
- Use your Project ID (PID) and password to log in.
    - **Example**: PID = 2021-S1-US-3 | Password = 1234
- If the password for the PID is invalid, an error message will be displayed.

---

### **Session Management**
- The default session (SESSION-0) and any previously created sessions will be displayed.
- If SESSION-0 is selected, you can clone it:
    1. Click CLONE SESSION.
    2. Enter a number for the new session name.
- If a session other than SESSION-0 is selected, you can:
    1. Clone the session.
    2. Delete the session.

---

### **Runfile Management**
- After selecting a session, all available runfiles within that session will be displayed.
- Select a runfile to view its content in the table.
- The runfile name is shown in the top-left corner of the table.
- If the runfile is not part of SESSION-0, you can:
    1. **Clone the runfile**: Create a duplicate of the runfile.
    2. **Delete the runfile**: Remove the runfile from the session.

---
    
### **Table Management**
- For runfiles not in SESSION-0, after selecting a row, you can:
    1. Click CLONE ROW to duplicate rows.
    2. Click DELETE ROW to remove rows.
    3. Click EDIT ROW to modify rows (must share the same source).

---

### **Submit Job**
- After selecting a runfile and providing a valid email address for notifications, the SUBMIT JOB button will be enabled.
- Click SUBMIT JOB to send the job to UNITY.
- Upon successful submission:
    - A notification will be sent to your email (to be implemented).
    - You can log out or continue submitting additional jobs.
- Once the job is finished:
    - You will receive another notification with links to view the results (to be implemented).

---

### **Job Status**
- Check the status of a submitted job using the job ID, username, or job name (to be implemented).

'''

layout = html.Div(dcc.Markdown(markdown_content),
                  style={'margin-top': '50px', 'margin-left': '100px', 'margin-right': 'auto', 'margin-bottom': '100px',
                         'text-align': 'left', 'font-size':'20px'})
