from dash import dcc, html, Input, Output, State
from my_server import app
from flask_login import logout_user, current_user
from flask import session
from views import login, project_layout, help, ui_elements as ui
import argparse
from config_loader import load_config

# load the configuration
try :
    config = load_config()
except Exception as e:
    print(f"Error loading configuration: {e}")
    config = {}

# Constants
PREFIX = config['path']['prefix']
DEFAULT_WORK_LMT = config['path']['work_lmt']
DATA_STORE_INIT = {
    'pid': None,
    'runfile': None,
    'source': {},
    'selected_row': None,
    'selected_runfile': None,
    'selected_session': None
}
# Define the app layout
def create_layout():
    return html.Div(
        [
            html.Div(id='navbar-container'),
            html.Br(),
            html.Div(id='body-content', className='content-container'),
            dcc.Location(id='url', refresh=False),
            dcc.Store(id='data-store', data=DATA_STORE_INIT, storage_type='local'),
        ],
        id='main-container',
        className='main-container'
    )

app.layout = create_layout()

# update the body-content children based on the URL

@app.callback(
    [
        Output('navbar-container', 'children'),
        Output('body-content', 'children'),
        Output('data-store', 'data',allow_duplicate=True)
    ],
    Input('url', 'pathname'),
    State('data-store', 'data'),
    prevent_initial_call=True
)
def update_page(pathname,data):
    if not data:
        data = DATA_STORE_INIT

    is_authenticated = current_user.is_authenticated
    username = current_user.username if is_authenticated else None
    navbar = ui.create_navbar(is_authenticated, username)

    if not pathname.startswith(PREFIX):
        return navbar, html.Div('404 - Page not found'), data

    route = pathname[len(PREFIX):]

    if route in ['', 'login']:
        content = login.layout
    elif route == 'project' and is_authenticated:
        content = project_layout.layout
    elif route == 'help':
        content = help.layout
    elif route == 'logout':
        if is_authenticated:
            data = DATA_STORE_INIT
            logout_user()
            session.clear()
        content = dcc.Location(pathname=f'{PREFIX}login', id='redirect-after-logout')
    elif not is_authenticated:
        content = login.layout
    else:
        content = html.Div('404 - Page not found')

    return navbar, content, data

server = app.server

# Run the server
def main():
    parser = argparse.ArgumentParser(description="Run the Dash app")
    parser.add_argument("-p", "--port", type=int, default=8000, help="Port to run the Dash app on")
    args = parser.parse_args()

    try:
        app.server.run(port=args.port, debug=True)
    except Exception as e:
        print(f"Error: {e}")
        app.server.run(port=args.port, debug=True)

if __name__ == '__main__':
    main()