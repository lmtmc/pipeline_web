# # display all the projects in the github repo
# import os
# from datetime import datetime
# import dash
# from dash import dcc, html, Input, Output, State, ALL, dash_table
# from my_server import app
# from flask_login import logout_user, current_user
#
# from config_loader import load_config
#
# # load the configuration
# try:
#     config = load_config()
# except Exception as e:
#     print(f"Error loading configuration: {e}")
#     config = {}
#
# # Constants
# PREFIX = config.get('path', {}).get('prefix', '')
#
# def get_projects_list(folder_path):
#     """Get list of projects from a folder path."""
#     try:
#         if not os.path.exists(folder_path):
#             return []
#
#         folder_path = os.path.join(folder_path, 'lmtoy_run')
#         # Get all directories in the folder path
#         projects = [d for d in os.listdir(folder_path)
#                    if os.path.isdir(os.path.join(folder_path, d))]
#
#         # Get project details
#         project_details = []
#         for project in projects:
#             if project.startswith('lmtoy'):
#                 pid = project.split('_')[1]
#                 project_path = os.path.join(folder_path, project)
#                 created_time = datetime.fromtimestamp(os.path.getctime(project_path))
#                 modified_time = datetime.fromtimestamp(os.path.getmtime(project_path))
#
#                 project_details.append({
#                     'name': pid,
#                     'path': project_path,
#                     'created_time': created_time,
#                     'modified_time': modified_time
#                 })
#
#         return project_details
#     except Exception as e:
#         print(f"Error getting projects list: {e}")
#         return []
#
# def get_project_details(project_path):
#     """Get detailed information about a specific project."""
#     try:
#         if not os.path.exists(project_path):
#             return None
#
#         return {
#             'name': os.path.basename(project_path),
#             'path': project_path,
#             'modified_time': datetime.fromtimestamp(os.path.getmtime(project_path)),
#             'files': [f for f in os.listdir(project_path)
#                      if os.path.isfile(os.path.join(project_path, f))]
#         }
#     except Exception as e:
#         print(f"Error getting project details: {e}")
#         return None
#
# def create_layout():
#     """Create the admin page layout."""
#     folder_path = config.get('path', {}).get('work_lmt', '')
#     projects = get_projects_list(folder_path)
#
#     # Sort projects by last modified time (newest first)
#     projects.sort(key=lambda x: x['modified_time'], reverse=True)
#
#     # Create table rows
#     table_rows = []
#     for project in projects:
#         github_url = f"https://github.com/lmtoy/lmtoy_{project['name']}"
#         table_rows.append(
#             html.Tr([
#                 html.Td(project['name'], className='project-name'),
#                 html.Td(f"{project['modified_time'].strftime('%Y-%m-%d %H:%M:%S')}", className='project-time'),
#                 html.Td(
#                     html.Div([
#                         html.A(
#                             'GitHub Page',
#                             href=github_url,
#                             target='_blank',
#                             className='github-link'
#                         ),
#                         html.A(
#                             'Edit',
#                             id={'type': 'view-project', 'index': project['name']},
#                             className='view-button',
#                             n_clicks=0
#                         )
#                     ], className='action-buttons')
#                 )
#             ])
#         )
#
#     return html.Div([
#         html.Div(id='admin-alert', style={'display': 'none'}),
#         html.H1('Projects List', className='page-title'),
#         html.Div([
#             html.Table(
#                 [
#                     html.Thead(
#                         html.Tr([
#                             html.Th('Project ID', className='project-id-header'),
#                             html.Th('Last Modified', className='modified-header'),
#                             html.Th('Actions', className='actions-header')
#                         ])
#                     ),
#                     html.Tbody(table_rows)
#                 ],
#                 className='projects-table'
#             )
#         ], className='table-container')
#     ], className='projects-container')
#
# layout = create_layout()
#
# @app.callback(
#     [Output('url', 'pathname'),
#      Output('admin-alert', 'children'),
#      Output('admin-alert', 'style')],
#     Input({'type': 'view-project', 'index': ALL}, 'n_clicks'),
#     prevent_initial_call=True
# )
# def handle_edit_button(n_clicks):
#     if not any(n_clicks):
#         raise dash.exceptions.PreventUpdate
#
#     # Get the index of the clicked button
#     ctx = dash.callback_context
#     if not ctx.triggered:
#         raise dash.exceptions.PreventUpdate
#
#     button_id = ctx.triggered[0]['prop_id'].split('.')[0]
#     pid = eval(button_id)['index']
#
#     # Check if user is authenticated and is admin
#     if not current_user.is_authenticated:
#         return dash.no_update, "Please log in to access this feature.", {'display': 'block', 'color': 'red'}
#
#     if not current_user.is_admin:
#         return dash.no_update, "You are not authorized to access this page. You can login using PID", {'display': 'block', 'color': 'red'}
#
#     # Redirect to the project layout with the selected project
#     return f"{PREFIX}project/{pid}", "", {'display': 'none'}
#
#
# display all the projects in the github repo
import os
from datetime import datetime
import dash
from dash import dcc, html, Input, Output, State, ALL, dash_table, callback # Added callback explicitly
# import dash_bootstrap_components as dbc # Consider adding for styling if needed
from my_server import app # Assuming this is your Flask server instance wrapped by Dash
from flask_login import logout_user, current_user
import pandas as pd
from dash.exceptions import PreventUpdate

from config_loader import load_config

# load the configuration
try:
    config = load_config()
except Exception as e:
    print(f"Error loading configuration: {e}")
    config = {}

# Constants
PREFIX = config.get('path', {}).get('prefix', '')
PAGE_SIZE = 10 # Define how many projects per page

def get_projects_list(folder_path):
    """Get list of projects from a folder path."""
    try:
        if not os.path.exists(folder_path):
            return pd.DataFrame()
        
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
                modified_time = datetime.fromtimestamp(os.path.getmtime(project_path))
                github_url = f"[GitHub](https://github.com/lmtoy/lmtoy_{pid})"
                
                project_details.append({
                    'Project ID': pid,
                    'Last Modified': modified_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'GitHub': github_url,
                    'View/Edit': '📝 View/Edit'
                })
        
        # Convert to DataFrame, sort, and add index
        df = pd.DataFrame(project_details)
        df = df.sort_values('Last Modified', ascending=False)
        # Add index column starting from 1
        df.insert(0, 'No.', range(1, len(df) + 1))
        return df
        
    except Exception as e:
        print(f"Error getting projects list: {e}")
        return pd.DataFrame()

# Removed get_project_details as it wasn't used in the provided layout code snippet

def create_layout():
    """Create the admin page layout."""
    folder_path = config.get('path', {}).get('work_lmt', '')
    df = get_projects_list(folder_path)
    
    return html.Div([
        html.Div(id='admin-alert', style={'display': 'none'}),
        html.H1('Projects List', className='page-title'),
        html.Div([
            dash_table.DataTable(
                id='projects-table',
                columns=[
                    {'name': 'No.', 'id': 'No.', 'type': 'numeric'},  # Added index column
                    {'name': 'Project ID', 'id': 'Project ID', 'type': 'text'},
                    {'name': 'Last Modified', 'id': 'Last Modified', 'type': 'datetime'},
                    {'name': 'GitHub', 'id': 'GitHub', 'presentation': 'markdown'},
                    {'name': 'View/Edit', 'id': 'View/Edit', 'type': 'text'},
                ],
                data=df.to_dict('records'),
                # Enable features
                page_size=10,
                page_current=0,
                sort_action='native',
                sort_mode='single',
                filter_action='native',
                filter_options={'case': 'insensitive'},
                # Style
                style_table={
                    'overflowX': 'auto'
                },
                style_cell={
                    'textAlign': 'left',
                    'padding': '12px',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'fontSize': '16px',
                    'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif'
                },
                # Specific styling for the index column
                style_cell_conditional=[
                    {
                        'if': {'column_id': 'No.'},
                        'textAlign': 'center',
                        'width': '60px',
                        'fontWeight': '500'
                    }
                ],
                style_header={
                    'backgroundColor': '#f8f9fa',
                    'fontWeight': 'bold',
                    'border': '1px solid #dee2e6',
                    'fontSize': '16px',
                    'height': '50px'
                },
                style_data={
                    'border': '1px solid #dee2e6',
                    'height': '50px'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#f8f9fa'
                    },
                    {
                        'if': {'column_id': 'View/Edit'},
                        'cursor': 'pointer',
                        'color': '#007bff',
                        'textDecoration': 'none',
                        'fontWeight': '500'
                    },
                    {
                        'if': {'column_id': 'Project ID'},
                        'fontWeight': '500'
                    }
                ],
                # Enable cell clicking
                cell_selectable=True,
                markdown_options={'html': True}
            )
        ], className='table-container')
    ], className='projects-container')

layout = create_layout()

# Add callback to handle clicking on View/Edit
@callback(
    [
        Output('url', 'pathname'),
        Output('admin-alert', 'children'),
        Output('admin-alert', 'style')
    ],
    Input('projects-table', 'active_cell'),
    State('projects-table', 'data'),
    prevent_initial_call=True
)
def handle_cell_click(active_cell, table_data):
    if not active_cell:
        raise PreventUpdate
    
    # Only handle clicks in the View/Edit column
    if active_cell['column_id'] != 'View/Edit':
        raise PreventUpdate
    
    # Get the project ID from the clicked row
    row_data = table_data[active_cell['row']]
    pid = row_data['Project ID']
    
    # Check if user is authenticated and is admin
    if not current_user.is_authenticated:
        return dash.no_update, "Please log in to access this feature.", {
            'display': 'block',
            'color': 'red',
            'padding': '10px',
            'marginBottom': '10px',
            'backgroundColor': '#ffe6e6',
            'borderRadius': '4px'
        }
    
    if not current_user.is_admin:
        return dash.no_update, "You are not authorized to access this page.", {
            'display': 'block',
            'color': 'red',
            'padding': '10px',
            'marginBottom': '10px',
            'backgroundColor': '#ffe6e6',
            'borderRadius': '4px'
        }
    
    # Redirect to the project layout with the selected project
    return f"{PREFIX}project/{pid}", "", {'display': 'none'}
