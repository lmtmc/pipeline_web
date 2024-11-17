# todo password clear after login
from dash import dcc, html, Input, Output, State, no_update
from flask_login import logout_user, current_user
import os
import dash_bootstrap_components as dbc
from my_server import app, User
from flask_login import login_user
from werkzeug.security import check_password_hash
from functions import project_function as pf, logger
from views.ui_elements import Storage
import time
import yaml

from config_loader import load_config
try :
    config = load_config()
except Exception as e:
    print(f"Error loading configuration: {e}")

prefix = config['path']['prefix']
default_work_lmt = config['path']['work_lmt']
pf.ensure_path_exists(default_work_lmt)

lmtoy_run_path = os.path.join(default_work_lmt, 'lmtoy_run')
pf.ensure_path_exists(default_work_lmt)

pid_options = pf.get_pid_option(lmtoy_run_path)


layout = dbc.Container([
    dcc.Location(id='url_login', refresh=True),
    html.Img(src='assets/lmt_img.jpg', style={'width': '100%', 'height': 'auto', 'margin-top': '100px'},
             className='mb-4'),
    html.Div([
        html.H1('Login using PID', className='text-center text-primary, mb-4'),
        dbc.Label('Select a PID:', id='h1-label', className='mb-4'),
        dcc.Dropdown(id='pid', options=pid_options, className='mb-4'),
        dbc.Label('Password:', id='pwd-label', className='mb-4'),
        dbc.Input(id='pwd-box', n_submit=0, type='password', className='mb-5'),
        html.Div(dbc.Alert(id='output-state', is_open=False, className='alert-warning', duration=3000)),
        html.Div(dbc.Button('Login', type='submit', id='login-button',
                            style={'pointer-events': 'none', 'opacity': '0.5', 'width': '100%'}, className='mb-4'
                            ), className="d-grid gap-2"),

    ],
    )],

    style={'width': '500px', 'margin': 'auto'})

# if both pid and password have value then enable the login button
@app.callback(
    Output('login-button', 'style'),
    [
        Input('pid', 'value'),
        Input('pwd-box', 'value')
    ]
)
def disable_login_button(pid, password):
    if pid and password:
        return {'pointer-events': 'auto', 'opacity': '1'}
    return {'pointer-events': 'none', 'opacity': '0.5'}


# if the input password matches the pid password, login to that pid
@app.callback(
    Output('url_login', 'pathname'),
    Output('output-state', 'children'),
    Output('output-state', 'is_open'),
    Output(Storage.DATA_STORE.value, 'data', allow_duplicate=True),
    Output('pwd-box', 'value'),
    Input('login-button', 'n_clicks'),
    State('pid', 'value'),
    State('pwd-box', 'value'),
    State('output-state', 'is_open'),
    State(Storage.DATA_STORE.value, 'data'),
    prevent_initial_call='initial_duplicate'
)
def login_state(n_clicks, pid, password, is_open, data):
    if not n_clicks:
        return no_update, no_update, no_update, no_update, no_update

    user = User.query.filter_by(username=pid).first()
    if user and check_password_hash(user.password, password):
        login_user(user)

        data['pid'] = pid
        data['source'] = pf.get_source(default_work_lmt, pid)

        return f'{prefix}project', '', False, data, ''
    else:
        return f'{prefix}login', 'Invalid password', True, data, ''
