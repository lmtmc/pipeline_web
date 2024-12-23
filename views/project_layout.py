import logging
import os
from pathlib import Path

import flask
import pandas as pd
from dash import html, Input, Output, State, ALL, ctx, no_update, dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from flask_login import current_user
import shutil
from my_server import app
from functions import project_function as pf
from views import ui_elements as ui
from views.ui_elements import Session, Runfile, Table
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
        # dcc.Interval(id='check-job-interval', interval=60 * 1000, n_intervals=0),
        dbc.Row([
            dbc.Col([
                ui.session_layout,
                html.Br(),
            ],width=2,),
            dbc.Col(ui.runfile_layout, width=10),
        ], className='mb-3'),
        dbc.Row([
            dbc.Col(ui.submit_job_layout,),
            dbc.Col(ui.job_status_layout,),
        ]),
        html.Div(id='parameter-edit-selector'),

     ]
)

# Hide the Delete Session and Edit, delete, clone runfile for the default session
@app.callback(
    [
        Output(Runfile.DEL_BTN.value, 'style'),
        Output(Runfile.CLONE_BTN.value, 'style'),
        Output(Session.DEL_BTN.value, 'style'),
        Output(Session.NEW_BTN.value, 'style'),
        Output('data-store', 'data'),
    ],
    Input(Session.SESSION_LIST.value, 'active_item'),
    State('data-store', 'data'),
)
def default_session(active_session, data_store):
    # Update the selected session in the data store
    data_store['selected_session'] = active_session

    if active_session is None:
        # Hide all buttons if no session is selected
        return HIDE_STYLE,HIDE_STYLE, HIDE_STYLE, HIDE_STYLE, data_store

    if active_session == init_session:
        # Hide delete buttons and show only the new session button for the default session
        return HIDE_STYLE,HIDE_STYLE, HIDE_STYLE, SHOW_STYLE, data_store

    # Default case: Show all buttons
    return SHOW_STYLE, SHOW_STYLE,SHOW_STYLE, SHOW_STYLE, data_store


# update session list
@app.callback(
    [
        Output(Session.SESSION_LIST.value, 'children'),
        Output(Session.MODAL.value, 'is_open'),
        Output(Session.MESSAGE.value, 'children'),
        Output(Session.SESSION_LIST.value, 'active_item'),
        Output(Session.RUNFILE_SELECT.value, 'options'),
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
        session_list = pf.get_session_list(init_session, pid_path)

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

# Flask route to serve the file, using session as part of the URL
@app.server.route('/view_result/<username>/<session>')
def serve_readme(username,session):
    # Construct the file path using the session from the URL
    readme_path = os.path.join(pf.get_session_path(current_user.username, session), 'README.html')
    print(f'Serving README from: {readme_path}')
    if os.path.exists(readme_path):
        return flask.send_file(readme_path)
    else:
        return 'Error: README.html not found', 404
# if selected file is not empty and email input is a valid email format show the submit job button
@app.callback(
    Output(Runfile.RUN_BTN.value, 'disabled'),
    Input(Session.RUNFILE_SELECT.value, 'value'),
    Input('email-input', 'value'),
    prevent_initial_call=True
)
def enable_run_button(selected_runfile, email):
    if selected_runfile and email and pf.is_valid_email(email):
        return False
    return True

# submit job
@app.callback(
    Output(Session.SUBMIT_JOB.value, 'children'),
    Input(Runfile.RUN_BTN.value, 'n_clicks'),
    State(Session.RUNFILE_SELECT.value, 'value'),
    State('email-input', 'value'),
    prevent_initial_call=True
)
def submit_job(n_clicks, selected_runfile, email):
    if not selected_runfile:
        return html.Pre('No runfile selected.')

    try:
        runfile = os.path.basename(selected_runfile)
        result = pf.execute_remote_submit(current_user.username, runfile)

        print('result',type(result),result)

        if not isinstance(result, dict):
            return html.Pre(f"Unexpected result format: {result}")
        # Step 2: Update UI with the result
        if result["returncode"] == 0:
            result_message = f"Job submitted successfully for {runfile}!\n{result}"
            print('result_message',result_message)
            print('Sending email...',email)
            pf.send_email('Job submitted successfully', result_message, email)

        else:
            result_message = f"Error in submission: {result['stderr']}"
        return result_message
    except Exception as e:
        error_message = html.Pre(f"Error: {e}")
        return error_message

@app.callback(
    Output("slurm-job-status-output", "children", allow_duplicate=True),
    Input("check-status-btn", "n_clicks"),
    State('data-store', 'data'),
    prevent_initial_call=True,
)
def update_job_status(n_clicks, data):
    selected_runfile= data.get('selected_runfile')
    status, success = pf.check_runfile_job_status(selected_runfile)
    file_name = os.path.basename(selected_runfile)
    if success:
        # If jobs are found, display them in a table
        if isinstance(status, list) and status:
            headers = status[0].keys()
            rows = [
                html.Tr([html.Td(job[header]) for header in headers])
                for job in status
            ]

            return html.Div([
                html.H5(f"Current job status for {file_name}"),
                dbc.Table(
                    [
                        html.Thead(html.Tr([html.Th(header) for header in headers])),
                        html.Tbody(rows),
                    ],
                    bordered=True,
                    hover=True,
                    responsive=True,
                    striped=True,
                ),
            ])
        else:
            # No jobs found case
            return dbc.Alert("No jobs found.", color="info", dismissable=True)
    else:
        # Show an error if the status retrieval failed
        return dbc.Alert(status, color="danger", dismissable=True)
# if account is selected, show the default value
@app.callback(
    Output("user-id-input", "value"),
    Input("job-status-option", "value"),
    prevent_initial_call=True,
)
def update_user_id_input(option):
    if option == "Account":
        return "lmthelpdesk_umass_edu"
    return ''

@app.callback(
    Output("cancel-job-confirm-dialog", "displayed"),
    Input("cancel-job-btn", "n_clicks"),
    State("job-id-input", "value"),
    prevent_initial_call=True,
)
def display_confirm_dialog(n_clicks, job_id):
    if not job_id:
        return False
    return True

@app.callback(
    Output("slurm-job-status-output", "children"),
    Input("cancel-job-confirm-dialog", "submit_n_clicks"),
    State("job-id-input", "value"),
    prevent_initial_call=True,
)
def cancel_job(n_clicks, job_id):
    status, success = pf.cancel_slurm_job(job_id)
    if success:
        # Display the parsed job status in a table
        return html.Div([
            dbc.Alert(f"Job {job_id} has been successfully cancelled.", color="success", dismissable=True),
            dbc.Table(
        [
                    html.Thead(html.Tr([html.Th(header) for header in status.keys()])),
                    html.Tbody(html.Tr([html.Td(value) for value in status.values()])),
                ],
                bordered=True,
                hover=True,
                responsive=True,
                striped=True,
            ),
            ],
        )
    else:
        # Show an error or no jobs found message
        return dbc.Alert(status, color="danger", dismissable=True)

# display selected runfile
@app.callback(
    [
        Output(Runfile.CONTENT_TITLE.value, 'children'),
        Output(Runfile.CONTENT_DISPLAY.value, 'style'),
        Output('runfile-table', 'rowData', allow_duplicate=True),
        Output('runfile-table', 'columnDefs', allow_duplicate=True),
        Output('data-store', 'data', allow_duplicate=True)
    ],
    [
        Input({'type': 'runfile-radio', 'index': ALL}, 'value'),
        Input(Runfile.CONFIRM_DEL_ALERT.value, 'submit_n_clicks'),
    ],
    State('data-store', 'data'),
    prevent_initial_call=True
)
def display_runfile_content(selected_runfile, del_runfile_btn, data_store):
    if not ctx.triggered:
        raise PreventUpdate
    current_runfile = next((value for value in selected_runfile if value), None)

    if not current_runfile:
        return '', HIDE_STYLE, '','',data_store

    runfile_title = pf.get_runfile_title(current_runfile, init_session)
    runfile_data,runfile_content = pf.df_runfile(current_runfile)

    row_data = runfile_data.to_dict('records')
    column_defs = [
        {
            'headerName': 'instrument' if c == '_io' else 'source' if c == '_s' else c,
            'field': c,
            'filter': True,
            'sortable': True,
            'headerTooltip': f'{c} column',
        } for c in runfile_data.columns
    ]

    if ctx.triggered_id == Runfile.CONFIRM_DEL_ALERT.value:
        pf.del_runfile(current_runfile)
    data_store['selected_runfile'] = current_runfile
    return runfile_title,SHOW_STYLE, row_data, column_defs,data_store

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
# If selected rows, show the edit button else hide it
@app.callback(
    Output(Table.OPTION.value, 'style'),
    Input('runfile-table', 'selectedRows'),
    State(Session.SESSION_LIST.value, 'active_item'),
    prevent_initial_call=True
)
def show_edit_button(selected_rows, active_session):
    if selected_rows and active_session != init_session:
        return SHOW_STYLE
    return HIDE_STYLE

# if delete row button is clicked, show the confirmation alert
@app.callback(
    [
        Output(Table.CONFIRM_DEL_ROW.value, 'displayed'),
        Output(Table.CONFIRM_DEL_ROW.value, 'message')
    ],
    Input(Table.DEL_ROW_BTN.value, 'n_clicks'),
    prevent_initial_call=True
)
def display_confirmation(n_clicks):
    if n_clicks:
        return True, 'Are you sure you want to delete the selected row(s)?'
    return False, ''

# if confirm delete is clicked, delete the selected rows
@app.callback(
    Output('runfile-table', 'rowData', allow_duplicate=True),  # Update the table with new data
    Input(Table.CONFIRM_DEL_ROW.value, 'submit_n_clicks'),  # Confirm deletion
    State('runfile-table', 'selectedRows'),  # Selected rows to delete
    State('runfile-table', 'rowData'),  # Current table data
    State('data-store', 'data'),  # Data context, e.g., file path
    prevent_initial_call=True
)
def delete_row(confirm_clicks, selected_rows, row_data, data_store):
    if confirm_clicks and selected_rows:
        # Extract selected row indices
        selected_ids = {row['index'] for row in selected_rows}
        # Filter out selected rows
        updated_data = [row for row in row_data if row['index'] not in selected_ids]

        # Save updated data to file
        if data_store and 'selected_runfile' in data_store:
            file_path = data_store['selected_runfile']
            df = pd.DataFrame(updated_data)
            pf.save_runfile(df,file_path)
            print(f"Updated data saved to {file_path}")

        # Return updated data to the table
        return updated_data

    # If no rows were selected or no deletion, return the current data unchanged
    return row_data
# if add row button is clicked, add a new row to the table
@app.callback(
    Output('runfile-table', 'rowData', allow_duplicate=True),  # Update the table with cloned data
    Input(Table.CLONE_ROW_BTN.value, 'n_clicks'),  # Clone button clicked
    State('runfile-table', 'selectedRows'),  # Selected rows to clone
    State('runfile-table', 'rowData'),  # Current table data
    State('data-store', 'data'),  # Data context, e.g., file path
    prevent_initial_call=True
)
def clone_row(n_clicks, selected_rows, row_data, data_store):
    if n_clicks and selected_rows:
        # Determine the maximum current index to create unique indices for cloned rows
        max_index = max(row['index'] for row in row_data) if row_data else -1
        new_rows = []

        for i, row in enumerate(selected_rows):
            # Create a clone of the selected row with a unique index
            cloned_row = row.copy()
            cloned_row['index'] = max_index + i + 1  # Assign new unique index
            new_rows.append(cloned_row)

        # Append cloned rows to the existing data
        updated_data = row_data + new_rows

        # Save updated data to file
        if data_store and 'selected_runfile' in data_store:
            file_path = data_store['selected_runfile']
            df = pd.DataFrame(updated_data)
            pf.save_runfile(df, file_path)
            print(f"Updated data saved to {file_path}")

        # Return updated data to the table
        return updated_data

    # If no rows were selected or no cloning, return the current data unchanged
    return row_data

# choose the parameter layout based on the instrument
instruments = ['rsr', 'seq']
@app.callback(
    Output('parameter-edit-selector', 'children'),
    Input('runfile-table', 'selectedRows'),
    prevent_initial_call=True
)
def show_edit_layout(selected_rows):
    if not selected_rows or not isinstance(selected_rows, list) or not selected_rows[0]:
        raise PreventUpdate
    instrument = selected_rows[0].get('_io', '').upper()
    if 'RSR' in instrument:
        layout = ui.create_parameter_layout_modal(instruments[0],len(selected_rows),ui.rsr_parameter_configs)
    elif 'SEQ' in instrument:
        layout = ui.create_parameter_layout_modal(instruments[1],len(selected_rows),ui.sequoia_parameter_configs)
    else:
        layout = html.Div('Invaid instrument', className='alert alert-danger')
    return layout

# if selected rows, and the edit button is clicked, show the parameter edit modal
@app.callback(
    Output('parameter-edit-modal', 'is_open'),
    Input(Table.EDIT_BTN.value, 'n_clicks'),
    State('runfile-table', 'selectedRows'),
    prevent_initial_call=True
)
def show_edit_layout(n, selected_rows):
    if selected_rows:
        return True
    return False

# if the parameter-edit-layout is open and edit-appy or edit-cancel is clicked, close the modal
@app.callback(
    Output('parameter-edit-modal', 'is_open', allow_duplicate=True),
    Input('rsr-single-edit-apply', 'n_clicks'),
    Input('rsr-single-edit-cancel', 'n_clicks'),
    prevent_initial_call=True
)
def close_edit_layout(n1,n2):
    return False

@app.callback(
    Output('parameter-edit-modal', 'is_open', allow_duplicate=True),
    Input('seq-single-edit-apply', 'n_clicks'),
    Input('seq-single-edit-cancel', 'n_clicks'),
    prevent_initial_call=True
)
def close_edit_layout(n1,n2):
    return False

@app.callback(
    Output('parameter-edit-modal', 'is_open', allow_duplicate=True),
    Input('rsr-multi-edit-apply', 'n_clicks'),
    Input('rsr-multi-edit-cancel', 'n_clicks'),
    prevent_initial_call=True
)
def close_edit_layout(n1,n2):
    return False

@app.callback(
    Output('parameter-edit-modal', 'is_open', allow_duplicate=True),
    Input('seq-multi-edit-apply', 'n_clicks'),
    Input('seq-multi-edit-cancel', 'n_clicks'),
    prevent_initial_call=True
)
def close_edit_layout(n1,n2):
    return False

# if the parameter-edit-layout is open, populate the source option from datastore
@app.callback(
    [
        Output('rsr-_s-dropdown', 'options'),
        Output('rsr-_s-dropdown', 'value')
    ],
    Input(Table.EDIT_BTN.value, 'n_clicks'),
    [
        State('runfile-table', 'selectedRows'),
        State('data-store', 'data')
    ],
    prevent_initial_call=True
)
def rsr_source_option(n, selected_rows, data):
    return pf.get_source_and_obsnum_options(n, selected_rows, data)

@app.callback(
    [
        Output('seq-_s-dropdown', 'options'),
        Output('seq-_s-dropdown', 'value')
    ],
    Input(Table.EDIT_BTN.value, 'n_clicks'),
    [
        State('runfile-table', 'selectedRows'),
        State('data-store', 'data')
    ],
    prevent_initial_call=True
)
def seq_source_option(n, selected_rows, data):
    return pf.get_source_and_obsnum_options(n, selected_rows, data)
#
# update the obsnum options based on the source value in the cell for rsr
@app.callback(
    [
        Output('rsr-obsnum-dropdown', 'options'),
        Output('rsr-obsnum-dropdown', 'value'),
        Output('rsr-obsnum-dropdown', 'disabled'),
        Output('rsr-_s-dropdown', 'disabled')
    ],
    Input('rsr-_s-dropdown', 'value'),
    State('runfile-table', 'selectedRows'),
    State('data-store', 'data'),
    prevent_initial_call=True
)
def update_obsnum_options(source, selected_rows, data):
    return pf.get_obsnum_options(source, selected_rows, data)

# update the obsnum options based on the source value in the cell for seq
@app.callback(
    [
        Output('seq-obsnum-dropdown', 'options'),
        Output('seq-obsnum-dropdown', 'value'),
        Output('seq-obsnum-dropdown', 'disabled'),
        Output('seq-_s-dropdown', 'disabled')
    ],
    Input('seq-_s-dropdown', 'value'),
    State('runfile-table', 'selectedRows'),
    State('data-store', 'data'),
    prevent_initial_call=True
)
def update_obsnum_options(source, selected_rows, data):
    return pf.get_obsnum_options(source, selected_rows, data)

#  update all the parameters based on the selected row
rsr_cols = ui.rsr_cols
seq_cols = ui.seq_cols

rsr_outputs = [
    Output(f'{col}-dropdown', 'value', allow_duplicate=True) if col in ['rsr-obsnum', 'rsr-_s']
    #else Output(f'{col}-label', 'children') if col == 'rsr-_io'
    else Output(f'{col}-radio', 'value') if col == 'rsr-admit'
    else Output(f'{col}-input', 'value')
    for col in rsr_cols
]

seq_outputs = [
    Output(f'{col}-dropdown', 'value', allow_duplicate=True) if col in ['seq-obsnum', 'seq-_s']
    else Output(f'{col}-checkbox', 'value') if col == 'seq-pix_list'
    else Output(f'{col}-radio', 'value') if col == 'seq_admit'
    else Output(f'{col}-input', 'value')
    for col in seq_cols
]
# display values for all parameters based on the selected row for rsr
@app.callback(
    rsr_outputs,
    [
        Input(Table.EDIT_BTN.value, 'n_clicks'),
    ],
    [
        State('runfile-table', 'selectedRows'),
    ],
)
def show_edit_layout(n1, selected_rows):
    if not selected_rows:
        return no_update
    selected_row_data = selected_rows[0]
    instrument = selected_row_data.get('_io', '').split('/')[0].upper()
    # Determin parameter list based on instrument
    if 'RSR' not in instrument:
        raise PreventUpdate
    # Dynamically extract values for all rsr_cols
    cols = [col.split('-')[1] for col in rsr_cols]
    values = [selected_row_data.get(col, None) for col in cols]
    # Return the values in the correct order
    return values

# display values for all parameters based on the selected row for seq
@app.callback(
    seq_outputs,
    [
        Input(Table.EDIT_BTN.value, 'n_clicks'),
    ],
    [
        State('runfile-table', 'selectedRows'),
    ],
    prevent_initial_call=True
)
def show_edit_layout(n1, selected_rows):
    if not selected_rows:
        return no_update
    selected_row_data = selected_rows[0]
    instrument = selected_row_data.get('_io', '').split('/')[0].upper()
    # Determin parameter list based on instrument
    if 'SEQ' not in instrument:
        raise PreventUpdate
    # Dynamically extract values for all rsr_cols
    cols = [col.split('-')[1] for col in seq_cols]
    # Handle 'pix_list' safely
    pix_list = selected_row_data.get('pix_list')
    if pix_list is None:
        selected_row_data['pix_list'] = []
    elif isinstance(pix_list, str):
        selected_row_data['pix_list'] = pix_list.split(',')

    values = [
        selected_row_data.get(col, [] if col == 'pix_list' else None)
        if col in selected_row_data else []  # Check if 'col' exists in selected_row_data
        for col in cols
    ]
    # Return the values in the correct order
    return values

#Update the selected row with all parameters for rsr layout
@app.callback(
    Output('runfile-table', 'columnDefs', allow_duplicate=True),
    Output('runfile-table', 'rowData', allow_duplicate=True),
    Input('rsr-single-edit-apply', 'n_clicks'),
    State('runfile-table', 'selectedRows'),
    State('runfile-table', 'rowData'),
    State('data-store', 'data'),
    *[State(f'{col}-dropdown', 'value') if col in ['rsr-obsnum', 'rsr-_s']
      #else State(f'{col}-label', 'value') if col == 'rsr-_io'
      else State(f'{col}-radio', 'value') if col == 'rsr-admit'
      else State(f'{col}-input', 'value')
      for col in rsr_cols],
    prevent_initial_call=True
)
def update_selected_rows_rsr(n_clicks, selected_rows, row_data, data_store, *args):
    if not n_clicks or not selected_rows:
        raise PreventUpdate

    selected_row = selected_rows[0]
    selected_index = selected_row.get('index')
    if selected_index is None:
        raise PreventUpdate
    # Map input values to columns
    # remove rsr to match the table column names
    cols = [col.split('-')[1] for col in rsr_cols]

    updated_values = dict(zip(cols, args))

    updated_values['index'] = selected_index
    # Create a DataFrame from the updated values
    updated_values_df = pd.DataFrame([updated_values])

    # Create a DataFrame from the existing data
    row_data_df = pd.DataFrame(row_data)

    # Align columns between existing data and updated values
    row_data_df = row_data_df.reindex(columns=row_data_df.columns.union(updated_values_df.columns, sort=False), fill_value=None)
    updated_values_df = updated_values_df.reindex(columns=row_data_df.columns, fill_value=None)

    # Update the specific row with new values
    row_data_df.loc[selected_index] = updated_values_df.iloc[0]

    # Normalize data: convert empty strings and NaN to None
    row_data_df = row_data_df.where(pd.notna(row_data_df), None)

    # Identify columns with at least one non-None value
    valid_columns = row_data_df.apply(lambda col: col.notna() & (col != ''), axis=0).any()
    columns_with_values = row_data_df.columns[valid_columns].tolist()
    print('columns_with_values',columns_with_values)

    row_data_df = row_data_df[columns_with_values]

    # Generate column definitions
    column_defs = [
        {
            'headerName': 'instrument' if col == '_io' else 'source' if col == '_s' else col,
            'field': col,
            'filter': True,
            'sortable': True,
            'headerTooltip': f'{col} column',
        }
        for col in columns_with_values
    ]

    # Save the updated runfile if applicable
    runfile = data_store.get('selected_runfile')
    if runfile:
        pf.save_runfile(row_data_df, runfile)

    return column_defs, row_data_df.to_dict('records')
#
# #Update the selected row with all parameters for seq layout
@app.callback(
    Output('runfile-table', 'columnDefs', allow_duplicate=True),
    Output('runfile-table', 'rowData',allow_duplicate=True),
    Input('seq-single-edit-apply', 'n_clicks'),
    State('runfile-table', 'selectedRows'),
    State('runfile-table', 'rowData'),
    State('data-store', 'data'),
    *[State(f'{col}-dropdown', 'value') if col in ['seq-obsnum', 'seq-_s']
      else State(f'{col}-checkbox', 'value') if col == 'seq-pix_list'
      else State(f'{col}-radio', 'value') if col == 'seq-admit'
      else State(f'{col}-input', 'value')
      for col in seq_cols],
    prevent_initial_call=True
)
def update_selected_rows_seq(n_clicks, selected_rows, row_data, data_store, *args):
    if not n_clicks or not selected_rows:
        raise PreventUpdate

    selected_row = selected_rows[0]
    selected_index = selected_row.get('index')
    if selected_index is None:
        raise PreventUpdate
    # Map input values to columns
    # remove seq to match the table column names
    cols = [col.split('-')[1] for col in seq_cols]
    updated_values = dict(zip(cols, args))

    # Sort seq-pix_list
    if 'pix_list' in updated_values:
        if 'pix_list' in updated_values:
            pix_list_value = updated_values['pix_list']
            if isinstance(pix_list_value, list):
                # Convert list items to integers, sort them, and convert back to strings
                sorted_pix_list = sorted(int(x) for x in pix_list_value if x.isdigit())
                updated_values['pix_list'] = ','.join(map(str, sorted_pix_list))
            else:
                updated_values['pix_list'] = None
    print('updated_values',updated_values)
    # Special handling for list-type columns
    for key, value in updated_values.items():
        if isinstance(value, list):
            # Convert list to comma-separated string or None if empty
            updated_values[key] = ','.join(map(str, value)) if value else None
    print('updated_values',updated_values)
    updated_values['index'] = selected_index
    # Create a DataFrame from the updated values
    updated_values_df = pd.DataFrame([updated_values])
    # Create a DataFrame from the existing data
    row_data_df = pd.DataFrame(row_data)

    # Align columns between existing data and updated values
    row_data_df = row_data_df.reindex(columns=row_data_df.columns.union(updated_values_df.columns, sort=False), fill_value=None)
    updated_values_df = updated_values_df.reindex(columns=row_data_df.columns, fill_value=None)

    # Update the specific row with new values
    row_data_df.loc[selected_index] = updated_values_df.iloc[0]

    # Normalize data: convert empty strings and NaN to None
    row_data_df = row_data_df.where(pd.notna(row_data_df), None)

    # Identify columns with at least one non-None value
    valid_columns = row_data_df.apply(lambda col: col.notna() & (col != ''), axis=0).any()
    columns_with_values = row_data_df.columns[valid_columns].tolist()

    row_data_df = row_data_df[columns_with_values]

    # Generate column definitions
    column_defs = [
        {
            'headerName': 'instrument' if col == '_io' else 'source' if col == '_s' else col,
            'field': col,
            'filter': True,
            'sortable': True,
            'headerTooltip': f'{col} column',
        }
        for col in columns_with_values
    ]

    # Save the updated runfile if applicable
    runfile = data_store.get('selected_runfile')
    if runfile:
        pf.save_runfile(row_data_df, runfile)

    return column_defs, row_data_df.to_dict('records')


# in the multi-edit layout, if the apply button is clicked, update the column with the new value for all selected rows
@app.callback(
    Output('runfile-table', 'columnDefs',allow_duplicate=True),
    Output('runfile-table', 'rowData',allow_duplicate=True),
    Input('seq-multi-edit-apply', 'n_clicks'),
    State('runfile-table', 'selectedRows'),
    State('runfile-table', 'rowData'),
    State('data-store', 'data'),
    State('seq-multi-edit-dropdown', 'value'),
    State('seq-multi-edit-input', 'value'),
    prevent_initial_call=True
)
def update_selected_rows(n_clicks, selected_rows, row_data, data_store, column, new_value):
    if not n_clicks or not selected_rows:
        raise PreventUpdate

    # create a dataframe from the rowData
    row_data_df = pd.DataFrame(row_data).copy()

    # Update all selected rows with the new value for the specified column
    selected_indices = [row['index'] for row in selected_rows]

    for index in selected_indices:
        if column not in row_data_df.columns:
            # add the column if it doesn't exist
            row_data_df[column] = None
        row_data_df.at[index, column] = new_value

    # Normalize data: convert empty strings and NaN to None
    row_data_df = row_data_df.where(pd.notna(row_data_df), None)
    valid_columns = row_data_df.apply(lambda col: col.notna() & (col != ''), axis=0).any()
    columns_with_values = row_data_df.columns[valid_columns].tolist()
    row_data_df = row_data_df[columns_with_values]

    # Generate column definitions
    column_defs = [
        {
            'headerName': 'instrument' if col == '_io' else 'source' if col == '_s' else col,
            'field': col,
            'filter': True,
            'sortable': True,
            'headerTooltip': f'{col} column',
        }
        for col in columns_with_values
    ]
    # Save the updated runfile if applicable
    runfile = data_store.get('selected_runfile')
    if runfile:
        pf.save_runfile(row_data_df, runfile)
    return column_defs, row_data_df.to_dict('records')

@app.callback(
    Output('runfile-table', 'columnDefs',allow_duplicate=True),
    Output('runfile-table', 'rowData',allow_duplicate=True),
    Input('rsr-multi-edit-apply', 'n_clicks'),
    State('runfile-table', 'selectedRows'),
    State('runfile-table', 'rowData'),
    State('data-store', 'data'),
    State('rsr-multi-edit-dropdown', 'value'),
    State('rsr-multi-edit-input', 'value'),
    prevent_initial_call=True
)
def update_selected_rows(n_clicks, selected_rows, row_data, data_store, column, new_value):
    if not n_clicks or not selected_rows:
        raise PreventUpdate

    # create a dataframe from the rowData
    row_data_df = pd.DataFrame(row_data).copy()

    # Update all selected rows with the new value for the specified column
    selected_indices = [row['index'] for row in selected_rows]

    for index in selected_indices:
        if column not in row_data_df.columns:
            # add the column if it doesn't exist
            row_data_df[column] = None
        row_data_df.at[index, column] = new_value

    # Normalize data: convert empty strings and NaN to None
    row_data_df = row_data_df.where(pd.notna(row_data_df), None)
    valid_columns = row_data_df.apply(lambda col: col.notna() & (col != ''), axis=0).any()
    columns_with_values = row_data_df.columns[valid_columns].tolist()
    row_data_df = row_data_df[columns_with_values]

    # Generate column definitions
    column_defs = [
        {
            'headerName': 'instrument' if col == '_io' else 'source' if col == '_s' else col,
            'field': col,
            'filter': True,
            'sortable': True,
            'headerTooltip': f'{col} column',
        }
        for col in columns_with_values
    ]
    # Save the updated runfile if applicable
    runfile = data_store.get('selected_runfile')
    if runfile:
        pf.save_runfile(row_data_df, runfile)
    return column_defs, row_data_df.to_dict('records')
#
# if click parameter help button, show the content of the parameter help
@app.callback(
    Output('rsr-parameter-help', 'style'),
    Output('rsr-parameter-help', 'children'),
    Input('para-help-btn', 'n_clicks'),
    State('rsr-parameter-help', 'style'),
    prevent_initial_call=True
)
def show_parameter_help(n_clicks, current_style):
    if not n_clicks:
        raise PreventUpdate

    if current_style == SHOW_STYLE:
        return HIDE_STYLE, ''
    else:
        return SHOW_STYLE, ui.create_parameter_help(instruments[0])

@app.callback(
    Output('seq-parameter-help', 'style'),
    Output('seq-parameter-help', 'children'),
    Input('para-help-btn', 'n_clicks'),
    State('seq-parameter-help', 'style'),
    prevent_initial_call=True
)
def toggle_parameter_help(n_clicks, current_style):
    if not n_clicks:
        raise PreventUpdate

    # Check if the current style indicates that the help section is visible
    if current_style == SHOW_STYLE:
        # Hide the help section
        return HIDE_STYLE, ''
    else:
        # Show the help section
        return SHOW_STYLE, ui.create_parameter_help(instruments[1])