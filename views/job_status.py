import dash_bootstrap_components as dbc
from dash import html, Input, Output, State, dcc, callback_context
from dash.exceptions import PreventUpdate
from flask_login import current_user
import logging
from utils import project_function as pf
import os

# Setup logging
logger = logging.getLogger(__name__)

def create_job_status_layout():
    """Create the job status layout with comprehensive job management features."""
    return dbc.Container(
        [
            # Header
            dbc.Row([
                dbc.Col([
                    html.H2("Job Status Management", className="text-center mb-4"),
                    html.Hr()
                ])
            ]),
            
            # Navigation back to project
            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        [html.I(className="fas fa-arrow-left me-2"), "Back to Project"],
                        id="back-to-project-btn",
                        color="secondary",
                        className="mb-3"
                    )
                ])
            ]),
            
            # Job Status Overview
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5("Current Job Status", className="mb-0"),
                            html.Small("Real-time SLURM job monitoring", className="text-muted")
                        ]),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button(
                                        [html.I(className="fas fa-sync-alt me-2"), "Refresh Status"],
                                        id="refresh-status-btn",
                                        color="primary",
                                        className="w-100"
                                    )
                                ], width=3),
                                dbc.Col([
                                    dbc.Button(
                                        [html.I(className="fas fa-clock me-2"), "Auto Refresh"],
                                        id="auto-refresh-btn",
                                        color="info",
                                        outline=True,
                                        className="w-100"
                                    )
                                ], width=3),
                                dbc.Col([
                                    dbc.Button(
                                        [html.I(className="fas fa-download me-2"), "Export Data"],
                                        id="export-jobs-btn",
                                        color="success",
                                        className="w-100"
                                    )
                                ], width=3),
                                dbc.Col([
                                    dbc.Button(
                                        [html.I(className="fas fa-chart-bar me-2"), "Job Analytics"],
                                        id="job-analytics-btn",
                                        color="warning",
                                        className="w-100"
                                    )
                                ], width=3)
                            ], className="mb-3"),
                            
                            # Job Status Display
                            html.Div(id="job-status-display", className="mt-3")
                        ])
                    ])
                ])
            ], className="mb-4"),
            
            # Job Management Section
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5("Job Management", className="mb-0"),
                            html.Small("Cancel jobs and manage resources", className="text-muted")
                        ]),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Job ID", html_for="job-id-input"),
                                    dbc.Input(
                                        id="job-id-input",
                                        placeholder="Enter Job ID to cancel",
                                        type="text",
                                        className="mb-2"
                                    ),
                                    dbc.Button(
                                        [html.I(className="fas fa-stop-circle me-2"), "Cancel Job"],
                                        id="cancel-job-btn",
                                        color="danger",
                                        className="w-100"
                                    )
                                ], width=6),
                                dbc.Col([
                                    dbc.Label("User ID", html_for="user-id-input"),
                                    dbc.Input(
                                        id="user-id-input",
                                        placeholder="Enter User ID",
                                        type="text",
                                        value="lmthelpdesk_umass_edu",
                                        className="mb-2"
                                    ),
                                    dbc.Button(
                                        [html.I(className="fas fa-search me-2"), "Search User Jobs"],
                                        id="search-user-jobs-btn",
                                        color="primary",
                                        outline=True,
                                        className="w-100"
                                    )
                                ], width=6)
                            ])
                        ])
                    ])
                ])
            ], className="mb-4"),
            
            # Job History Section
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5("Job History", className="mb-0"),
                            html.Small("View completed and failed jobs", className="text-muted")
                        ]),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Date Range", html_for="date-range-picker"),
                                    dcc.DatePickerRange(
                                        id="date-range-picker",
                                        className="mb-2"
                                    )
                                ], width=4),
                                dbc.Col([
                                    dbc.Label("Job Status", html_for="status-filter"),
                                    dbc.Select(
                                        id="status-filter",
                                        options=[
                                            {"label": "All Jobs", "value": "all"},
                                            {"label": "Completed", "value": "completed"},
                                            {"label": "Failed", "value": "failed"},
                                            {"label": "Cancelled", "value": "cancelled"}
                                        ],
                                        value="all",
                                        className="mb-2"
                                    )
                                ], width=4),
                                dbc.Col([
                                    dbc.Label("", html_for="load-history-btn"),
                                    dbc.Button(
                                        [html.I(className="fas fa-history me-2"), "Load History"],
                                        id="load-history-btn",
                                        color="info",
                                        className="w-100"
                                    )
                                ], width=4)
                            ]),
                            html.Div(id="job-history-display", className="mt-3")
                        ])
                    ])
                ])
            ]),
            
            # Confirmation Dialogs
            dcc.ConfirmDialog(
                id='cancel-job-confirm-dialog',
                message='Are you sure you want to cancel this job? This action cannot be undone.',
                submit_n_clicks=0
            ),
            
            dcc.ConfirmDialog(
                id='export-confirm-dialog',
                message='Export job data to CSV file?',
                submit_n_clicks=0
            ),
            
            # Loading Spinner
            dbc.Spinner(
                html.Div(id="loading-output"),
                color="primary"
            ),
            
            # Alert Messages
            html.Div(id="alert-container"),
            
            # Hidden div for navigation
            dcc.Location(id='job-status-location', refresh=True),
            
            # Store for job data
            dcc.Store(id='job-data-store', data={}),
            
            # Store for project data (inherited from main app)
            dcc.Store(id='data-store', data={}),
            
            # Interval for auto-refresh
            dcc.Interval(
                id='auto-refresh-interval',
                interval=30000,  # 30 seconds
                n_intervals=0,
                disabled=True
            )
        ],
        fluid=True,
        className="py-4"
    )

# Create the layout
layout = create_job_status_layout()

# Callback to handle back navigation
def register_callbacks(app):
    """Register all callbacks for the job status page."""
    
    @app.callback(
        Output('job-status-location', 'href'),
        Input('back-to-project-btn', 'n_clicks'),
        State('data-store', 'data'),
        prevent_initial_call=True
    )
    def navigate_back(n_clicks, data):
        if n_clicks:
            # Navigate back to the project page with the current PID
            pid = data.get('pid') if data else None
            if pid:
                return f'/pipeline_web/project/{pid}'
            else:
                return '/pipeline_web/project'
        raise PreventUpdate
    
    @app.callback(
        Output('job-status-display', 'children'),
        [Input('refresh-status-btn', 'n_clicks'),
         Input('auto-refresh-interval', 'n_intervals')],
        [State('job-data-store', 'data')],
        prevent_initial_call=True
    )
    def update_job_status(refresh_clicks, interval_clicks, job_data):
        if not callback_context.triggered:
            raise PreventUpdate
            
        try:
            # Get current user's jobs or all jobs if admin
            if current_user.is_authenticated:
                if current_user.is_admin:
                    # Admin can see all jobs
                    status, success = pf.check_slurm_job_status("all")
                else:
                    # For regular users, show all jobs since we can't determine the actual username
                    # The current_user.username appears to be set to project ID instead of username
                    status, success = pf.check_slurm_job_status("all")
            else:
                return dbc.Alert("Please log in to view job status.", color="warning")
            
            if success and status:
                if isinstance(status, list) and status:
                    # Create a comprehensive job status table
                    headers = status[0].keys()
                    
                    # Create table rows with status-based styling
                    rows = []
                    for job in status:
                        # Determine row color based on job status
                        status_value = job.get('STATE', '').lower()
                        if 'running' in status_value:
                            row_class = "table-primary"
                        elif 'completed' in status_value:
                            row_class = "table-success"
                        elif 'failed' in status_value or 'cancelled' in status_value:
                            row_class = "table-danger"
                        elif 'pending' in status_value:
                            row_class = "table-warning"
                        else:
                            row_class = ""
                        
                        row = html.Tr(
                            [html.Td(job[header]) for header in headers],
                            className=row_class
                        )
                        rows.append(row)
                    
                    return html.Div([
                        dbc.Table(
                            [
                                html.Thead(html.Tr([html.Th(header) for header in headers])),
                                html.Tbody(rows)
                            ],
                            bordered=True,
                            hover=True,
                            responsive=True,
                            striped=True,
                            className="mt-3"
                        ),
                        html.Div([
                            html.Small(f"Last updated: {pf.get_current_timestamp()}", className="text-muted")
                        ], className="mt-2 text-end")
                    ])
                else:
                    return dbc.Alert("No active jobs found.", color="info")
            else:
                return dbc.Alert(f"Error retrieving job status: {status}", color="danger")
                
        except Exception as e:
            logger.error(f"Error updating job status: {str(e)}")
            return dbc.Alert(f"Error updating job status: {str(e)}", color="danger")
    
    @app.callback(
        Output('cancel-job-confirm-dialog', 'displayed'),
        Input('cancel-job-btn', 'n_clicks'),
        State('job-id-input', 'value'),
        prevent_initial_call=True
    )
    def show_cancel_confirmation(n_clicks, job_id):
        if n_clicks and job_id:
            return True
        return False
    
    @app.callback(
        [Output('alert-container', 'children'),
         Output('job-id-input', 'value')],
        Input('cancel-job-confirm-dialog', 'submit_n_clicks'),
        State('job-id-input', 'value'),
        prevent_initial_call=True
    )
    def cancel_job(n_clicks, job_id):
        if n_clicks and job_id:
            try:
                success, message = pf.cancel_slurm_job(job_id)
                if success:
                    alert = dbc.Alert(
                        f"Job {job_id} has been successfully cancelled.",
                        color="success",
                        dismissable=True
                    )
                else:
                    alert = dbc.Alert(
                        f"Failed to cancel job {job_id}: {message}",
                        color="danger",
                        dismissable=True
                    )
                return alert, ""  # Clear the input field
            except Exception as e:
                logger.error(f"Error cancelling job: {str(e)}")
                return dbc.Alert(f"Error cancelling job: {str(e)}", color="danger"), job_id
        raise PreventUpdate
    
    @app.callback(
        Output('auto-refresh-interval', 'disabled'),
        Input('auto-refresh-btn', 'n_clicks'),
        State('auto-refresh-interval', 'disabled'),
        prevent_initial_call=True
    )
    def toggle_auto_refresh(n_clicks, currently_disabled):
        if n_clicks:
            return not currently_disabled
        raise PreventUpdate
    
    @app.callback(
        Output('alert-container', 'children', allow_duplicate=True),
        Input('search-user-jobs-btn', 'n_clicks'),
        State('user-id-input', 'value'),
        prevent_initial_call=True
    )
    def search_user_jobs(n_clicks, user_id):
        if n_clicks and user_id:
            try:
                status, success = pf.check_slurm_job_status(user_id)
                if success:
                    if isinstance(status, list) and status:
                        return dbc.Alert(
                            f"Found {len(status)} jobs for user {user_id}",
                            color="success",
                            dismissable=True
                        )
                    else:
                        return dbc.Alert(
                            f"No jobs found for user {user_id}",
                            color="info",
                            dismissable=True
                        )
                else:
                    return dbc.Alert(
                        f"Error searching jobs for user {user_id}: {status}",
                        color="danger",
                        dismissable=True
                    )
            except Exception as e:
                logger.error(f"Error searching user jobs: {str(e)}")
                return dbc.Alert(f"Error searching user jobs: {str(e)}", color="danger")
        raise PreventUpdate
