import dash
from dash import dcc, html

# Define custom styles
help_styles = {
    'container': {
        'maxWidth': '1200px',
        'margin': '0 auto',
        'padding': '20px',
        'backgroundColor': '#f8f9fa',
        'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif'
    },
    'title': {
        'color': '#2c3e50',
        'textAlign': 'center',
        'marginBottom': '30px',
        'fontSize': '3rem',
        'fontWeight': '600'
    },
    'section': {
        'backgroundColor': 'white',
        'borderRadius': '10px',
        'padding': '25px',
        'marginBottom': '30px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
    },
    'sectionTitle': {
        'color': '#2c3e50',
        'fontSize': '2.2rem',
        'marginBottom': '20px',
        'paddingBottom': '10px',
        'borderBottom': '2px solid #e9ecef'
    },
    'subsectionTitle': {
        'color': '#34495e',
        'fontSize': '1.8rem',
        'marginTop': '25px',
        'marginBottom': '15px'
    },
    'paragraph': {
        'color': '#495057',
        'fontSize': '1.3rem',
        'lineHeight': '1.6',
        'marginBottom': '15px'
    },
    'list': {
        'listStyleType': 'none',
        'paddingLeft': '0'
    },
    'listItem': {
        'marginBottom': '15px',
        'padding': '15px',
        'backgroundColor': '#f8f9fa',
        'borderRadius': '5px',
        'borderLeft': '4px solid #007bff',
        'fontSize': '1.3rem'
    },
    'featureTitle': {
        'color': '#007bff',
        'fontSize': '1.5rem',
        'fontWeight': '600',
        'marginBottom': '10px'
    },
    'image': {
        'maxWidth': '100%',
        'borderRadius': '8px',
        'marginTop': '20px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
    },
    'securityNote': {
        'backgroundColor': '#fff3cd',
        'borderLeft': '4px solid #ffc107',
        'padding': '20px',
        'marginTop': '20px',
        'borderRadius': '5px',
        'fontSize': '1.3rem'
    }
}

def create_layout():
    return html.Div([
        html.Div([
            html.H2("Help Documentation", style=help_styles['title']),
            html.Hr(style={'borderColor': '#e9ecef', 'marginBottom': '40px'}),
            
            # Admin Page Section
            html.Div([
                html.H3("Admin Page", style=help_styles['sectionTitle']),
                html.P("The Admin Page is a dashboard interface for managing LMT (Large Millimeter Telescope) projects. It provides tools for viewing, updating, and managing project repositories and their associated profiles.",
                      style=help_styles['paragraph']),
                
                html.H4("Main Features", style=help_styles['subsectionTitle']),
                html.Ul([
                    html.Li([
                        html.Strong("Projects List", style=help_styles['featureTitle']),
                        html.P("Projects are organized by year in tabs, showing:", style=help_styles['paragraph']),
                        html.Ul([
                            html.Li("Project ID and number", style=help_styles['listItem']),
                            html.Li("Last modified date", style=help_styles['listItem']),
                            html.Li("GitHub link", style=help_styles['listItem']),
                            html.Li("View/Edit options", style=help_styles['listItem']),
                            html.Li("Profile status", style=help_styles['listItem']),
                            html.Li("Repository status", style=help_styles['listItem'])
                        ], style=help_styles['list'])
                    ], style=help_styles['listItem']),
                    
                    html.Li([
                        html.Strong("Project Management", style=help_styles['featureTitle']),
                        html.P("Key functions:", style=help_styles['paragraph']),
                        html.Ul([
                            html.Li("View projects by year", style=help_styles['listItem']),
                            html.Li("Search and filter projects", style=help_styles['listItem']),
                            html.Li("Sort by any column", style=help_styles['listItem']),
                            html.Li("Update repositories individually or all at once", style=help_styles['listItem'])
                        ], style=help_styles['list'])
                    ], style=help_styles['listItem']),
                    
                    html.Li([
                        html.Strong("Profile Management", style=help_styles['featureTitle']),
                        html.P("Manage project profiles:", style=help_styles['paragraph']),
                        html.Ul([
                            html.Li("View current profile settings", style=help_styles['listItem']),
                            html.Li("Update email addresses", style=help_styles['listItem']),
                            html.Li("Set and change passwords", style=help_styles['listItem']),
                            html.Li("Toggle password visibility", style=help_styles['listItem'])
                        ], style=help_styles['list'])
                    ], style=help_styles['listItem']),
                    
                    html.Li([
                        html.Strong("Status Indicators", style=help_styles['featureTitle']),
                        html.P("Understand different statuses:", style=help_styles['paragraph']),
                        html.Ul([
                            html.Li("Profile Status: 'Profile' or 'Profile Set'", style=help_styles['listItem']),
                            html.Li("Repository Status: 'Up to date', 'Needs update', or 'Not tracked'", style=help_styles['listItem'])
                        ], style=help_styles['list'])
                    ], style=help_styles['listItem'])
                ], style=help_styles['list']),
                
                html.H4("Best Practices", style=help_styles['subsectionTitle']),
                html.Ul([
                    html.Li("Regular repository updates", style=help_styles['listItem']),
                    html.Li("Proper profile management", style=help_styles['listItem']),
                    html.Li("Regular status checks", style=help_styles['listItem']),
                    html.Li("Secure password practices", style=help_styles['listItem'])
                ], style=help_styles['list']),
                
                html.H4("Security Notes", style=help_styles['subsectionTitle']),
                html.Div([
                    html.Ul([
                        html.Li("Passwords are stored securely", style=help_styles['listItem']),
                        html.Li("Use password visibility toggle for verification", style=help_styles['listItem']),
                        html.Li("Always confirm passwords when updating", style=help_styles['listItem']),
                        html.Li("Access is restricted to authorized users", style=help_styles['listItem'])
                    ], style=help_styles['list'])
                ], style=help_styles['securityNote'])
            ], style=help_styles['section']),
            
            # Login Section
            html.Div([
                html.H3("Login", style=help_styles['sectionTitle']),
                html.P("To log in to the application:", style=help_styles['paragraph']),
                html.Ul([
                    html.Li("Enter your Project ID", style=help_styles['listItem']),
                    html.Li("Enter your password", style=help_styles['listItem']),
                    html.Li("Click the 'Login' button", style=help_styles['listItem'])
                ], style=help_styles['list']),
                html.Img(src="assets/img/app_login.png", alt="Login Example", style=help_styles['image'])
            ], style=help_styles['section']),
            
            # Session Management Section
            html.Div([
                html.H3("Session Management", style=help_styles['sectionTitle']),
                html.P("Manage your sessions:", style=help_styles['paragraph']),
                html.Ul([
                    html.Li("Clone existing sessions", style=help_styles['listItem']),
                    html.Li("Delete sessions", style=help_styles['listItem']),
                    html.Li("View session details", style=help_styles['listItem'])
                ], style=help_styles['list']),
                html.Img(src="assets/img/app_session_list.png", alt="Session Management Example", style=help_styles['image'])
            ], style=help_styles['section']),
            
            # Runfile Management Section
            html.Div([
                html.H3("Runfile Management", style=help_styles['sectionTitle']),
                html.P("Work with runfiles:", style=help_styles['paragraph']),
                html.Ul([
                    html.Li("Select runfiles from your project", style=help_styles['listItem']),
                    html.Li("Submit jobs", style=help_styles['listItem']),
                    html.Li("Check job status", style=help_styles['listItem'])
                ], style=help_styles['list']),
                html.Img(src="assets/img/app_runfile_edit.png", alt="Runfile Management Example", style=help_styles['image'])
            ], style=help_styles['section']),
            
            # Table Management Section
            html.Div([
                html.H3("Table Management", style=help_styles['sectionTitle']),
                html.P("Manage rows in your runfiles:", style=help_styles['paragraph']),
                html.Ul([
                    html.Li("Clone rows", style=help_styles['listItem']),
                    html.Li("Delete rows", style=help_styles['listItem']),
                    html.Li("Edit row data", style=help_styles['listItem'])
                ], style=help_styles['list']),
                html.Img(src="assets/img/app_edit_row.png", alt="Table Management Example", style=help_styles['image'])
            ], style=help_styles['section']),
            
            # Single Row Edit Section
            html.Div([
                html.H3("Single Row Edit", style=help_styles['sectionTitle']),
                html.P("Edit a single row:", style=help_styles['paragraph']),
                html.Ul([
                    html.Li("Click on a row to edit", style=help_styles['listItem']),
                    html.Li("Make your changes", style=help_styles['listItem']),
                    html.Li("Save the changes", style=help_styles['listItem'])
                ], style=help_styles['list']),
                html.Img(src="assets/img/app_single_row_parameter.png", alt="Single Row Edit Example", style=help_styles['image'])
            ], style=help_styles['section']),
            
            # Multiple Row Edit Section
            html.Div([
                html.H3("Multiple Row Edit", style=help_styles['sectionTitle']),
                html.P("Edit multiple rows at once:", style=help_styles['paragraph']),
                html.Ul([
                    html.Li("Select multiple rows", style=help_styles['listItem']),
                    html.Li("Make bulk changes", style=help_styles['listItem']),
                    html.Li("Save all changes", style=help_styles['listItem'])
                ], style=help_styles['list']),
                html.Img(src="assets/img/app_multi_row_parameter.png", alt="Multiple Row Edit Example", style=help_styles['image'])
            ], style=help_styles['section']),
            
            # Submit Job Section
            html.Div([
                html.H3("Submit Job", style=help_styles['sectionTitle']),
                html.P("Submit jobs for processing:", style=help_styles['paragraph']),
                html.Ul([
                    html.Li("Select the runfile", style=help_styles['listItem']),
                    html.Li("Configure job parameters", style=help_styles['listItem']),
                    html.Li("Submit and receive email notifications", style=help_styles['listItem'])
                ], style=help_styles['list']),
                html.Img(src="assets/img/app_submit_job.png", alt="Job Submission Example", style=help_styles['image'])
            ], style=help_styles['section']),
            
            # Job Status Section
            html.Div([
                html.H3("Job Status", style=help_styles['sectionTitle']),
                html.P("Check job status:", style=help_styles['paragraph']),
                html.Ul([
                    html.Li("View running jobs", style=help_styles['listItem']),
                    html.Li("Check completion status", style=help_styles['listItem']),
                    html.Li("View job results", style=help_styles['listItem'])
                ], style=help_styles['list']),
                html.Img(src="assets/img/app_job_status.png", alt="Job Status Example", style=help_styles['image'])
            ], style=help_styles['section'])
        ], style=help_styles['container'])
    ])

# Assign the layout
layout = create_layout()