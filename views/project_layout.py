import logging
import os
from pathlib import Path

import flask
from dash import html, Input, Output, State, ALL, ctx, no_update, dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from flask_login import current_user
import shutil
from my_server import app
from functions import project_function as pf
from functions.project_function import get_session_list
from views import ui_elements as ui
from views.ui_elements import Session, Runfile
from config_loader import load_config

try :
    config = load_config()
except Exception as e:
    print(f"Error loading configuration: {e}")

prefix = config['path']['prefix']
default_work_lmt = config['path']['work_lmt']

default_session_prefix = os.path.join(default_work_lmt, 'lmtoy_run/lmtoy_')
init_session = config['session']['init_session']

# Constants

HIDE_STYLE = {'display': 'none'}
SHOW_STYLE = {'display': 'block'}

# if any of the update_btn get trigger, update the session list
update_btn = [
    Session.SAVE_BTN.value, Session.CONFIRM_DEL.value, Runfile.DEL_BTN.value
]

layout = html.Div(
    [
        dbc.Row([
            dbc.Col([
                ui.session_layout,
                html.Br(),
                ui.submit_job_layout
    ],width=2,),
            dbc.Col(ui.runfile_layout, width=10),
        ]),
        dcc.Location(id='edit-url', refresh=True),
     ]
)

# Hide the Delete Session and Edit, delete, clone runfile for the default session
@app.callback(
    [
        Output(Runfile.DEL_BTN.value, 'style'),
        Output(Runfile.EDIT_BTN.value, 'style'),
        Output(Runfile.CLONE_BTN.value, 'style'),
        Output(Session.DEL_BTN.value, 'style'),
        Output(Session.NEW_BTN.value, 'style'),
    ],
    [Input(Session.SESSION_LIST.value, 'active_item')]
)
def default_session(active_session):
    if active_session is None:
        # Hide both delete and new session buttons if no session is selected
        return 5 * [HIDE_STYLE]

    if active_session == init_session:
        # Hide session delete and runfile buttons for the default session
        return [HIDE_STYLE] * 4 + 1*[SHOW_STYLE]

    # Default case where all buttons are visible
    return 5 * [SHOW_STYLE]

# update session list
@app.callback(
    [
        Output(Session.SESSION_LIST.value, 'children'),
        Output(Session.MODAL.value, 'is_open'),
        Output(Session.MESSAGE.value, 'children'),
        Output(Session.SESSION_LIST.value, 'active_item'),
        Output(Session.RUNFILE_SELECT.value, 'options'),
        # Output(Session.RUNFILE_SELECT.value, 'value'),
    ],
    [
        Input(Session.NEW_BTN.value, 'n_clicks'),
        Input(Session.SAVE_BTN.value, 'n_clicks'),
        Input(Session.CONFIRM_DEL.value, 'submit_n_clicks'),
        Input(Runfile.CONFIRM_DEL_ALERT.value, 'submit_n_clicks'),
        Input(Runfile.SAVE_CLONE_RUNFILE_BTN.value, 'n_clicks'),
        Input(Session.SESSION_LIST.value, 'active_item'),
    ],
    [
        State(Session.NAME_INPUT.value, 'value')
    ],
)
def update_session_display(n1, n2, n3, n4, n5, active_session, name):
    try:
        triggered_id = ctx.triggered_id

        if not pf.check_user_exists():
            return [], False, "User is not authenticated", no_update,no_update

        pid_path = os.path.join(default_work_lmt, current_user.username)
        try:
            os.makedirs(pid_path, exist_ok=True)
        except OSError as e:
            error_message = f"Failed to create directory {pid_path}: {str(e)}"
            logging.error(error_message)
            return [], False, error_message, None, []

        modal_open, message = no_update, ''
        session_list = get_session_list(init_session, pid_path)

        if triggered_id == Session.NEW_BTN.value:
            modal_open = True

        elif triggered_id == Session.SAVE_BTN.value:
            message, modal_open = pf.save_session(pid_path, name, active_session)

        elif triggered_id == Session.CONFIRM_DEL.value:
            message = pf.delete_session(pid_path, active_session)
            active_session = None if "Successfully" in message else active_session

        if triggered_id in update_btn:
            active_session = init_session if active_session is None else active_session

        # Ensure a valid active session
        active_session = active_session or init_session

        runfile_options, runfile_value = pf.get_runfile_info(active_session, pid_path)

        return session_list, modal_open, message, active_session, runfile_options

    except Exception as e:
        logging.error(f"Error in update_session_display: {str(e)}")
        return [], False, f"An error occurred: {str(e)}", None, [], None

# update the label of the submit job
@app.callback(
    Output('submit-session-job-label', 'children'),
    Input(Session.SESSION_LIST.value, 'active_item'),
    prevent_initial_call=True
)
def update_submit_job_label(active_session):
    if active_session:
        return f"Submit Job for {active_session}"
    return "Submit Job"

# display confirmation alert when delete session button is clicked
@app.callback(
    [
        Output(Session.CONFIRM_DEL.value, 'displayed'),
        Output(Session.CONFIRM_DEL.value, 'message')
    ],
    [
        Input(Session.DEL_BTN.value, 'n_clicks'),
        Input(Session.SESSION_LIST.value, 'active_item'),
    ])
def display_confirmation(n_clicks, active_item):
    if ctx.triggered_id == Session.DEL_BTN.value and active_item:
        return True, f'Are you sure you want to delete {active_item}?'
    return False, ''

# If there is data in the folder, show the open result link
@app.callback(
    Output('view-result-url', 'style'),
    Output('view-result-url', 'href'),
    Input(Session.SESSION_LIST.value, 'active_item'),
    prevent_initial_call=True
)
def show_job_status(active_session):

    if not active_session:
        return no_update
    session_path = pf.get_session_path(current_user.username, active_session)
    status,run_btn_disabled, view_result_style,view_result_href = pf.check_job_status(session_path)
    return view_result_style, view_result_href
# open readme in a new tab when chick view result button

# Flask route to serve the file, using session as part of the URL
@app.server.route('/view_result/<username>/<session>')
def serve_readme(username, session):
    # Construct the file path using the session from the URL
    readme_path = os.path.join(pf.get_session_path(current_user.username, session), 'README.html')
    print(f'Serving README from: {readme_path}')
    if os.path.exists(readme_path):
        return flask.send_file(readme_path)
    else:
        return 'Error: README.html not found', 404
# if selected file is not empty, show the submit job button
@app.callback(
    Output(Runfile.RUN_BTN.value, 'style'),
    Input(Session.RUNFILE_SELECT.value, 'value'),
    prevent_initial_call=True
)
def enable_run_button(selected_runfile):
    if selected_runfile:
        return SHOW_STYLE
    return HIDE_STYLE

# submit job
@app.callback(
    Output(Session.SUBMIT_JOB.value, 'children'),
    Input(Runfile.RUN_BTN.value, 'n_clicks'),
    State(Session.RUNFILE_SELECT.value, 'value'),
    prevent_initial_call=True
)
def submit_job(n_clicks, selected_runfile):
    if not selected_runfile:
        return html.Pre('No runfile selected.')

    try:
        runfile = os.path.basename(selected_runfile)
        result = pf.execute_remote_command(current_user.username, runfile)

        # Step 2: Update UI with the result
        result_message = f"Job submitted successfully!\n{result}"
        return result_message
    except Exception as e:
        error_message = html.Pre(f"Error: {e}")
        return error_message

# display selected runfile
@app.callback(
    [
        Output(Runfile.CONTENT_TITLE.value, 'children'),
        Output(Runfile.CONTENT_DISPLAY.value, 'style'),
        Output(Runfile.CONTENT.value, 'value') # if output textarea
    ],
    [
        Input({'type': 'runfile-radio', 'index': ALL}, 'value'),
        Input(Runfile.CONFIRM_DEL_ALERT.value, 'submit_n_clicks'),
    ],
    prevent_initial_call=True
)
def display_runfile_content(selected_runfile, del_runfile_btn):
    if not ctx.triggered:
        raise PreventUpdate
    current_runfile = next((value for value in selected_runfile if value), None)
    if not current_runfile:
        return '', HIDE_STYLE, ''

    runfile_title = pf.get_runfile_title(current_runfile, init_session)
    runfile_content = pf.df_runfile(current_runfile)[1]

    if ctx.triggered_id == Runfile.CONFIRM_DEL_ALERT.value:
        pf.del_runfile(current_runfile)
    return runfile_title,SHOW_STYLE, runfile_content

# open a modal if clone-runfile button
@app.callback(
    Output(Runfile.CLONE_RUNFILE_MODAL.value, 'is_open'),
    Output(Runfile.SAVE_CLONE_RUNFILE_STATUS.value, 'children'),
    Output(Runfile.SAVE_CLONE_RUNFILE_STATUS.value, 'style'),
    [
        Input(Runfile.CLONE_BTN.value, 'n_clicks'),
        Input(Runfile.SAVE_CLONE_RUNFILE_BTN.value, 'n_clicks'),
        Input({'type': 'runfile-radio', 'index': ALL}, 'value'),
    ],
    [
        State(Runfile.NAME_INPUT.value, 'value'),
        State(Runfile.CLONE_RUNFILE_MODAL.value, 'is_open'),
    ],
    prevent_initial_call=True
)
def copy_runfile(clone_clicks, save_clicks, selected_runfile, new_name, modal_is_open):
    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered_id
    current_runfile = next((value for value in selected_runfile if value), None)

    if not current_runfile:
        return no_update, no_update, no_update

        # Handle opening the modal
    if triggered_id == Runfile.CLONE_BTN.value:
        return True, '', HIDE_STYLE

        # Handle saving the cloned runfile
    if triggered_id == Runfile.SAVE_CLONE_RUNFILE_BTN.value:
        if not new_name:
            return modal_is_open, 'Please enter a new name!', SHOW_STYLE

        new_name_path = os.path.join(Path(current_runfile).parent, f"{current_user.username}.{new_name}")

        if os.path.exists(new_name_path):
            return modal_is_open, f"Runfile {new_name} already exists!", SHOW_STYLE

        try:
            shutil.copy(current_runfile, new_name_path)
            print(f"Runfile {new_name} created successfully!")
            return False, f'Runfile {new_name} created successfully!', HIDE_STYLE
        except Exception as e:
            return modal_is_open, f"Error creating runfile: {str(e)}", SHOW_STYLE

        # If we reach here, it means the runfile selection changed
    return modal_is_open, '', HIDE_STYLE

# click runfile delete button, show the confirmation alert
@app.callback(
    [
        Output(Runfile.CONFIRM_DEL_ALERT.value, 'displayed'),
        Output(Runfile.CONFIRM_DEL_ALERT.value, 'message')
    ],
    [
        Input(Runfile.DEL_BTN.value, 'n_clicks'),
        Input({'type': 'runfile-radio', 'index': ALL}, 'value')
    ],
    prevent_initial_call=True
)
def runfile_del_display_confirmation(n_clicks, selected_runfile):
    selected_runfile = [value for value in selected_runfile if value is not None]

    if ctx.triggered_id == Runfile.DEL_BTN.value:
        if selected_runfile:
            file_name = selected_runfile[0].split('/')[-1]
            return True, f'Are you sure you want to delete {file_name}?'
        else:
            return False, ''
    else:
        return False, ''

# If edit was clicked, show the modal
@app.callback(
    Output('edit-url', 'pathname'),
    Output('data-store', 'data'),
    Input(Runfile.EDIT_BTN.value, 'n_clicks'),
    [
        State({'type': 'runfile-radio', 'index': ALL}, 'value'),
        State('data-store', 'data')
    ],
)
def edit_runfile(n_clicks, runfile, data):
    if n_clicks is None:
        return no_update, no_update

    current_runfile = next((value for value in runfile if value), None)
    data['selected_runfile'] = current_runfile
    edit_url = f"{prefix}{data['instrument']}-edit"
    return edit_url , data

# if data store has selected runfile, set the runfile select value
@app.callback(
    Output({'type': 'runfile-radio', 'index': ALL}, 'value'),
    Input('data-store', 'data'),
    #prevent_initial_call=True
)
def preselect_runfile(data):
    # Check if there is a previously selected runfile in the data-store
    if data and 'selected_runfile' in data:
        return [None,data['selected_runfile']]
    # If no runfile is selected, ensure all radio buttons are cleared
    return [None, None]