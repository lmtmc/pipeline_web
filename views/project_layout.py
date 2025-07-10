#TODO Test 'lmtoy_clone_session.sh'
#TODO Test 'lmtoy_sbatch2.sh'
#TODO monitor the slurm job status. When all finished make summary and send email to the user
#TODO test the link of the view result button
import logging
import os
from threading import Thread
import pandas as pd
from dash import html, Input, Output, State, ALL, ctx, no_update, dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from flask_login import current_user
from my_server import app
from utils import project_function as pf, repo_utils as ru
from views import ui_elements as ui
from views.ui_elements import Session, Runfile, Table
from config_loader import load_config
import math

try :
    config = load_config()
except Exception as e:
    print(f"Error loading configuration: {e}")

prefix = config['path']['prefix']
default_work_lmt = config['path']['work_lmt']
default_lmtoy_run = os.path.join(default_work_lmt, 'lmtoy_run')
default_session_prefix = os.path.join(default_work_lmt, 'lmtoy_run/lmtoy_')
init_session = config['session']['init_session']

# Constants

HIDE_STYLE = {'display': 'none'}
SHOW_STYLE = {'display': 'block'}

layout = html.Div(
    [
        dbc.Row([
            dbc.Col([
                ui.session_layout,
                html.Br(),
            ],width=2, className='h-100'),
            dbc.Col(ui.runfile_layout, width=10, className='h-100'),
        ], className='mb-3 h-100'),
        ui.job_status_layout,
        html.Div(id='parameter-edit-selector'),
        dcc.Location(id='result-location', refresh=True),
     ],
     className='h-100'
)

# Hide the Delete Session for the default session and hide the clone button for other sessions
@app.callback(
    [
        Output(Session.DEL_BTN.value, 'style'),
        Output(Session.NEW_BTN.value, 'style'),
    ],
    Input(Session.SESSION_LIST.value, 'active_item'),
)
def default_session(active_session):
    if active_session is None:
        # Hide all buttons if no session is selected
        print(f'No active session selected: {active_session}')
        return HIDE_STYLE, HIDE_STYLE

    if active_session == init_session:
        # Hide delete buttons and show only the new session button for the default session
        print(f'Active session is default session: {active_session}')
        return HIDE_STYLE, SHOW_STYLE
    print(f'Active session is not default session: {active_session}')
    return SHOW_STYLE, HIDE_STYLE


# update session list when modifying session
@app.callback(
    [
        Output(Session.SESSION_LIST.value, 'children'),
        Output(Session.MODAL.value, 'is_open'),
        Output(Session.MESSAGE.value, 'children'),
        Output(Session.SESSION_LIST.value, 'active_item'),
    ],
    [
        Input(Session.NEW_BTN.value, 'n_clicks'),
        Input(Session.SAVE_BTN.value, 'n_clicks'),
        Input(Session.CONFIRM_DEL.value, 'submit_n_clicks'),

    ],
    [
        State(Session.SESSION_LIST.value, 'active_item'),
        State(Session.NAME_INPUT.value, 'value'),
        State('data-store', 'data')
    ],
)
def update_session_display(n1, n2, n3, active_session, name, data):
    try:
        triggered_id = ctx.triggered_id

        if not pf.check_user_exists():
            return [], False, "User is not authenticated", no_update

        # Use data['pid'] for both admin and regular users
        pid_path = os.path.join(default_work_lmt, data['pid'])

        try:
            os.makedirs(pid_path, exist_ok=True)
        except OSError as e:
            error_message = f"Failed to create directory {pid_path}: {str(e)}"
            logging.error(error_message)
            return [], False, error_message, None

        modal_open, message = no_update, ''
        session_list = pf.get_session_list(init_session, pid_path, data['pid'])
        # Initialize active session if none is selected
        if not active_session and session_list:
            active_session = init_session

        if triggered_id == Session.NEW_BTN.value:
            modal_open = True

        # handle save session
        elif triggered_id == Session.SAVE_BTN.value:
            if not name:
                message = "Please enter a session name."
            else:
                message, modal_open = pf.save_session(pid_path, name)
                if "Successfully" in message:
                    session_list = pf.get_session_list(init_session, pid_path, data['pid'])
                    active_session = f'Session-{name}'
                else:
                    active_session = active_session

        # handle delete session
        elif triggered_id == Session.CONFIRM_DEL.value:
            message = pf.delete_session(pid_path, active_session)
            active_session = None if "Successfully" in message else active_session
            session_list = pf.get_session_list(init_session, pid_path, data['pid'])

        if triggered_id in [Session.SAVE_BTN.value, Session.CONFIRM_DEL.value]:
            active_session = init_session if active_session is None else active_session

        return session_list, modal_open, message, active_session

    except Exception as e:
        session_list = pf.get_session_list(init_session, pid_path, data['pid'])
        logging.error(f"Error in update_session_display: {str(e)}")
        return session_list, False, f"An error occurred: {str(e)}", None

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
# if Session-0 is clicked, not shown save, sumbit job and check status button, runfile table not selectable
@app.callback(
    [
        Output('runfile-save-btn', 'style'),
        Output('check-status-btn', 'style'),
        Output('runfile-run-btn', 'style'),
        Output('runfile-table', 'dashGridOptions'),
        Output('runfile-table', 'defaultColDef'),
    ],
    Input(Session.SESSION_LIST.value, 'active_item'),
)
def show_runfile_buttons(active_session):
    if active_session == init_session:
        dashGridOptions = {
            "rowSelection": None,  # No row selection allowed
            "suppressRowClickSelection": True,
            'enableBrowserTooltips': True,
            'skipHeaderOnAutoSize': False,
        }
        defaultColDef = {
            "filter": True,
            "resizable": True,
            "sortable": True,
        }
        return HIDE_STYLE, HIDE_STYLE, HIDE_STYLE, dashGridOptions, defaultColDef
    else:
        # Enable selection and show checkboxes
        dashGridOptions = {
            "rowSelection": "multiple",
            "rowMultiSelectWithClick": True,
            "suppressRowClickSelection": False,
            'enableBrowserTooltips': True,
            'skipHeaderOnAutoSize': False,
        }
        defaultColDef = {
            "filter": True,
            "resizable": True,
            "sortable": True,
        }

    return SHOW_STYLE, SHOW_STYLE, SHOW_STYLE,dashGridOptions, defaultColDef

# if click the view result button go to the url to view the result
@app.callback(
    Output('result-location', 'href'),  # Keep the current URL
    Input('view-result-btn', 'n_clicks'),
    State(Session.SESSION_LIST.value, 'active_item'),
    State('data-store', 'data'),
    prevent_initial_call=True
)
def view_result(n_clicks, active_session, data):
    if not active_session:
        return no_update, no_update
    print(f'Active session for view_result: {active_session}')
    try:
        pf.make_summary(data['pid'], active_session)
        result_url = pf.generate_result_url(data['pid'], active_session)

        # Return both the URL for the hidden div and keep current location
        return result_url
    except Exception as e:
        logging.error(f"Error in view_result: {str(e)}")
        logging.error(f"Error in view_result: {str(e)}")
        return no_update

# submit job
# if submit job is clicked show confirm submit modal, if cancel submit job is clicked hide the modal
@app.callback(
    Output('confirm-submit-job', 'is_open', allow_duplicate=True),
    [
        Input('runfile-run-btn', 'n_clicks'),
        Input('cancel-submit-job', 'n_clicks'),
        Input('confirm-submit-job-btn', 'n_clicks')
    ],
    prevent_initial_call=True
)
def show_confirm_submit(n_clicks, cancel_clicks, confirm_clicks):
    if not ctx.triggered:
        raise PreventUpdate
        
    triggered_id = ctx.triggered_id
    
    if triggered_id == 'runfile-run-btn':
        return True
    elif triggered_id in ['cancel-submit-job', 'confirm-submit-job-btn']:
        return False
        
    return False

@app.callback(
    [
        Output(Session.SUBMIT_JOB.value, 'children'),
        Output('confirm-submit-job', 'is_open')
    ],
    Input('confirm-submit-job-btn', 'n_clicks'),
    [
        State({'type': 'runfile-radio', 'index': ALL}, 'value'),
        State(Session.SESSION_LIST.value, 'active_item'),
        State('email-input', 'value'),
        State('data-store', 'data')
    ],
    prevent_initial_call=True
)
def submit_job(n_clicks, selected_runfile, session, email, data_store):
    if not n_clicks:
        raise PreventUpdate
        
    if not ctx.triggered:
        raise PreventUpdate
        
    triggered_id = ctx.triggered_id
    if triggered_id != 'confirm-submit-job-btn':
        raise PreventUpdate
        
    selected_runfile = next((value for value in selected_runfile if value), None)
    if not selected_runfile:
        return dbc.Alert("No runfile selected.", color="warning", dismissable=True), True
        
    if not session:
        return dbc.Alert("No session selected.", color="warning", dismissable=True), True
        
    runfile_name = os.path.basename(selected_runfile)
    if not email:
        return dbc.Alert("Please enter an email address to receive job submission notifications.", color="warning", dismissable=True), True
        
    # Validate email format
    if not pf.is_valid_email(email):
        return dbc.Alert("Please enter a valid email address.", color="warning", dismissable=True), True
        
    # Prepare confirmation message
    confirmation_message = dbc.Alert(
        [
            html.Strong(f"Job Submitted: "),
            f"Runfile '{runfile_name}' for {session} is being processed. ",
            html.Br(),
            f"Notification will be sent to {email} when complete."
        ],
        color="success",
        dismissable=True
    )
    
    # Submit the job
    try:
        Thread(target=pf.process_job_submission, args=(data_store['pid'], selected_runfile, session, email)).start()
    except Exception as e:
        logging.error(f"Error submitting job: {str(e)}")
        return dbc.Alert(f"Error submitting job: {str(e)}", color="danger", dismissable=True), True
        
    return confirmation_message, True

@app.callback(
    Output("slurm-job-status-output", "children", allow_duplicate=True),
    Input("check-status-btn", "n_clicks"),
    State('data-store', 'data'),
    prevent_initial_call=True,
)
def update_job_status(n_clicks, data):
    selected_runfile= data.get('selected_runfile')
    if not selected_runfile:
        return dbc.Alert("No runfile selected.", color="info", dismissable=True)
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

# display selected runfile
@app.callback(
    [
        Output(Runfile.CONTENT_TITLE.value, 'children',allow_duplicate=True),
        Output(Runfile.CONTENT_DISPLAY.value, 'style', allow_duplicate=True),
        Output('runfile-table', 'rowData', allow_duplicate=True),
        Output('runfile-table', 'columnDefs', allow_duplicate=True),
        Output('data-store', 'data', allow_duplicate=True),
        #Output('submit-job-confirm-text', 'children'),
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
            'checkboxSelection': c == 'index',
            'headerCheckboxSelection': c == 'index',
            'width': 150,  # Set a default width for columns
            'resizable': True,  # Allow column resizing
            'minWidth': 100,  # Minimum column width
            'maxWidth': 300,  # Maximum column width
        } for c in runfile_data.columns
    ]

    # Replace NaN values in the data
    cleaned_row_data = []
    for row in row_data:
        cleaned_row = {key: (None if isinstance(value, float) and math.isnan(value) else value) for key, value in
                       row.items()}
        cleaned_row_data.append(cleaned_row)

    if ctx.triggered_id == Runfile.CONFIRM_DEL_ALERT.value:
        pf.del_runfile(current_runfile)
    data_store['selected_runfile'] = current_runfile
    return runfile_title,SHOW_STYLE, cleaned_row_data, column_defs,data_store

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
    else Output(f'{col}-radio', 'value') if col == 'seq_admit' or col == 'seq-pix_action'
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
    prevent_initial_call=True
)
def show_edit_layout(n1, selected_rows):
    if not n1:
        raise PreventUpdate
    if not selected_rows:
        return no_update
    selected_row_data = selected_rows[0]
    instrument = selected_row_data.get('_io', '').split('/')[0].upper()

    # Determin parameter list based on instrument
    if 'RSR' not in instrument:
        raise PreventUpdate
    # Dynamically extract values for all rsr_cols
    cols = [col.split('-')[1] for col in rsr_cols]

    # Handle 'obsnum' safely
    # Create dropdown for obsnum values
    # if obsnum is a string, split it by comma if it is a list get the first element
    # Modify the obsnum_values processing:
    obsnum_values = selected_row_data.get('obsnum', '')

    if obsnum_values is None:
        obsnum_values = []
    elif isinstance(obsnum_values, str):
        obsnum_values = [v.strip() for v in obsnum_values.split(',') if v.strip()]
    elif isinstance(obsnum_values, list):
        obsnum_values = [str(v).strip() for v in obsnum_values]

    other_values = [
        selected_row_data.get(col, None) for col in cols if col != 'obsnum'
    ]
    values = [obsnum_values] + other_values
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
    # if pix_list is None:
    #     selected_row_data['pix_list'] = []
    # elif isinstance(pix_list, str):
    #     selected_row_data['pix_list'] = pix_list.split(',')
    if not pix_list or (isinstance(pix_list, str) and pix_list.strip() == ''):
        pix_action = 'N/A'
        pix_list_values = []
    elif isinstance(pix_list, str):
        if pix_list.startswith('-'):
            pix_action = 'Exclude'
            pix_list_values = pix_list[1:].split(',') if pix_list[1:] else []
        else:
            pix_action = 'Add'
            pix_list_values = pix_list.split(',') if pix_list else []
    elif isinstance(pix_list, list):
        pix_action = 'Add'
        pix_list_values = pix_list
    else:
        pix_action = 'N/A'
        pix_list_values = []

    values = []
    for col in cols:
        if col == 'pix_action':
            values.append(pix_action)
        elif col == 'pix_list':
            values.append(pix_list_values)
        else:
            # For other columns, get the value directly
            values.append(selected_row_data.get(col, None))
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

    row_data_df = row_data_df[columns_with_values]

    # Generate column definitions
    column_defs = [
        {
            'headerName': 'instrument' if col == '_io' else 'source' if col == '_s' else col,
            'field': col,
            'filter': True,
            'sortable': True,
            'headerTooltip': f'{col} column',
            'checkboxSelection': col == 'index',
            'headerCheckboxSelection': col == 'index',
        }
        for col in columns_with_values
    ]

    # Save the updated runfile if applicable
    runfile = data_store.get('selected_runfile')
    if runfile:
        pf.save_runfile(row_data_df, runfile)

    row_data = row_data_df.to_dict('records')
    for row in row_data:
        if isinstance(row['obsnum'], list):
            row['obsnum'] = ','.join(row['obsnum'])

    return column_defs, row_data
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

    # # Sort seq-pix_list
    # if 'pix_list' in updated_values:
    #     if 'pix_list' in updated_values:
    #         pix_list_value = updated_values['pix_list']
    #         if isinstance(pix_list_value, list):
    #             # Convert list items to integers, sort them, and convert back to strings
    #             sorted_pix_list = sorted(int(x) for x in pix_list_value if x.isdigit())
    #             updated_values['pix_list'] = ','.join(map(str, sorted_pix_list))
    #         else:
    #             updated_values['pix_list'] = None
    # handle seq-pix_list and pix_action
    pix_action = updated_values.get('pix_action', 'N/A')
    pix_list_value = updated_values.get('pix_list', [])
    if pix_action == 'Exclude' and pix_list_value:
        pix_list_str='-'+','.join(str(x) for x in sorted(map(int, pix_list_value ))))
    elif pix_action == 'Add' and pix_list_value:
        pix_list_str=','.join(str(x) for x in sorted(map(int, pix_list_value)))
    else:
        pix_list_str = ''
    updated_values['pix_list'] = pix_list_str

    # Remove pix_action from updated values
    updated_values.pop('pix_action', None)

    # Special handling for list-type columns
    for key, value in updated_values.items():
        if isinstance(value, list):
            # Convert list to comma-separated string or None if empty
            updated_values[key] = ','.join(map(str, value)) if value else None

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
            'headerName': 'instrument' if col == '_io' else 'source' if col == '_s' else str(col),
            'field': str(col),
            'filter': True,
            'sortable': True,
            'headerTooltip': f'{col} column',
            'checkboxSelection': col == 'index',
            'headerCheckboxSelection': col == 'index',
        }
        for col in columns_with_values if str(col)!='length'
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
            'checkboxSelection': col == 'index',
            'headerCheckboxSelection': col == 'index',
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
            'checkboxSelection': col == 'index',
            'headerCheckboxSelection': col == 'index',
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

@app.callback(
    [
        Output('runfile-table', 'rowData',allow_duplicate=True),
        Output('runfile-table', 'columnDefs',allow_duplicate=True),
        Output('runfile-content-title', 'children',allow_duplicate=True),
        Output(Runfile.CONTENT_DISPLAY.value, 'style'),
    ],
    [
        Input(Session.SESSION_LIST.value, 'active_item'),
        Input({'type': 'runfile-radio', 'index': ALL}, 'value'),
    ],
    State('data-store', 'data'),
)
def update_runfile_display(active_session, selected_runfile, data):
    if not active_session:
        return [], [], '', HIDE_STYLE

    try:
        # Get the selected runfile
        selected_runfile = next((value for value in selected_runfile if value), None)
        
        if not selected_runfile:
            return [], [], '', HIDE_STYLE

        # Get runfile data
        runfile_data, runfile_content = pf.df_runfile(selected_runfile)
        
        if runfile_data.empty:
            return [], [], '', HIDE_STYLE

        # Generate column definitions
        column_defs = [
            {
                'headerName': 'instrument' if col == '_io' else 'source' if col == '_s' else col,
                'field': col,
                'filter': True,
                'sortable': True,
                'headerTooltip': f'{col} column',
                'checkboxSelection': col == 'index',
                'headerCheckboxSelection': col == 'index',
                'width': 150,
                'resizable': True,
                'minWidth': 100,
                'maxWidth': 300,
            }
            for col in runfile_data.columns
        ]

        # Convert DataFrame to records
        row_data = runfile_data.to_dict('records')
        
        # Get runfile title
        runfile_title = pf.get_runfile_title(selected_runfile, active_session)

        return row_data, column_defs, runfile_title, SHOW_STYLE

    except Exception as e:
        logging.error(f"Error updating runfile display: {str(e)}")
        return [], [], '', HIDE_STYLE

@app.callback(
    [
        Output('runfile-table', 'rowData',allow_duplicate=True),
        Output('save-filter-alert','displayed')
    ],
    [
        Input('runfile-save-btn', 'n_clicks'),
        Input('save-filter-alert', 'submit_n_clicks'),
        Input('save-filter-alert', 'cancel_n_clicks')
    ],
    [
        State('runfile-table', 'rowData'),
        State('runfile-table', 'filterModel'),
        State('data-store', 'data')
    ],
    prevent_initial_call=True
)
def save_filter(save_clicks, confirm_clicks, cancel_clicks, row_data, filter_model, data_store):
    if not ctx.triggered:
        raise PreventUpdate
        
    triggered_id = ctx.triggered_id
    
    if triggered_id == 'runfile-save-btn':
        # Show the confirmation dialog when save button is clicked
        return no_update, True
        
    elif triggered_id == 'save-filter-alert':
        if not confirm_clicks:
            return no_update, False
            
        # Convert the row data and data store to DataFrame
        df = pd.DataFrame(row_data)
        # Apply the filter model to the DataFrame
        if filter_model:
            for column, filter_details in filter_model.items():
                if column not in df.columns:
                    print(f"Column '{column}' not found in DataFrame.")
                    continue

                if filter_details['filterType'] == 'text':
                    filter_value = filter_details['filter']
                    filter_type = filter_details.get('type', 'contains')  # Default to 'contains'

                    if filter_type == 'contains':
                        df = df[df[column].astype(str).str.contains(filter_value, case=False, na=False)]
                    elif filter_type == 'equals':
                        df = df[df[column] == filter_value]
                    # Add more filter types here as needed

                elif filter_details['filterType'] == 'number':
                    filter_value = filter_details['filter']
                    filter_type = filter_details.get('type', 'equals')  # Default to 'equals'

                    if filter_type == 'equals':
                        df = df[df[column] == filter_value]
                    elif filter_type == 'greaterThan':
                        df = df[df[column] > filter_value]
                    elif filter_type == 'lessThan':
                        df = df[df[column] < filter_value]
                    # Add more filter types here as needed

                elif filter_details['filterType'] == 'set':
                    filter_values = filter_details['values']
                    df = df[df[column].isin(filter_values)]
                    
        # Save the filtered data
        filtered_data = df.to_dict('records')
        print(f"Filtered data saved to {data_store['selected_runfile']}")
        pf.save_runfile(df, data_store['selected_runfile'])
        return filtered_data, False
        
    elif triggered_id == 'save-filter-alert.cancel_n_clicks':
        return no_update, False
        
    return no_update, no_update

# # if there is job running disable the sumbit job button
# @app.callback(
#     Output(Runfile.RUN_BTN.value, 'disabled'),
#     Input({'type': 'runfile-radio', 'index': ALL}, 'value'),
#     prevent_initial_call=True
# )
# def disable_submit_job_button(selected_runfile):
#     selected_runfile = next((value for value in selected_runfile if value), None)
#     if not selected_runfile:
#         return True
#     status, finished = pf.check_runfile_job_status(selected_runfile)
#     # if the job is running, disable the submit job button
#     if not finished:
#         return True
#     return False

@app.callback(
    Output('runfile-notes', 'value'),
    Input({'type': 'runfile-radio', 'index': ALL}, 'value'),
    State('data-store', 'data'),
    prevent_initial_call=True
)
def load_runfile_notes(selected_runfile, data):
    if not selected_runfile:
        raise PreventUpdate
        
    current_runfile = next((value for value in selected_runfile if value), None)
    if not current_runfile:
        return ''
        
    # Try to load notes from the notes file
    notes_file = f"{current_runfile}.notes"
    try:
        if os.path.exists(notes_file):
            with open(notes_file, 'r') as f:
                return f.read()
    except Exception as e:
        logging.error(f"Error loading runfile notes: {str(e)}")
    return ''

@app.callback(
    Output('runfile-notes', 'value', allow_duplicate=True),
    Input('runfile-notes', 'value'),
    State({'type': 'runfile-radio', 'index': ALL}, 'value'),
    prevent_initial_call=True
)
def save_runfile_notes(notes, selected_runfile):
    if not selected_runfile:
        raise PreventUpdate
        
    current_runfile = next((value for value in selected_runfile if value), None)
    if not current_runfile:
        return ''
        
    # Save notes to the notes file
    notes_file = f"{current_runfile}.notes"
    try:
        with open(notes_file, 'w') as f:
            f.write(notes if notes else '')
    except Exception as e:
        logging.error(f"Error saving runfile notes: {str(e)}")
        
    return notes

# Add a callback to save notes when the runfile is saved
@app.callback(
    Output('runfile-notes', 'value', allow_duplicate=True),
    Input('runfile-table', 'rowData'),
    State({'type': 'runfile-radio', 'index': ALL}, 'value'),
    State('runfile-notes', 'value'),
    prevent_initial_call=True
)
def save_notes_on_runfile_save(row_data, selected_runfile, notes):
    if not selected_runfile:
        raise PreventUpdate
        
    current_runfile = next((value for value in selected_runfile if value), None)
    if not current_runfile:
        return ''
        
    # Save notes to the notes file
    notes_file = f"{current_runfile}.notes"
    try:
        with open(notes_file, 'w') as f:
            f.write(notes if notes else '')
    except Exception as e:
        logging.error(f"Error saving runfile notes: {str(e)}")
        
    return notes

# Add callback for git pull button
@app.callback(
    Output('git-pull-status', 'children'),
    [Input('git-pull-btn', 'n_clicks'),
     Input('project-updates-btn', 'n_clicks')],
    State('data-store', 'data'),
    prevent_initial_call=True
)
def handle_git_pull(git_pull_clicks, project_updates_clicks, data):
    try:
        pid = data.get('pid')
        if not pid:
            raise ValueError("Project ID (pid) not found in data store")

        repo_name = f'lmtoy_{pid}'
        triggered_id = ctx.triggered_id

        if triggered_id == 'git-pull-btn':
            # Execute git pull
            success, message = ru.update_single_repo(repo_name, default_lmtoy_run)
            if not success:
                return dbc.Alert(
                    [
                        html.I(className="fas fa-exclamation-circle me-2"),
                        "Failed to pull latest changes:",
                        html.Br(),
                        message
                    ],
                    color="danger",
                    dismissable=True
                )
            return dbc.Alert(
                [
                    html.I(className="fas fa-check-circle me-2"),
                    "Successfully pulled latest changes",
                    html.Br(),
                    message
                ],
                color="success",
                dismissable=True
            )
        else:  # project-updates-btn
            # Check repository status
            success, status_msg = ru.get_single_repo_status(repo_name)
            if not success:
                return dbc.Alert(
                    [
                        html.I(className="fas fa-exclamation-circle me-2"),
                        "Failed to check project status:",
                        html.Br(),
                        status_msg
                    ],
                    color="danger",
                    dismissable=True
                )

            color = "success" if status_msg == "Up to date" else "warning"
            icon = "fas fa-check-circle" if status_msg == "Up to date" else "fas fa-info-circle"
            message = "Project is already up to date." if status_msg == "Up to date" else "Project may need updates."

            return dbc.Alert(
                [
                    html.I(className=f"{icon} me-2"),
                    message,
                    html.Br(),
                    status_msg
                ],
                color=color,
                dismissable=True
            )

    except Exception as e:
        logging.error(f"Error in git operations: {str(e)}")
        return dbc.Alert(
            [
                html.I(className="fas fa-exclamation-circle me-2"),
                "Error performing git operation:",
                html.Br(),
                str(e)
            ],
            color="danger",
            dismissable=True
        )

