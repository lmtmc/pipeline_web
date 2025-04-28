# display all the projects in the github repo
import os
from datetime import datetime
import dash
from dash import dcc, html, Input, Output, State, ALL
from my_server import app
from flask_login import logout_user, current_user
from flask import session
from views import login, project_layout, help, ui_elements as ui
import argparse
from config_loader import load_config

# load the configuration
try:
    config = load_config()
except Exception as e:
    print(f"Error loading configuration: {e}")
    config = {}

# Constants
PREFIX = config.get('path', {}).get('prefix', '')

def get_projects_list(folder_path):
    """Get list of projects from a folder path."""
    try:
        if not os.path.exists(folder_path):
            return []
        
        folder_path = os.path.join(folder_path, 'lmtoy_run')
        # Get all directories in the folder path
        projects = [d for d in os.listdir(folder_path) 
                   if os.path.isdir(os.path.join(folder_path, d))]
        
        # Get project details
        project_details = []
        for project in projects:
            if project.startswith('lmtoy'):
                pid = project.split('_')[1]
                project_path = os.path.join(folder_path, project)
                created_time = datetime.fromtimestamp(os.path.getctime(project_path))
                modified_time = datetime.fromtimestamp(os.path.getmtime(project_path))
                
                project_details.append({
                    'name': pid,
                    'path': project_path,
                    'created_time': created_time,
                    'modified_time': modified_time
                })
        
        return project_details
    except Exception as e:
        print(f"Error getting projects list: {e}")
        return []

def get_project_details(project_path):
    """Get detailed information about a specific project."""
    try:
        if not os.path.exists(project_path):
            return None
        
        return {
            'name': os.path.basename(project_path),
            'path': project_path,
            'modified_time': datetime.fromtimestamp(os.path.getmtime(project_path)),
            'files': [f for f in os.listdir(project_path) 
                     if os.path.isfile(os.path.join(project_path, f))]
        }
    except Exception as e:
        print(f"Error getting project details: {e}")
        return None 
    
def create_layout():
    """Create the admin page layout."""
    folder_path = config.get('path', {}).get('work_lmt', '')
    projects = get_projects_list(folder_path)
    
    # Sort projects by last modified time (newest first)
    projects.sort(key=lambda x: x['modified_time'], reverse=True)
    
    # Create table rows
    table_rows = []
    for project in projects:
        github_url = f"https://github.com/lmtoy/lmtoy_{project['name']}"
        table_rows.append(
            html.Tr([
                html.Td(project['name'], className='project-name'),
                html.Td(f"{project['modified_time'].strftime('%Y-%m-%d %H:%M:%S')}", className='project-time'),
                html.Td(
                    html.Div([
                        html.A(
                            'GitHub Page',
                            href=github_url,
                            target='_blank',
                            className='github-link'
                        ),
                        html.A(
                            'Edit',
                            id={'type': 'view-project', 'index': project['name']},
                            className='view-button',
                            n_clicks=0
                        )
                    ], className='action-buttons')
                )
            ])
        )
    
    return html.Div([
        html.Div(id='admin-alert', style={'display': 'none'}),
        html.H1('Projects List', className='page-title'),
        html.Div([
            html.Table(
                [
                    html.Thead(
                        html.Tr([
                            html.Th('Project ID', className='project-id-header'),
                            html.Th('Last Modified', className='modified-header'),
                            html.Th('Actions', className='actions-header')
                        ])
                    ),
                    html.Tbody(table_rows)
                ],
                className='projects-table'
            )
        ], className='table-container')
    ], className='projects-container')

layout = create_layout()

@app.callback(
    [Output('url', 'pathname'),
     Output('admin-alert', 'children'),
     Output('admin-alert', 'style')],
    Input({'type': 'view-project', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def handle_edit_button(n_clicks):
    if not any(n_clicks):
        raise dash.exceptions.PreventUpdate
    
    # Get the index of the clicked button
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    pid = eval(button_id)['index']
    
    # Check if user is authenticated and is admin
    if not current_user.is_authenticated:
        return dash.no_update, "Please log in to access this feature.", {'display': 'block', 'color': 'red'}
    
    if not current_user.is_admin:
        return dash.no_update, "You are not authorized to access this page. You can login using PID", {'display': 'block', 'color': 'red'}
    
    # Redirect to the project layout with the selected project
    return f"{PREFIX}project/{pid}", "", {'display': 'none'}


