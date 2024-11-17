from dash import dcc, html, Input, Output, State, no_update
import os
import dash_bootstrap_components as dbc
from my_server import app, User
from flask_login import login_user
from werkzeug.security import check_password_hash
from functions import project_function as pf, pid_info
from views.ui_elements import Storage
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

layout = dbc.Container([
    dcc.Location(id='url_login', refresh=True),
    html.Img(src='assets/lmt_img.jpg', style={'width': '100%', 'height': 'auto', 'margin-top': '100px'}, className='mb-4'),
    dbc.Label('PID:', className='mb-2'),
    dbc.Input(id='pid', type='text', placeholder='Enter PID', className='mb-4'),
    dbc.Label('Password:', className='mb-2'),
    dbc.Input(id='pwd-box', n_submit=0, type='password', className='mb-5'),
    dbc.Alert(id='output-state', is_open=False, className='alert-warning', duration=3000),
    dbc.Button('Login', type='submit', id='login-button', className='mb-4 w-100'),
], style={'width': '500px', 'margin': 'auto'})

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

    try:
        user = User.query.filter_by(username=pid).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            data['pid'] = pid
            data['source'] = pid_info.get_source(default_work_lmt, pid)
            data['email'] = pid_info.get_email(pid)
            data['instrument'] = pid_info.get_instrument(pid)
            return f'{prefix}project', '', False, data, ''
        else:
            return f'{prefix}login', 'Invalid password', True, data, ''
    except Exception as e:
        return f'{prefix}login', f'Error: {e}', True, data, ''