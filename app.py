# Standard library imports
import os
import argparse
from flask import session
from flask_login import logout_user, current_user
import dash_bootstrap_components as dbc
# Third-party imports
from dash import dcc, html, Input, Output, State

# Local imports
from my_server import app
from views import login, help, ui_elements as ui, admin_page, project_layout
from config_loader import load_config
from functions import project_function as pf

# Load configuration
try:
    config = load_config()
except Exception as e:
    print(f"Error loading configuration: {e}")
    config = {}

# Constants
PREFIX = config['path']['prefix']
DEFAULT_WORK_LMT = config['path']['work_lmt']

# Data store initialization
DATA_STORE_INIT = {
    'pid': None,
    'runfile': None,
    'source': {},
    'selected_row': None,
    'selected_runfile': None,
    'selected_session': None,
    'selected_project': None
}

def create_layout():
    """Create the main application layout."""
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

@app.callback(
    [
        Output('navbar-container', 'children'),
        Output('body-content', 'children'),
        Output('data-store', 'data', allow_duplicate=True)
    ],
    Input('url', 'pathname'),
    State('data-store', 'data'),
    prevent_initial_call=True
)
def update_page(pathname, data):
    """Update the page content based on the current URL path."""
    if not data:
        data = DATA_STORE_INIT

    is_authenticated = current_user.is_authenticated
    username = current_user.username if is_authenticated else None
    navbar = ui.create_navbar(is_authenticated, username)

    # Handle root path
    if pathname == '/':
        if is_authenticated:
            if current_user.is_admin:
                return navbar, admin_page.layout, data
            return navbar, project_layout.layout, data
        return navbar, login.layout, data

    # Remove prefix if present
    route = pathname[len(PREFIX):] if pathname.startswith(PREFIX) else pathname.lstrip('/')

    # Route handling
    if route in ['', 'login']:
        if is_authenticated:
            if current_user.is_admin:
                return navbar, admin_page.layout, data
            return navbar, project_layout.layout, data
        return navbar, login.layout, data
    
    elif route == 'admin' and is_authenticated and current_user.is_admin:
        return navbar, admin_page.layout, data
    
    elif route.startswith('project/'):
        if not is_authenticated:
            return navbar, login.layout, data
            
        # Extract PID and update data store
        pid = route.split('/')[1]
        data['pid'] = pid
        data['selected_project'] = pid
        
        # Get source for the PID
        try:
            source = pf.get_source(pid)
            data['source'] = source
        except Exception as e:
            print(f"Error getting source for PID {pid}: {str(e)}")
        
        return navbar, project_layout.layout, data
    
    elif route == 'help':
        return navbar, help.layout, data
    
    elif route == 'logout':
        if is_authenticated:
            data = DATA_STORE_INIT
            logout_user()
            session.clear()
        return navbar, dcc.Location(pathname=f'{PREFIX}login', id='redirect-after-logout'), data
    
    elif not is_authenticated:
        return navbar, login.layout, data
    
    return navbar, html.Div('404 - Page not found'), data

def main():
    """Run the server with command line arguments."""
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
server = app.server
