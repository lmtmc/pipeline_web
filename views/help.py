import dash
from dash import dcc, html

def create_layout():
    return html.Div([
        html.Div([
            html.H2("Help Documentation"),
            html.Hr(),
            
            html.Div([
                html.H3("Login"),
                html.P("To log in to the application:"),
                html.Ul([
                    html.Li("Enter your Project ID"),
                    html.Li("Enter your password"),
                    html.Li("Click the 'Login' button")
                ]),
                html.Img(src="assets/img/app_login.png", alt="Login Example")
            ], className="help-section"),
            
            html.Div([
                html.H3("Session Management"),
                html.P("Manage your sessions:"),
                html.Ul([
                    html.Li("Clone existing sessions"),
                    html.Li("Delete sessions"),
                    html.Li("View session details")
                ]),
                html.Img(src="assets/img/app_session_list.png", alt="Session Management Example")
            ], className="help-section"),
            
            html.Div([
                html.H3("Runfile Management"),
                html.P("Work with runfiles:"),
                html.Ul([
                    html.Li("Select runfiles from your project"),
                    html.Li("Submit jobs"),
                    html.Li("Check job status")
                ]),
                html.Img(src="assets/img/app_runfile_edit.png", alt="Runfile Management Example")
            ], className="help-section"),
            
            html.Div([
                html.H3("Table Management"),
                html.P("Manage rows in your runfiles:"),
                html.Ul([
                    html.Li("Clone rows"),
                    html.Li("Delete rows"),
                    html.Li("Edit row data")
                ]),
                html.Img(src="assets/img/app_edit_row.png", alt="Table Management Example")
            ], className="help-section"),
            
            html.Div([
                html.H3("Single Row Edit"),
                html.P("Edit a single row:"),
                html.Ul([
                    html.Li("Click on a row to edit"),
                    html.Li("Make your changes"),
                    html.Li("Save the changes")
                ]),
                html.Img(src="assets/img/app_single_row_parameter.png", alt="Single Row Edit Example")
            ], className="help-section"),
            
            html.Div([
                html.H3("Multiple Row Edit"),
                html.P("Edit multiple rows at once:"),
                html.Ul([
                    html.Li("Select multiple rows"),
                    html.Li("Make bulk changes"),
                    html.Li("Save all changes")
                ]),
                html.Img(src="assets/img/app_multi_row_parameter.png", alt="Multiple Row Edit Example")
            ], className="help-section"),
            
            html.Div([
                html.H3("Submit Job"),
                html.P("Submit jobs for processing:"),
                html.Ul([
                    html.Li("Select the runfile"),
                    html.Li("Configure job parameters"),
                    html.Li("Submit and receive email notifications")
                ]),
                html.Img(src="assets/img/app_submit_job.png", alt="Job Submission Example")
            ], className="help-section"),
            
            html.Div([
                html.H3("Job Status"),
                html.P("Check job status:"),
                html.Ul([
                    html.Li("View running jobs"),
                    html.Li("Check completion status"),
                    html.Li("View job results")
                ]),
                html.Img(src="assets/img/app_job_status.png", alt="Job Status Example")
            ], className="help-section")
        ], className="help-container")
    ])

# Assign the layout
layout = create_layout()