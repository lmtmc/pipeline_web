import concurrent

from dash import dcc, html, Input, Output, State, no_update
import os
import dash_bootstrap_components as dbc
from my_server import app, User
from flask_login import login_user
from werkzeug.security import check_password_hash
from functions import project_function as pf
from views.ui_elements import Storage
from config_loader import load_config

US_17_sources = {
    "NGC6232" : [ 108853, 108854, 108855, 108857, 108858, 108859,],
    "VIIZw800": [ 107356, 107357, 107358, 107361, 107362, 107363,]}

MU_8_sources = {
    "NGC5194-CO": [
        88874, -88882, 88967, 88971,
        90648, 90650, 90652, 90654, 90658, 90660, 90664, 90666,
        90740, 90744, -90758,
        90911, 90915, -90947, 90951,
        -91037, 91041, 91112
    ],
    "NGC5194-HCN": [
        90995, 90999,
        88878,
        88990,
        90139, 90141, -90143, 90149,
        90151, 90155, 90157, 90163,
        90268, 90270, 90274, 90276,
        90280, 90282, 90286, 90381,
        90383, 90385, 90389, 90442,
        90444, 90446, 90450, 90452,
        90454, 90458, 90460, 90462,
        91328,
        91336, 91344, 91350, 91356,
        91362, 91368, 91523, 91534,
        91579, 91613, 91619, 91661,
        91669, 91681, 91713, 92215,
        92223, 92274, 92286, 92294,
        92351, 92504,
        91338,
        91346, 91352, 91358, 91364,
        91370, 91525, 91536, 91615,
        91621, 91663, 91671, 91675,
        91683, 91715, 92219, 92227,
        92280, 92290, 92300, 92355,
        92626
    ],
    "NGC628": [
        86278,
        88305, 88307, 88311, 88313, 88315,
        -88501,
        88649, 88653,
        88801, 88805,
        88915, 88919,
        -80101, -80099, -80097, -80093, -80091,
        -80089, -80087, -80045, -80043
    ]
}

# Load configuration
try:
    config = load_config()
except Exception as e:
    print(f"Error loading configuration: {e}")
    config = {}

prefix = config['path']['prefix']
default_work_lmt = config['path']['work_lmt']

pf.ensure_path_exists(default_work_lmt)
lmtoy_run_path = os.path.join(default_work_lmt, 'lmtoy_run')
pf.ensure_path_exists(default_work_lmt)

layout = dbc.Container(
    [
        dcc.Location(id='url_login', refresh=True),
        html.Img(src='assets/lmt_img.jpg', style={'width': '100%', 'height': 'auto', 'margin-top': '100px'}, className='mb-4'),
        dbc.Label('PID:', className='mb-2'),
        dbc.Input(id='pid', type='text', placeholder='Enter PID', className='mb-4'),
        dbc.Label('Password:', className='mb-2'),
        dbc.Input(id='pwd-box', n_submit=0, type='password', className='mb-5'),
        dbc.Alert(id='output-state', is_open=False, className='alert-warning', duration=3000),
        dbc.Button('Login', type='submit', id='login-button', className='mb-4 w-100'),
    ],
    style={'width': '500px', 'margin': 'auto'}
)

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
# @app.callback(
#     [
#         Output('url_login', 'pathname'),
#         Output('output-state', 'children'),
#         Output('output-state', 'is_open'),
#         Output(Storage.DATA_STORE.value, 'data', allow_duplicate=True),
#         Output('pwd-box', 'value')
#     ],
#     Input('login-button', 'n_clicks'),
#     [
#         State('pid', 'value'),
#         State('pwd-box', 'value'),
#         State('output-state', 'is_open'),
#         State(Storage.DATA_STORE.value, 'data')
#     ],
#     prevent_initial_call='initial_duplicate'
# )
# def login_state(n_clicks, pid, password, is_open, data):
#     if not n_clicks:
#         return no_update, no_update, no_update, no_update, no_update
#
#     try:
#         user = User.query.filter_by(username=pid).first()
#         if user and check_password_hash(user.password, password):
#             login_user(user)
#             if data is None:
#                 data = {}
#
#             # Attempt to fetch the source with a timeout
#             def get_source_with_timeout(pid):
#                 with concurrent.futures.ThreadPoolExecutor() as executor:
#                     future = executor.submit(pf.get_source, pid)
#                     return future.result(timeout=5)  # Set timeout in seconds
#
#             try:
#                 source = get_source_with_timeout(pid)
#             except concurrent.futures.TimeoutError:
#                 if pid == '2023-S1-US-17':
#                     source = US_17_sources
#                 elif pid == '2018-S1-MU-8':
#                     source = MU_8_sources
#                 else:
#                     source = None
#                 print(f"Timeout fetching source for {pid}")
#             except Exception as e:
#                 source = None
#                 print(f"Error fetching source for {pid}: {e}")
#
#             data.update({
#                 'pid': pid,
#                 'source': source
#             })
#             print(f'Logged in as {pid}', 'data:', data)
#             print('source:', data.get('source'))
#             return f'{prefix}project', '', False, data, ''
#         else:
#             return f'{prefix}login', 'Invalid password', True, data, ''
#     except Exception as e:
#         return f'{prefix}login', f'Error: {e}', True, data, ''

# if the input password matches the pid password, login to that pid
@app.callback(
    [
        Output('url_login', 'pathname'),
        Output('output-state', 'children'),
        Output('output-state', 'is_open'),
        Output(Storage.DATA_STORE.value, 'data', allow_duplicate=True),
        Output('pwd-box', 'value')
    ],
    Input('login-button', 'n_clicks'),
    [
        State('pid', 'value'),
        State('pwd-box', 'value'),
        State('output-state', 'is_open'),
        State(Storage.DATA_STORE.value, 'data')
    ],
    prevent_initial_call='initial_duplicate'
)
def login_state(n_clicks, pid, password, is_open, data):
    if not n_clicks:
        return no_update, no_update, no_update, no_update, no_update

    try:
        # Fetch user and validate password
        user = User.query.filter_by(username=pid).first()
        if user and check_password_hash(user.password, password):
            login_user(user)

            # Initialize data if None
            if data is None:
                data = {}

            # Map PIDs to sources for clarity and scalability
            sources_map = {
                '2023-S1-US-17': US_17_sources,
                '2018-S1-MU-8': MU_8_sources
            }
            source = sources_map.get(pid, None)  # Get source if PID exists, otherwise None

            # Update data with PID and source
            data.update({
                'pid': pid,
                'source': source
            })

            # Successful login, redirect to project page
            return f'{prefix}project', '', False, data, ''
        else:
            # Invalid credentials
            return f'{prefix}login', 'Invalid password', True, data, ''
    except Exception as e:
        # Log the error and return error message
        print(f"Error during login: {e}")
        return f'{prefix}login', f'Error: {e}', True, data, ''
