import os
from datetime import datetime
import dash
from dash import dcc, html, Input, Output, State, ALL, dash_table, callback, ctx, no_update
import dash_bootstrap_components as dbc
from my_server import app
from flask_login import logout_user, current_user
import pandas as pd
from dash.exceptions import PreventUpdate
import requests
import subprocess
from functools import lru_cache
import logging
import sqlite3

from config_loader import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('admin_page.log')
    ]
)
logger = logging.getLogger(__name__)

# load the configuration
try:
    config = load_config()
except Exception as e:
    print(f"Error loading configuration: {e}")
    config = {}

# Constants
PREFIX = config.get('path', {}).get('prefix', '')
PAGE_SIZE = 10
GITHUB_API_URL = config.get('github', {}).get('api_url', 'https://api.github.com/orgs/lmtoy/repos')
REPO_PREFIX = config.get('github', {}).get('repo_prefix', 'lmtoy_')

DB_PATH = "instance/users.db"
print(f"DB_PATH: {DB_PATH}")
# Cache the GitHub API response for 5 minutes
@lru_cache(maxsize=1)
def get_github_repos():
    """Get list of repositories from lmtoy GitHub organization with caching."""
    try:
        all_repos = []
        page = 1
        per_page = 100

        while True:
            response = requests.get(
                GITHUB_API_URL,
                params={'page': page, 'per_page': per_page},
                timeout=10
            )

            if response.status_code != 200:
                logger.error(f"Error fetching GitHub repos: {response.status_code}")
                break

            repos = response.json()
            if not repos:
                break

            all_repos.extend([repo['name'] for repo in repos if repo['name'].startswith(REPO_PREFIX)])
            page += 1

            if len(repos) < per_page:
                break

        logger.info(f"Found {len(all_repos)} repositories")
        return all_repos
    except Exception as e:
        logger.error(f"Error fetching GitHub repos: {e}")
        return []

def get_project_credentials(pid):
    """Get both password and email for a project in one query."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT password, email FROM user WHERE username = ?', (pid,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return {'password': result[0], 'email': result[1]}
        return {'password': None, 'email': None}
    except Exception as e:
        logger.error(f"Error reading credentials for project {pid}: {e}")
        return {'password': None, 'email': None}


def update_project_credentials(pid, password=None, email=None):
    """Update password and/or email for a project."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get current credentials
        current_creds = get_project_credentials(pid)

        # Use current values if new ones not provided
        new_password = password if password is not None else current_creds['password']
        new_email = email if email is not None else current_creds['email']

        # Check if user exists
        cursor.execute('SELECT 1 FROM user WHERE username = ?', (pid,))
        exists = cursor.fetchone()

        if exists:
            cursor.execute('''
                UPDATE user 
                SET password = ?, email = ?
                WHERE username = ?
            ''', (new_password, new_email, pid))
        else:
            cursor.execute('''
                INSERT INTO user (username, password, email, is_admin)
                VALUES (?, ?, ?, 0)
            ''', (pid, new_password, new_email))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error updating credentials for project {pid}: {e}")
        return False


def get_projects_list(folder_path):
    """Get list of projects from a folder path with error handling."""
    try:
        if not os.path.exists(folder_path):
            logger.warning(f"Folder path does not exist: {folder_path}")
            return pd.DataFrame()

        folder_path = os.path.join(folder_path, 'lmtoy_run')
        if not os.path.exists(folder_path):
            logger.warning(f"lmtoy_run folder does not exist: {folder_path}")
            return pd.DataFrame()

        projects = [d for d in os.listdir(folder_path)
                    if os.path.isdir(os.path.join(folder_path, d))]

        project_details = []
        for project in projects:
            if project.startswith(REPO_PREFIX):
                try:
                    pid = project.split('_')[1]
                    project_path = os.path.join(folder_path, project)
                    modified_time = datetime.fromtimestamp(os.path.getmtime(project_path))
                    github_url = f"[GitHub](https://github.com/lmtoy/{project})"

                    # Check if credentials exist
                    creds = get_project_credentials(pid)
                    profile_status = "👤 Set" if creds['password'] else "👤 Not Set"

                    project_details.append({
                        'Project ID': pid,
                        'Last Modified': modified_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'GitHub': github_url,
                        'View/Edit': '📝 View/Edit',
                        'Update': '🔄 Update',
                        'Profile': profile_status
                    })
                except Exception as e:
                    logger.error(f"Error processing project {project}: {e}")
                    continue

        df = pd.DataFrame(project_details)
        if not df.empty:
            df = df.sort_values('Last Modified', ascending=False)
            df.insert(0, 'No.', range(1, len(df) + 1))
        return df

    except Exception as e:
        logger.error(f"Error getting projects list: {e}")
        return pd.DataFrame()


def create_layout():
    """Create the admin page layout with optimized styling."""
    folder_path = config.get('path', {}).get('work_lmt', '')
    df = get_projects_list(folder_path)

    return html.Div([
        # Store for current project ID and modal state
        dcc.Store(id='current-project-store'),
        dbc.Alert(id='admin-alert',
                  is_open=False,
                  dismissable=True,
                  duration=4500),
        dbc.Alert(id='profile-alert',
                  is_open=False,
                  dismissable=True,
                  duration=4500,
                  style={
                      'position': 'fixed',
                      'top': '20px',
                      'right': '20px',
                      'zIndex': 9999,
                      'minWidth': '300px'
                  }),
        dbc.Modal([
            dbc.ModalHeader("Project Profile Management"),
            dbc.ModalBody([
                html.Div(id='modal-project-info'),
                html.Hr(),
                html.Div([
                    html.H6("New Email Address", className='mb-2'),
                    dbc.Row([
                        dbc.Col(
                            dbc.Input(
                                id='new-email-input',
                                type='text',
                                placeholder='Enter email address',
                                style={
                                    'border': '1px solid #ced4da',
                                    'borderRadius': '4px',
                                    'padding': '8px 12px',
                                    'width': '100%',
                                    'fontSize': '14px',
                                    'height': '38px'
                                }
                            ),
                            width=12
                        ),
                    ], className='mb-4'),
                ]),
                html.Div([
                    html.H6("New Password", className='mb-2'),
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                dbc.Input(
                                    id='new-password-input',
                                    type='text',
                                    placeholder='Enter new password',
                                    style={
                                        'border': '1px solid #ced4da',
                                        'borderRadius': '4px 0 0 4px',
                                        'padding': '8px 12px',
                                        'width': 'calc(100% - 38px)',
                                        'fontSize': '14px',
                                        'height': '38px',
                                        'display': 'inline-block',
                                        'verticalAlign': 'top'
                                    }
                                ),
                                dbc.Button("👁️", id='toggle-password-btn', outline=True, 
                                    style={
                                        'border': '1px solid #ced4da',
                                        'borderRadius': '0 4px 4px 0',
                                        'height': '38px',
                                        'width': '38px',
                                        'padding': '0',
                                        'display': 'inline-block',
                                        'verticalAlign': 'top',
                                        'marginLeft': '-1px'
                                    }
                                ),
                            ], style={'display': 'flex', 'alignItems': 'center'}),
                        ], width=12),
                    ], className='mb-3 g-0'),
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                dbc.Input(
                                    id='confirm-password-input',
                                    type='text',
                                    placeholder='Confirm new password',
                                    style={
                                        'border': '1px solid #ced4da',
                                        'borderRadius': '4px 0 0 4px',
                                        'padding': '8px 12px',
                                        'width': 'calc(100% - 38px)',
                                        'fontSize': '14px',
                                        'height': '38px',
                                        'display': 'inline-block',
                                        'verticalAlign': 'top'
                                    }
                                ),
                                dbc.Button("👁️", id='toggle-confirm-password-btn', outline=True, 
                                    style={
                                        'border': '1px solid #ced4da',
                                        'borderRadius': '0 4px 4px 0',
                                        'height': '38px',
                                        'width': '38px',
                                        'padding': '0',
                                        'display': 'inline-block',
                                        'verticalAlign': 'top',
                                        'marginLeft': '-1px'
                                    }
                                ),
                            ], style={'display': 'flex', 'alignItems': 'center'}),
                        ], width=12),
                    ], className='mb-3 g-0'),
                ]),
            ]),
            dbc.ModalFooter([
                dbc.Button("Save", id='save-profile-btn', color='success',className='ms-auto me-2'),
                dbc.Button("Close", id='close-modal-btn', ),
                
            ]),
        ], id='profile-modal', is_open=False, size="lg", backdrop="static"),

        html.Div([
            html.H1('Projects List', className='page-title',
                    style={'display': 'inline-block', 'marginRight': '20px'}),
            dbc.Button('Update All Projects', id='update-projects-btn', color='success')
        ], style={'display': 'flex', 'justifyContent': 'space-between',
                  'alignItems': 'center', 'marginBottom': '20px'}),

        html.Div([
            dash_table.DataTable(
                id='projects-table',
                columns=[
                    {'name': 'No.', 'id': 'No.', 'type': 'numeric'},
                    {'name': 'Project ID', 'id': 'Project ID', 'type': 'text'},
                    {'name': 'Last Modified', 'id': 'Last Modified', 'type': 'datetime'},
                    {'name': 'GitHub', 'id': 'GitHub', 'presentation': 'markdown'},
                    {'name': 'View/Edit', 'id': 'View/Edit', 'type': 'text'},
                    {'name': 'Update', 'id': 'Update', 'type': 'text'},
                    {'name': 'Profile', 'id': 'Profile', 'type': 'text'},
                ],
                data=df.to_dict('records'),
                page_size=PAGE_SIZE,
                page_current=0,
                sort_action='native',
                sort_mode='single',
                filter_action='native',
                filter_options={'case': 'insensitive'},
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '12px',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'fontSize': '16px',
                    'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif'
                },
                style_cell_conditional=[
                    {'if': {'column_id': 'No.'}, 'textAlign': 'center', 'width': '60px', 'fontWeight': '500'}
                ],
                style_header={
                    'backgroundColor': '#f8f9fa',
                    'fontWeight': 'bold',
                    'border': '1px solid #dee2e6',
                    'fontSize': '16px',
                    'height': '50px'
                },
                style_data={'border': '1px solid #dee2e6', 'height': '50px'},
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'},
                    {'if': {'column_id': 'View/Edit'}, 'cursor': 'pointer', 'color': '#007bff', 'fontWeight': '500'},
                    {'if': {'column_id': 'Update'}, 'cursor': 'pointer', 'color': '#28a745', 'fontWeight': '500'},
                    {'if': {'column_id': 'Profile'}, 'cursor': 'pointer', 'color': '#6c757d', 'fontWeight': '500'},
                    {'if': {'column_id': 'Project ID'}, 'fontWeight': '500'}
                ],
                cell_selectable=True,
                markdown_options={'html': True}
            )
        ], className='table-container')
    ], className='projects-container')


#Simplified callback for View/Edit functionality
@callback(
    [Output('url', 'pathname'), Output('admin-alert', 'children'), Output('admin-alert', 'is_open')],
    Input('projects-table', 'active_cell'),
    State('projects-table', 'data'),
    prevent_initial_call=True
)
def handle_view_edit(active_cell, table_data):
    if not active_cell or active_cell['column_id'] != 'View/Edit':
        raise PreventUpdate

    if not current_user.is_authenticated:
        return dash.no_update, "Please log in to access this feature.", True

    if not current_user.is_admin:
        return dash.no_update, "You are not authorized to access this page.", True

    row_data = table_data[active_cell['row']]
    pid = row_data['Project ID']
    return f"{PREFIX}project/{pid}", "", False


# opening profile modal
@callback(
    [
        Output('profile-modal', 'is_open'),
        Output('current-project-store', 'data'),
        Output('modal-project-info', 'children'),
    ],
    [
        Input('projects-table', 'active_cell'),
        Input('close-modal-btn', 'n_clicks')
    ],
    [
        State('projects-table', 'data'),
        State('profile-modal', 'is_open'),
    ],
    prevent_initial_call=True
)
def handle_profile_modal(active_cell, close_clicks, table_data, is_open):
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    print('trigger_id', trigger_id)

    if trigger_id == 'close-modal-btn':
        return False, None, ""

    if trigger_id == 'projects-table' and active_cell and active_cell['column_id'] == 'Profile':
        try:
            row_data = table_data[active_cell['row']]
            pid = row_data['Project ID']

            # Get current credentials
            creds = get_project_credentials(pid)

            project_info = html.Div([
                html.H5(f"Project: {pid}", className='text-primary'),
                html.P(f"Email: {creds['email'] or 'Not set'}", className='text-muted'),
                html.P(f"Password: {'Set' if creds['password'] else 'Not set'}", className='text-muted'),
                html.Hr(),
                html.H5("Update project profile information below", className='text-muted')
            ])

            return True, pid, project_info

        except Exception as e:
            logger.error(f"Error opening profile modal: {str(e)}")
            return False, None, html.P(f"Error: {str(e)}", className='text-danger')

    raise PreventUpdate


# Update the save callback to handle both email and password
@callback(
    [Output('profile-alert', 'children', allow_duplicate=True), Output('profile-alert', 'is_open', allow_duplicate=True)],
    Input('save-profile-btn', 'n_clicks'),
    [State('current-project-store', 'data'), 
     State('new-email-input', 'value'),
     State('new-password-input', 'value'),
     State('confirm-password-input', 'value')],
    prevent_initial_call=True
)
def save_profile(n_clicks, pid, email_value, password_value, confirm_password_value):
    if not n_clicks or not pid:
        raise PreventUpdate

    # Handle password update if provided
    if password_value or confirm_password_value:
        if not password_value or not confirm_password_value:
            return "Please enter both password fields", True
        if password_value != confirm_password_value:
            return "Passwords do not match", True

    # Update credentials
    if update_project_credentials(pid, email=email_value, password=password_value):
        return f"Profile updated successfully for project {pid}", True
    else:
        return "Error updating profile", True


# Password visibility toggle
@callback(
    Output('new-password-input', 'type'),
    Input('toggle-password-btn', 'n_clicks'),
    State('new-password-input', 'type'),
    prevent_initial_call=True
)
def toggle_password_visibility(n_clicks, current_type):
    return 'text' if current_type == 'password' else 'password'


# Update projects callback
@callback(
    [
        Output('projects-table', 'data'),
        Output('admin-alert', 'children', allow_duplicate=True),
        Output('admin-alert', 'is_open', allow_duplicate=True)
    ],
    [
        Input('update-projects-btn', 'n_clicks'),
        Input('projects-table', 'active_cell')
    ],
    prevent_initial_call=True
)
def handle_updates(n_clicks, active_cell):

    if not ctx.triggered:
        raise PreventUpdate

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    print('trigger_id in handle_updates:', trigger_id)
    folder_path = config.get('path', {}).get('work_lmt', '')
    target_dir = os.path.join(folder_path, 'lmtoy_run')

    if trigger_id == 'update-projects-btn':
        os.makedirs(target_dir, exist_ok=True)
        repos = get_github_repos()
        success_count = 0
        for repo in repos:
            if clone_or_pull_repo(repo, target_dir):
                success_count += 1
        df = get_projects_list(folder_path)
        message = f"Successfully updated {success_count} repositories. Total projects: {len(df)}"
        return df.to_dict('records'), message, True

    elif trigger_id == 'projects-table' and active_cell and active_cell['column_id'] == 'Update':
        df = pd.DataFrame(get_projects_list(folder_path))
        if active_cell['row'] < len(df):
            pid = df.iloc[active_cell['row']]['Project ID']
            project_name = f"lmtoy_{pid}"
            project_path = os.path.join(target_dir, project_name)

            try:
                if os.path.exists(project_path):
                    subprocess.run(['git', 'pull'], cwd=project_path, check=True)
                    df = get_projects_list(folder_path)
                    message = f"Successfully updated project {pid}"
                    return df.to_dict('records'), message, True
            except subprocess.CalledProcessError as e:
                message = f"Error updating project {pid}: {str(e)}"
                return dash.no_update, message, True

    raise PreventUpdate


def clone_or_pull_repo(repo_name, target_dir):
    """Clone or pull a repository with improved error handling."""
    repo_url = f"https://github.com/lmtoy/{repo_name}.git"
    repo_path = os.path.join(target_dir, repo_name)

    try:
        if os.path.exists(repo_path):
            result = subprocess.run(
                ['git', 'pull'],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Successfully pulled {repo_name}")
        else:
            result = subprocess.run(
                ['git', 'clone', repo_url, repo_path],
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Successfully cloned {repo_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error with git operation for {repo_name}: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error with {repo_name}: {e}")
        return False


layout = create_layout()
