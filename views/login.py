# login.py
# This file handles user login functionality for the Dash application.
# It includes the login form, password visibility toggle, and login status management.
# It also manages user authentication, session handling, and integrates with the Flask-Login extension.

from flask import request, session
from dash import dcc, html, Input, Output, State, no_update
import os
import dash_bootstrap_components as dbc
from my_server import app, User
from flask_login import login_user, current_user
from werkzeug.security import check_password_hash
from utils import project_function as pf, repo_utils as ru
from config_loader import load_config
from utils.logger import log_login_attempt, log_session_start, logger


# Load configuration
try:
    config = load_config()
except Exception as e:
    print(f"Error loading configuration: {e}")
    config = {}

prefix = config['path']['prefix']
default_work_lmt = config['path']['work_lmt']
default_session_prefix = os.path.join(default_work_lmt, 'lmtoy_run/lmtoy_')

# Ensure paths exist
pf.ensure_path_exists(default_work_lmt)
pf.ensure_path_exists(os.path.join(default_work_lmt, 'lmtoy_run'))

layout = html.Div([
    dcc.Location(id='url_login'),
    dbc.Container([
        html.Div([
            # Logo and Title
            html.Div([
                html.Img(
                    src='assets/lmt_img.jpg',
                    style={'width': '100%', 'height': 'auto'},
                    className='mb-4'),
            ], className='text-center'),
            
            # Login Form
            dbc.Form([
                # PID Input
                dbc.Row([
                    dbc.Col([
                        dbc.Label('PID:', html_for='pid'),
                        dbc.Input(
                            id='pid',
                            type='text',
                            placeholder='Enter your PID',
                            className='mb-3',
                            autoComplete='username'
                        ),
                    ])
                ]),
                
                # Password Input with Toggle
                dbc.Row([
                    dbc.Col([
                        dbc.Label('Password:', html_for='pwd-box'),
                        dbc.InputGroup([
                            dbc.Input(
                                id='pwd-box',
                                type='password',
                                placeholder='Enter your password',
                                autoComplete='current-password'
                            ),
                         dbc.Button(html.I(className='fas fa-eye', id='eye-icon'),
                                    id='toggle-password',
                                    color='secondary',
                                    outline=True,
                                    style={'border-left': 'none', },
                                    className='border-start-0'
                                ),
                    ], className='mb-3 password-input-group'),
                    ])
                ]),
                
                # Remember Me Checkbox
                dbc.Row([
                    dbc.Col([
                        dbc.Checkbox(
                            id='remember-me',
                            label='Remember me'
                        ),
                    ])
                ], className='mb-3'),

                dbc.Alert(id='output-state',
                          is_open=False,
                          duration=5000,
                          dismissable=True,
                          className='mb-3'),
                # Login Button
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            'Login',
                            id='login-button',
                            type='submit',
                            className='w-100 mb-3',
                            color='primary'
                        ),
                    ])
                ]),
                
                # Forgot Password Link
                dbc.Row([
                    dbc.Col([
                        html.A(
                            'Forgot Password?',
                            href=f'{prefix}forgot-password',
                            className='text-decoration-none')
                    ], className='text-center')
                ]),
            ], className='p-4 bg-light rounded shadow-sm')
        ], )
    ], style={'maxWidth': '500px', 'margin': 'auto', 'padding': '2rem 1rem'})
], id='login-page-container')

# Callback to toggle password visibility
@app.callback(
    [
        Output('pwd-box', 'type'),
        Output('eye-icon', 'className')
    ],
    Input('toggle-password', 'n_clicks'),
    State('pwd-box', 'type'),
    prevent_initial_call=True
)
def toggle_password_visibility(n_clicks, current_type):
    if current_type == 'password':
        return 'text', 'fas fa-eye-slash'
    else:
        return 'password', 'fas fa-eye'

# Login status callback
@app.callback(
    [Output('output-state', 'children'),
     Output('output-state', 'is_open'),
     Output('output-state', 'color'),
     Output('url_login', 'pathname'),
     Output('pwd-box', 'value')],
    Input('login-button', 'n_clicks'),
    [State('pwd-box', 'value'),
     State('pid', 'value'),
     State('remember-me', 'value')],
    prevent_initial_call=True
)
def login_status(n_clicks, password, pid, remember_me):
    """Handle login process and status messages."""
    if not n_clicks:
        return no_update, no_update, no_update, no_update, no_update

    # Validate inputs
    if not password or not pid:
        return (
            'Please enter both PID and password.',
            True,
            'warning',
            no_update,
            no_update
        )

    # Check if already authenticated
    if current_user.is_authenticated:
        return (
            'You are already logged in.',
            True,
            'info',
            no_update,
            no_update
        )

    try:
        # Fetch user and validate password
        user = User.query.filter_by(username=pid).first()

        if not user or not check_password_hash(user.password, password):
            # Log failed login attempt
            log_login_attempt(
                username=pid,
                success=False,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            return (
                'Invalid credentials. Please try again.',
                True,
                'danger',
                no_update,
                ''  # Clear password field
            )

        # Login successful
        login_user(user, remember=bool(remember_me))

        # Log successful login
        log_login_attempt(
            username=pid,
            success=True,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )

        # Log session start
        session_id = session.get('_id', 'unknown')
        log_session_start(
            username=pid,
            session_id=session_id,
            ip_address=request.remote_addr
        )

        # Handle admin login
        if user.username == 'admin':
            return (
                'Login as Admin successful!',
                True,
                'success',
                f'{prefix}admin',
                ''
            )

        # Handle regular user login with git pull
        default_pid_path = f'{default_session_prefix}{user.username}'

        try:
            # success, message = pf.execute_git_pull(default_pid_path)
            repo_name = f'lmtoy_{user.username}'
            success, message = ru.update_single_repo(repo_name, default_work_lmt)

            if success:
                return (
                    f'Login as {user.username} successful! {message}',
                    True,
                    'success',
                    f'{prefix}project/{pid}',
                    ''
                )
            else:
                logger.error(f"Git pull failed for user {user.username}: {message}")
                return (
                    f'Login successful, but git pull failed: {message}',
                    True,
                    'warning',
                    f'{prefix}project/{pid}',
                    ''
                )

        except Exception as git_error:
            logger.error(f"Git pull error for user {user.username}: {str(git_error)}")
            return (
                'Login successful, but git pull encountered an error.',
                True,
                'warning',
                f'{prefix}project/{pid}',
                ''
            )

    except Exception as e:
        # Log the error
        logger.error(f"Error during login for user {pid}: {str(e)}", exc_info=True)
        return (
            'An error occurred. Please try again later.',
            True,
            'danger',
            no_update,
            ''
        )