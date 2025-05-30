import os
from datetime import datetime
import dash
from dash import dcc, html, Input, Output, State, ALL, dash_table, callback, ctx, no_update, MATCH
import dash_bootstrap_components as dbc
from my_server import app
from flask_login import current_user
import pandas as pd
from dash.exceptions import PreventUpdate
import subprocess
import json

import logging
from db.users_mgt import get_project_credentials, update_project_credentials
from utils.ui_utils import get_project_id_from_cell, get_table_data_for_year
from utils.repo_utils import get_all_repos, get_repo_status, update_single_repo, pull_lmtoy_run

from config_loader import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('admin_page.log')
    ]
)
logger = logging.getLogger(__name__)

# load the configuration
try:
    config = load_config()
except Exception as e:
    logger.error(f"Error loading configuration: {e}")
    config = {}

# Constants
PREFIX = config.get('path', {}).get('prefix', '')
PAGE_SIZE = 10
GITHUB_API_URL = config.get('github', {}).get('api_url', 'https://api.github.com/orgs/lmtoy/repos')
REPO_PREFIX = config.get('github', {}).get('repo_prefix', 'lmtoy_')
WORK_DIR = config.get('path', {}).get('work_lmt', '')
LMTOY_RUN_DIR = os.path.join(WORK_DIR, 'lmtoy_run')

DB_PATH = "instance/users.db"

def create_layout():
    
    # Use combined repository data
    repos_by_year = get_all_repos()
    
    # Create tabs for each year
    tabs = []
    for year, repos in sorted(repos_by_year.items(), reverse=True):
        if not repos:  # Skip years with no repositories
            continue
            
        # Create data table for this year's repositories
        df = pd.DataFrame([
            {
                'No.': i + 1,
                'Project ID': repo.replace('lmtoy_', ''),
                'Last Modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'GitHub': f'<a href="https://github.com/lmtoy/{repo}" target="_blank">View on GitHub</a>',
                'View/Edit': 'View/Edit',
                'Profile': 'Profile Set' if get_project_credentials(repo.replace('lmtoy_', ''))['email'] and get_project_credentials(repo.replace('lmtoy_', ''))['password'] else 'Profile',
                'Status': get_repo_status(repo)
            }
            for i, repo in enumerate(repos)
        ])
        
        # Create tab label as a string
        tab_label = f"{year} ({len(repos)} projects)"
        
        tab = dbc.Tab(
            children=[
                dash_table.DataTable(
                    id={'type': 'projects-table', 'year': year},
                    columns=[
                        {'name': 'No.', 'id': 'No.', 'type': 'numeric'},
                        {'name': 'Project ID', 'id': 'Project ID', 'type': 'text'},
                        {'name': 'Last Modified', 'id': 'Last Modified', 'type': 'datetime'},
                        {'name': 'GitHub', 'id': 'GitHub', 'presentation': 'markdown'},
                        {'name': 'View/Edit', 'id': 'View/Edit', 'type': 'text'},
                        {'name': 'Profile', 'id': 'Profile', 'type': 'text'},
                        {'name': 'Status', 'id': 'Status', 'type': 'text'}
                    ],
                    data=df.to_dict('records'),
                    sort_action='native',
                    sort_mode='single',
                    filter_action='native',
                    filter_options={'case': 'insensitive'},
                    style_table={
                        'overflowX': 'auto',
                        'borderRadius': '8px',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                        'backgroundColor': 'white'
                    },
                    style_cell={
                        'textAlign': 'center',
                        'padding': '12px 16px',
                        'whiteSpace': 'normal',
                        'height': 'auto',
                        'fontSize': '14px',
                        'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif',
                        'border': '1px solid #e9ecef'
                    },
                    style_cell_conditional=[
                        {'if': {'column_id': 'No.'}, 
                         'width': '60px', 
                         'fontWeight': '500',
                         'backgroundColor': '#f8f9fa'},
                        {'if': {'column_id': 'Project ID'}, 
                         'width': '120px',
                         'fontWeight': '600',
                         'color': '#2c3e50'},
                        {'if': {'column_id': 'Last Modified'}, 
                         'width': '150px'},
                        {'if': {'column_id': 'GitHub'}, 
                         'width': '120px'},
                        {'if': {'column_id': 'View/Edit'}, 
                         'width': '100px',
                         'cursor': 'pointer',
                         'color': '#007bff',
                         'fontWeight': '500',
                         },
                        {'if': {'column_id': 'Profile'}, 
                         'width': '100px',
                         'cursor': 'pointer',
                         'color': '#6c757d',
                         'fontWeight': '500',
                         },
                        {'if': {'column_id': 'Profile', 'filter_query': '{Profile} = "Profile Set"'}, 
                         'color': '#28a745',
                         'fontWeight': '600'},
                        {'if': {'column_id': 'Status'}, 
                         'width': '120px',
                         'fontWeight': '500'}
                    ],
                    style_header={
                        'backgroundColor': '#f8f9fa',
                        'fontWeight': 'bold',
                        'border': '1px solid #dee2e6',
                        'fontSize': '14px',
                        'height': '50px',
                        'textTransform': 'uppercase',
                        'letterSpacing': '0.5px',
                        'color': '#495057',
                        'textAlign': 'center'
                    },
                    style_data={
                        'border': '1px solid #e9ecef',
                        'height': '50px',
                        'verticalAlign': 'middle'
                    },
                    style_data_conditional=[
                        {'if': {'row_index': 'odd'}, 
                         'backgroundColor': '#f8f9fa'},
                        {'if': {'column_id': 'Status', 'filter_query': '{Status} = "Up to date"'}, 
                         'color': '#28a745',
                         'fontWeight': '500'},
                        {'if': {'column_id': 'Status', 'filter_query': '{Status} = "Needs update"'}, 
                         'color': '#dc3545',
                         'fontWeight': '500',
                         'cursor': 'pointer'},
                        {'if': {'column_id': 'Status', 'filter_query': '{Status} = "Not tracked"'}, 
                         'color': '#6c757d',
                         'fontWeight': '500'}
                    ],
                    cell_selectable=True,
                    markdown_options={'html': True}
                )
            ],
            label=tab_label,
            label_style={
                'fontWeight': '600',
                'fontSize': '16px',
                'color': '#2c3e50',
                'padding': '8px 16px',
                'borderRadius': '4px',
                'transition': 'all 0.2s ease-in-out'
            }
        )
        tabs.append(tab)

    # If no repositories exist, show a message
    if not tabs:
        return html.Div([
            dbc.Alert(
                "No repositories found. Please ensure repositories are properly cloned.",
                color="warning",
                className="mt-3"
            )
        ])

    return html.Div([
        # Store for current project ID and modal state
        dcc.Store(id='current-project-store'),
        dbc.Alert(id='admin-alert',
                  is_open=False,
                  dismissable=True,
                  duration=4500),
        
        # Profile Modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Project Profile")),
            dbc.ModalBody(id='modal-project-info'),
            dbc.ModalFooter([
                dbc.Button("Close", id="close-modal-btn", className="ms-auto", n_clicks=0)
            ])
        ], id="profile-modal", is_open=False),
        
        html.Div([
            html.H5('Projects List'),
            dbc.Button('Update Repositories', 
                      id='update-repos-btn',
                      color='primary',
                      className='ms-auto',
                      style={'fontWeight': '500'})
        ], style={'display': 'flex', 
                 'alignItems': 'center',
                 'marginBottom': '20px',
                 'justifyContent': 'space-between'}),

        html.Div([
            dbc.Tabs(tabs, 
                    id='year-tabs',
                    style={
                        'backgroundColor': 'white',
                        'borderRadius': '8px',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                        'padding': '16px'
                    },
                    className='custom-tabs'
                )
        ], className='table-container')
    ], className='projects-container', style={'padding': '24px', 'backgroundColor': '#f8f9fa'})

# Update profile callback to handle PROFILE cell clicks
@callback(
    [Output('profile-modal', 'is_open'),
     Output('current-project-store', 'data'),
     Output('modal-project-info', 'children')],
    [Input({'type': 'projects-table', 'year': ALL}, 'active_cell'),
     Input('close-modal-btn', 'n_clicks')],
    [State({'type': 'projects-table', 'year': ALL}, 'data'),
     State('profile-modal', 'is_open')],
    prevent_initial_call=True
)
def handle_profile_click(active_cells, close_clicks, tables_data, is_open):
    """Handle Profile cell clicks."""
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Handle close button click
    if trigger_id == 'close-modal-btn':
        return False, None, ""
    
    try:
        row_data = get_table_data_for_year(trigger_id, active_cells, tables_data, 'Profile')
        pid = row_data['Project ID']
        
        # Get current credentials
        creds = get_project_credentials(pid)
        
        project_info = html.Div([
            html.H5(f"Project: {pid}", className='text-primary'),
            html.P(f"Email: {creds['email'] or 'Not set'}", className='text-muted'),
            html.P(f"Password: {'Set' if creds['password'] else 'Not set'}", className='text-muted'),
            html.P(f"Edit URL: {PREFIX}project/{pid}", className='text-info'),  # Show edit URL
            html.Hr(),
            html.H5("Update project profile information below", className='text-muted'),
            
            # Form container
            dbc.Form([
                # Email input
                dbc.Row([
                    dbc.Label("Email", html_for="new-email-input", width=3),
                    dbc.Col([
                        dbc.Input(
                            type="text",
                            id="new-email-input",
                            placeholder="Enter new email",
                            value=creds.get('email', ''),
                            className="mb-3"
                        ),
                    ], width=9)
                ], className="mb-3"),
                
                # Password input
                dbc.Row([
                    dbc.Label("New Password", html_for="new-password-input", width=3),
                    dbc.Col([
                        dbc.InputGroup([
                            dbc.Input(
                                type="text",
                                id="new-password-input",
                                placeholder="Enter new password",
                                className="mb-3"
                            ),
                            dbc.Button(
                                html.I(className="fas fa-eye"),
                                id="toggle-password-btn",
                                color="secondary",
                                className="mb-3"
                            ),
                        ]),
                    ], width=9)
                ], className="mb-3"),
                
                # Confirm password input
                dbc.Row([
                    dbc.Label("Confirm Password", html_for="confirm-password-input", width=3),
                    dbc.Col([
                        dbc.InputGroup([
                            dbc.Input(
                                type="text",
                                id="confirm-password-input",
                                placeholder="Confirm new password",
                                className="mb-3"
                            ),
                            dbc.Button(
                                html.I(className="fas fa-eye"),
                                id="toggle-confirm-password-btn",
                                color="secondary",
                                className="mb-3"
                            ),
                        ]),
                    ], width=9)
                ], className="mb-3"),
                
                # Save button
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            "Save Changes",
                            id="save-profile-btn",
                            color="primary",
                            className="mt-3"
                        ),
                    ], width={"offset": 3, "size": 9})
                ]),
                
                # Alert for feedback
                dbc.Row([
                    dbc.Col([
                        dbc.Alert(
                            id="profile-alert",
                            is_open=False,
                            duration=4000,
                            className="mt-3"
                        ),
                    ], width={"offset": 3, "size": 9})
                ])
            ])
        ])

        return True, pid, project_info
        
    except PreventUpdate:
        raise
    except Exception as e:
        logger.error(f"Error handling profile click: {str(e)}")
        return False, None, html.P(f"Error: {str(e)}", className='text-danger')

# Add callback for password visibility toggle
@callback(
    Output('new-password-input', 'type'),
    Input('toggle-password-btn', 'n_clicks'),
    State('new-password-input', 'type'),
    prevent_initial_call=True
)
def toggle_password_visibility(n_clicks, current_type):
    if n_clicks is None:
        raise PreventUpdate
    return 'text' if current_type == 'password' else 'password'

# Add callback for confirm password visibility toggle
@callback(
    Output('confirm-password-input', 'type'),
    Input('toggle-confirm-password-btn', 'n_clicks'),
    State('confirm-password-input', 'type'),
    prevent_initial_call=True
)
def toggle_confirm_password_visibility(n_clicks, current_type):
    if n_clicks is None:
        raise PreventUpdate
    return 'text' if current_type == 'password' else 'password'

# Add callback for saving profile changes
@callback(
    [Output('profile-alert', 'children'),
     Output('profile-alert', 'is_open'),
     Output('profile-alert', 'color')],
    Input('save-profile-btn', 'n_clicks'),
    [State('current-project-store', 'data'),
     State('new-email-input', 'value'),
     State('new-password-input', 'value'),
     State('confirm-password-input', 'value')],
    prevent_initial_call=True
)
def save_profile_changes(n_clicks, pid, email, password, confirm_password):
    if not n_clicks or not pid:
        raise PreventUpdate
        
    try:
        # Update credentials
        success, message = update_project_credentials(
            pid,
            email=email,
            password=password,
            confirm_password=confirm_password
        )
        
        if success:
            return message, True, "success"
        else:
            return message, True, "danger"
            
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        return f"Error updating profile: {str(e)}", True, "danger"

def update_single_repo(repo_name, work_dir):
    """Update a single repository."""
    try:
        repo_path = os.path.join(work_dir, repo_name)
        if not os.path.exists(repo_path):
            return False, f"Repository {repo_name} not found"
            
        subprocess.run(['git', 'pull'], cwd=repo_path, check=True)
        return True, f"Repository {repo_name} updated successfully"
    except subprocess.CalledProcessError as e:
        return False, f"Error updating repository {repo_name}: {str(e)}"
    except Exception as e:
        return False, f"Error updating repository {repo_name}: {str(e)}"

# Update the callback to handle both status updates and repository updates
@callback(
    [Output({'type': 'projects-table', 'year': ALL}, 'data'),
     Output('admin-alert', 'children', allow_duplicate=True),
     Output('admin-alert', 'is_open', allow_duplicate=True)],
    [Input({'type': 'projects-table', 'year': ALL}, 'active_cell'),
     Input('update-repos-btn', 'n_clicks')],
    [State({'type': 'projects-table', 'year': ALL}, 'data')],
    prevent_initial_call=True
)
def handle_updates(active_cells, update_clicks, tables_data):
    """Handle both status updates and repository updates."""
    if not ctx.triggered:
        raise PreventUpdate
        
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Handle repository update button click
    if trigger_id == 'update-repos-btn':
        try:
            # First pull latest changes from lmtoy_run
            success, message = pull_lmtoy_run()
            if not success:
                return tables_data, message, True
                
            # Get fresh repository data
            repos_by_year = get_all_repos()
            
            # Create updated data for each table
            updated_tables = []
            for year, repos in sorted(repos_by_year.items(), reverse=True):
                df = pd.DataFrame([
                    {
                        'No.': i + 1,
                        'Project ID': repo.replace('lmtoy_', ''),
                        'Last Modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'GitHub': f'<a href="https://github.com/lmtoy/{repo}" target="_blank">View on GitHub</a>',
                        'View/Edit': 'View/Edit',
                        'Profile': 'Profile Set' if get_project_credentials(repo.replace('lmtoy_', ''))['email'] and get_project_credentials(repo.replace('lmtoy_', ''))['password'] else 'Profile',
                        'Status': get_repo_status(repo)
                    }
                    for i, repo in enumerate(repos)
                ])
                updated_tables.append(df.to_dict('records'))
                
            return updated_tables, "Repositories updated successfully", True
        except Exception as e:
            logger.error(f"Error updating repositories: {str(e)}")
            return tables_data, f"Error updating repositories: {str(e)}", True
    
    # Handle status cell click
    try:
        trigger_data = json.loads(trigger_id)
        year = trigger_data['year']
        
        # Find the active cell in the correct table
        active_cell = next((cell for cell in active_cells if cell is not None), None)
        if not active_cell or active_cell['column_id'] != 'Status':
            raise PreventUpdate
            
        # Get the table data for the active year
        repos_by_year = get_all_repos()
        sorted_years = sorted(repos_by_year.keys(), reverse=True)  # Same ordering as in create_layout
        year_index = sorted_years.index(year)
        
        # Get the corresponding table data
        table_data = tables_data[year_index] if year_index < len(tables_data) else []
        if not table_data:
            raise PreventUpdate
            
        # Get the row data directly from the table data
        if 0 <= active_cell['row'] < len(table_data):
            row_data = table_data[active_cell['row']]
            project_id = row_data['Project ID']
            repo_name = f"lmtoy_{project_id}"  # Construct repo name from Project ID
            status = row_data['Status']
            
            if status == "Needs update":
                # Update the repository
                success, message = update_single_repo(repo_name, LMTOY_RUN_DIR)
                if success:
                    # Update the status in the table
                    row_data['Status'] = get_repo_status(repo_name)
                    return tables_data, message, True
                else:
                    return tables_data, message, True
    except json.JSONDecodeError:
        raise PreventUpdate
            
    raise PreventUpdate

# Add callback for View/Edit column clicks
@callback(
    Output('url', 'pathname'),
    [Input({'type': 'projects-table', 'year': ALL}, 'active_cell')],
    [State({'type': 'projects-table', 'year': ALL}, 'data')],
    prevent_initial_call=True
)
def handle_view_edit(active_cells, tables_data):
    """Handle View/Edit cell clicks."""
    if not ctx.triggered:
        raise PreventUpdate
        
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        row_data = get_table_data_for_year(trigger_id, active_cells, tables_data, 'View/Edit')
        pid = row_data['Project ID']
        return f'/project/{pid}'
            
    except PreventUpdate:
        raise
    except Exception as e:
        logger.error(f"Error handling view/edit click: {str(e)}")
        raise PreventUpdate

layout = create_layout()
