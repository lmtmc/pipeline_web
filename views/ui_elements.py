# slider and checklist cause issue
from dash import dcc, html, Output, State, dash_table, dcc
import dash_bootstrap_components as dbc
from dash_ag_grid import AgGrid
from flask_login import current_user
from functions import project_function as pf
from enum import Enum
from config_loader import load_config
try :
    config = load_config()
except Exception as e:
    print(f"Error loading configuration: {e}")

prefix = config['path']['prefix']
tooltip_style = {
        'fontSize': '1.5rem',         # Adjust font size
        'borderRadius': '5px',        # Optional: Add rounded corners to the tooltip
        'padding': '5px 10px',        # Optional: Add some padding inside the tooltip
    }
class Session(Enum):
    NAME_INPUT = 'session-name'
    MESSAGE = 'session-message'
    SESSION_LIST = 'session-list'
    SAVE_BTN = 'new-session-save'
    MODAL = 'new-session-modal'
    NEW_BTN = 'new-session'
    DEL_BTN = 'del-session'
    CONFIRM_DEL = 'confirm-del-session'
    DEL_ALERT = 'session-del-alert'
    SUBMIT_JOB = 'submit-job'
    RUNFILE_SELECT = 'runfile-select'


class Runfile(Enum):
    CONTENT_TITLE = 'runfile-content-title'
    CONTENT = 'runfile-content'
    DEL_BTN = 'del-runfile'
    CLONE_BTN = 'clone-runfile'
    SAVE_BTN = 'runfile-save'
    VALIDATION_ALERT = 'validation-message'
    CONFIRM_DEL_ALERT = 'confirm-del-runfile'
    SAVE_TABLE_BTN = 'save-table'
    RUN_BTN = 'run-btn'
    SAVE_CLONE_RUNFILE_BTN = 'save-clone-runfile'
    SAVE_CLONE_RUNFILE_STATUS = 'save-clone-runfile-status'
    CLONE_RUNFILE_MODAL = 'clone-runfile-modal'
    CONTENT_DISPLAY = 'parameter'
    NAME_INPUT = 'clone-input'
    STATUS = 'submit-job-status'
    SAVE_TEXT = 'save-text'


class Table(Enum):
    # Add Datatable related IDs here
    DEL_ROW_BTN = 'del-row'
    CLONE_ROW_BTN = 'clone-row'
    EDIT_BTN = 'edit-table'
    CONFIRM_DEL_ROW = 'confirm-del-row'
    OPTION = 'table-option'
    ADD_ROW_BTN = 'add-new-row'
    FILTER_BTN = 'filter-row'

def create_navbar(is_authenticated, username):
    logo_brand = dbc.Row(
        [
            dbc.Col(html.Img(src=f'{prefix}assets/lmt_img.jpg', height='30px'), width='auto'),
            dbc.Col(
                dbc.NavbarBrand("PIPELINE JOB MANAGER", className='ms-2', style={'fontSize': '20px', 'color': 'black'}),
                width='auto'),
        ],
        align='center',
        className='g-0',
    )

    right_content = []

    if is_authenticated:
        right_content.extend([
            dbc.NavItem(dbc.NavLink(f'Current Project: {username}', href="{prefix}project", style={'color': 'black'}),
                        className='me-3'),
            # dbc.NavItem(dbc.NavLink('Job Status', href=f'{prefix}job_status', style={'color': 'black'}), className='me-3'),
            dbc.NavItem(dbc.NavLink('Logout', href=f'{prefix}logout', style={'color':'black'}), className='me-3'),
        ])

    right_content.append(
        dbc.NavItem(
            dbc.NavLink(
                [html.I(className="bi bi-question-circle-fill me-2"), "Help"],
                href=f"{prefix}help",style={'color':'black'}
            )
        )
    )

    navbar = dbc.Navbar(
        dbc.Container(
            [
                logo_brand,
                dbc.Nav(right_content, className="ms-auto", navbar=True),
            ],
            fluid=True,
        ),
        dark=True,
        className='fixed-navbar',
    )

    return navbar

common_columns = ['_s', 'obsnum']

class Parameter(Enum):
    APPLYALL_BTN = 'apply-all'
    SAVE_BTN = 'save-row'
    UPDATE_BTN = 'update-row'
    MODAL = 'draggable-modal'
    TABLE = 'parameter-table'
    DETAIL = 'parameter-detail'
    ACTION = 'parameter-action'
    SOURCE_DROPDOWN = '_s'
    OBSNUM_DROPDOWN = 'obsnum(s)'
    CANCEL_BTN = 'cancel-btn'


class Storage(Enum):
    DATA_STORE = 'data-store'
    URL_LOCATION = 'url_session1'

session_modal = pf.create_modal(
    'Create a new session',
    [
        html.Div(dbc.Input(id=Session.NAME_INPUT.value, placeholder='Enter a session number',
                           min=0, max=100, step=1,
                           type='number'
                           )),
        html.Div(id=Session.MESSAGE.value)
    ],
    html.Button("Save", id=Session.SAVE_BTN.value, className="ml-auto"),
    'new-session-modal'
)

clone_runfile_modal = pf.create_modal('Input the new runfile name',
                                      html.Div([html.Label(current_user.username if current_user else None),
                                                dcc.Input(id=Runfile.NAME_INPUT.value)]),
                                      [
                                          html.Div(id=Runfile.SAVE_CLONE_RUNFILE_STATUS.value,
                                                   style={'display': 'none'}),
                                          html.Button("Clone", id=Runfile.SAVE_CLONE_RUNFILE_BTN.value)
                                      ],
                                      Runfile.CLONE_RUNFILE_MODAL.value)

session_layout = html.Div(
    [
        dbc.Row([
            dbc.Col('SESSION LIST',  id='session-list-title', className='title-link'),
            dbc.Col(
                dbc.ButtonGroup([
                    dbc.Button(html.I(className='fas fa-clone'), id=Session.NEW_BTN.value, outline=True, color='secondary',
                               className='btn-icon'),
                    dbc.Button(html.I(className='fas fa-trash-alt'), id=Session.DEL_BTN.value, outline=True, color='secondary',
                               className='btn-icon'),
                ]), width='auto',
        ),
            dbc.Tooltip("Clone Session", target=Session.NEW_BTN.value, placement='bottom'),
            dbc.Tooltip("Delete Session", target=Session.DEL_BTN.value, placement='bottom'),
            ], className='d-flex justify-content-end'),
        html.Div(
            dbc.Accordion(
                id=Session.SESSION_LIST.value,
                flush=True,
                persistence=True,
                persistence_type="session",
                active_item='session-0',
                style={'overflow': 'auto'}
            ),
            className='session-list-container mb-3',
        ),

        # Session modal and confirm dialog
        session_modal,
        html.Div(
            dcc.ConfirmDialog(id=Session.CONFIRM_DEL.value, message='')
        ),
    ],
    id='session-list-display',
    className='session-list-display'
)

def create_dropdown_parameter(col,multi=False,**kwargs):
    label = col.split("-")[1]
    label = f'{"source" if label == "_s" else label}:'
    return html.Div(
        [
            dbc.Label(label,id=f'{col}-label'),
            dcc.Dropdown(id=f'{col}-dropdown',
                         className='mb-3',
                         options=[],
                         multi=multi,),

        ]
    )
def create_radio_parameter(col, options, tooltip=None,**kwargs):
    return html.Div(
        [
            dbc.Label(f'{col.split("-")[-1]}:', id=f'{col}-label'),
            dcc.RadioItems(id=f'{col}-radio',
                           options=[{'label': 'N/A', 'value': ''}] + [{'label': opt, 'value': opt} for opt in options],
                           className='mb-3',
                           inputStyle={"margin-right": "10px"}
                           ),
            dbc.Tooltip(tooltip, target=f'{col}-label') if tooltip else None
        ]
    )
def create_input_parameter(col, disabled=False, hidden=False, **kwargs):
    label = col.split("-")[1]
    label = f'{"instrument" if label == "_io" else label}:'

    # Define the styles for the input box, label, and container
    input_style = {"backgroundColor": "#e9ecef"} if disabled else {}
    label_style = {}
    container_style = {}

    if hidden:
        # Hide both input, label, and container when hidden=True
        input_style["display"] = "none"
        label_style["display"] = "none"
        container_style["display"] = "none"

    return html.Div(
        [
            dbc.Label(label, style=label_style, id=f'{col}-label'),  # Conditionally hide the label
            dcc.Input(
                id=f'{col}-input',
                type='text',
                disabled=disabled,
                className='mb-3',
                style=input_style  # Apply style conditionally
            ),
        ],
        style=container_style  # Apply container style conditionally
    )

def create_checkbox_parameter(col, options,**kwargs):
    return html.Div(
        [
            dbc.Label(f'{col.split("-")[-1]}:'),
            dcc.Checklist(id=f'{col}-checkbox',
                          className='mb-3',
                          options = options,
                          inline=True),
        ],
    )

# Helper function to dynamically create parameter components
# Centralized function to create parameter components based on type
def create_parameter_component(param_name, param_type, **kwargs):
    component_map = {
        'dropdown': create_dropdown_parameter,
        'input': create_input_parameter,
        'radio': create_radio_parameter,
        'checkbox': create_checkbox_parameter,
    }

    # Check if the parameter type exists in the component_map
    if param_type in component_map:
        # Pass the 'hidden' attribute (along with other kwargs) to the component function
        return dbc.Col(component_map[param_type](param_name, **kwargs), width=kwargs.get('width', 'auto'))
    return None


# Common configurations for all parameters
url = "https://raw.githubusercontent.com/astroumd/lmtoy/master/docs/parameters.txt"
parameters = pf.get_parameter_info(url)
rsr_parameters = parameters['RSR/BS']
sequoia_parameters = parameters['SEQ/MAP']
# Initialize an empty list to hold the Tooltip components
rsr_tooltips, sequoia_tooltips = [], []
# Iterate over all columns in rsr_parameters
for param_name, param_value in rsr_parameters.items():
    # Only create a tooltip if the parameter has a value (i.e., tooltip exists)
    if param_value:  # You can also add a condition like `if param_value.strip() != ''`
        tooltip_id = f'rsr-{param_name}-label'  # ID for the label
        rsr_tooltips.append(
            dbc.Tooltip(param_value, target=tooltip_id, style=tooltip_style, placement='bottom')
        )
for param_name, param_value in sequoia_parameters.items():
    # Only create a tooltip if the parameter has a value (i.e., tooltip exists)
    if param_value:  # You can also add a condition like `if param_value.strip() != ''`
        tooltip_id = f'seq-{param_name}-label'  # ID for the label
        sequoia_tooltips.append(
            dbc.Tooltip(param_value, target=tooltip_id, style=tooltip_style, placement='bottom')
        )
# Wrap the tooltips in a html.Div and store in rsr_parameter_tooltips
rsr_parameter_tooltips = html.Div(rsr_tooltips)
sequoia_parameter_tooltips = html.Div(sequoia_tooltips)

# Initialize an empty list to hold the Tooltip components
tooltips = []

# Common configurations for all parameters
common_configs = [
    {'name': 'obsnum', 'type': 'dropdown', 'multi': True, 'width': 2},
    {'name': '_s', 'type': 'dropdown', 'multi': False, 'width': 2},
    {'name': '_io', 'type': 'input', 'disabled': True}
]

# Configuration for each parameter
rsr_parameter_configs = common_configs + [
    {'name': 'xlines', 'type': 'input'},
    {'name': 'badcb', 'type': 'input'},
    {'name': 'jitter', 'type': 'input'},
    {'name': 'badlags', 'type': 'input'},
    {'name': 'shortlags', 'type': 'input'},
    {'name': 'spike', 'type': 'input'},
    {'name': 'linecheck', 'type': 'input'},
    {'name': 'bandzoom', 'type': 'input'},
    {'name': 'speczoom', 'type': 'input'},
    {'name': 'rthr', 'type': 'input'},
    {'name': 'cthr', 'type': 'input'},
    {'name': 'sgf', 'type': 'input'},
    {'name': 'notch', 'type': 'input'},
    {'name': 'blo', 'type': 'input'},
    {'name': 'bandstats', 'type': 'input'},
    {'name': 'srdp', 'type': 'input'},
    {'name': 'admit', 'type': 'radio', 'options':['0','1']},
    {'name': 'restart', 'type': 'input', 'disabled': True},
]

sequoia_parameter_configs = common_configs + [
    {'name': 'pix_list', 'type': 'checkbox',
     'options':[{'label': str(i), 'value': str(i)} for i in range(16)],'value':[],'width': 2},
    {'name': 'dv', 'type': 'input'},
    {'name': 'dw', 'type': 'input'},
    {'name': 'extent', 'type': 'input'},
    {'name': 'restart', 'type': 'input','disabled': True},
    {'name': 'birdies', 'type': 'input'},
    {'name': 'public', 'type': 'input','disabled': True,'hidden': True},
    {'name': 'qagrade', 'type': 'input', 'disabled': True,'hidden': True},
]

rsr_cols = [f"rsr-{config['name']}" for config in rsr_parameter_configs]
seq_cols = [f"seq-{config['name']}" for config in sequoia_parameter_configs]
# Build layout dynamically
def parameter_layout_single_row(instrument,parameter_configs):

    return html.Div(
    [
        dbc.Row(
            [
                create_parameter_component(
                    f"{instrument}-{config['name']}",
                    config['type'],
                    multi=config.get('multi'),
                    disabled=config.get('disabled'),
                    options=config.get('options'),
                    width=config.get('width')
                )
                for config in parameter_configs
            ]
        ),
        dbc.Row([
                    dbc.Col(dbc.Button('Apply', id=f'{instrument}-single-edit-apply', color='primary', className='mt-3'), width='auto'),
                    dbc.Col(dbc.Button('Cancel', id=f'{instrument}-single-edit-cancel', color='danger', className='mt-3'), width='auto'),
                    ], className='d-flex justify-content-end')
    ], id='parameter-layout'
)

def parameter_layout_multi_row(instrument,parameter_configs):
    return html.Div(
        dbc.Row(
            [
                dbc.Col(dbc.Label('Select a Parameter'), width='auto'),
                dbc.Col(
                    dbc.Select(
                        id=f'{instrument}-multi-edit-dropdown',
                        options=[
                            {'label': config['name'], 'value': config['name']}
                            for config in parameter_configs if config['name'] not in ['obsnum', '_s','_io','restart','public','qagrade']
                        ],
                    ),
                    width='auto',
                ),
                dbc.Col(dbc.Label('New Value'), width='auto'),
                dbc.Col(dcc.Input(id=f'{instrument}-multi-edit-input', type='text'), width='auto'),
                dbc.Col(dbc.Button('Apply', id=f'{instrument}-multi-edit-apply', color='primary'), width='auto'),
                dbc.Col(dbc.Button('Cancel', id=f'{instrument}-multi-edit-cancel', color='danger'), width='auto'),
            ],
            className='d-flex align-items-center mb-5',
            id=f'multi-{instrument}-parameter',
        )
    )

# Wrapper to select appropriate layout based on instrument and row length
def create_instrument_parameter_layout(instrument, row_length, configs):
    if row_length == 1:
        return parameter_layout_single_row(instrument,configs)
    elif row_length > 1:
        return parameter_layout_multi_row(instrument,configs)
    return None

def create_parameter_layout_modal(instrument,row_length,configs):

    return dbc.Modal(
    [
        dbc.ModalHeader(
            [
                dbc.Row([
                    dbc.Col(html.H5('EDIT PARAMETERS'),width='auto'),
                    dbc.Col(dbc.Button('Parameter Help', id='para-help-btn',))],className='d-flex align-items-center'),
        ]
        ),
        dbc.ModalBody(
            html.Div([
                html.Div(id=f'{instrument}-parameter-help', style={'display': 'none'}),
                create_instrument_parameter_layout(instrument, row_length, configs),
                rsr_parameter_tooltips,
                sequoia_parameter_tooltips,
              ],id='layouts'),),
    ],id='parameter-edit-modal',
        size='xl',
        centered=True,
        scrollable=True,
        backdrop='static'
    )

runfile_layout = html.Div(
    [
        dbc.Card(
            [
                dbc.CardHeader(
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Label(id=Runfile.CONTENT_TITLE.value),
                                className='d-flex align-items-center',  # Center vertically
                                # width=8
                                ),
                            dbc.Col(
                                dbc.ButtonGroup(
                                    [
                                        html.Div(dbc.Button("Submit Job", id=Runfile.RUN_BTN.value, color='primary',
                                   className='me-2'), id='runfile-run-btn'),  # Using me-2 instead of margin-right
                                        html.Div(dbc.Button("Check Status", id="check-status-btn", color='secondary',
                                   className='me-2'), id='runfile-check-status-btn'),
                                        dbc.Button(
                                            "View Result",
                                            id='view-result-link',
                                            color='success',
                                            n_clicks=0  # Add this explicitly
                                        ),
                    ], size='md'),
                    className='d-flex justify-content-end',  # Align buttons to the right
                    width='auto'
                ),

            ], className='d-flex justify-content-between align-items-center')
                ),
                dbc.CardBody([
            # ButtonGroup in the same row, right next to the label
                dbc.Row([
                dbc.Col(
                    html.Div(
                        dbc.ButtonGroup([
                            dbc.Button([html.I(className='fas fa-edit'), " Edit"], id=Table.EDIT_BTN.value,
                                       outline=False, color='primary', className='btn-icon btn-noticeable'),
                            dbc.Button([html.I(className='fas fa-trash-alt'), " Delete"], id=Table.DEL_ROW_BTN.value,
                                       outline=False, color='danger', className='btn-icon btn-noticeable'),

                            dbc.Button([html.I(className='fas fa-clone'), " Clone"], id=Table.CLONE_ROW_BTN.value,
                                       outline=False, color='success', className='btn-icon btn-noticeable'),

                        ], className='d-flex justify-content-center mt-3'),
                        id=Table.OPTION.value
                    ),
                    width='auto',
                    className='d-flex justify-content-start'
                ),
            dbc.Tooltip("Edit Row(s)", target=Table.EDIT_BTN.value, placement='bottom'),
            dbc.Tooltip("Delete Row(s)", target=Table.DEL_ROW_BTN.value, placement='bottom'),
            dbc.Tooltip("Clone Row(s)", target=Table.CLONE_ROW_BTN.value, placement='bottom')
            ]),
                html.Div(
                    [
                        AgGrid(
                        id='runfile-table',
                        rowData=[],
                        defaultColDef={
                            "filter": True,
                            "resizable": True,
                            "sortable": True,
                            "checkboxSelection": {
                                "valueGetter": 'params.column == params.api.getAllDisplayedColumns()[0]'
                            },
                            "headerCheckboxSelection": {
                                "valueGetter": 'params.column == params.api.getAllDisplayedColumns()[0]'
                            }
                        },
                        dashGridOptions={
                            "rowSelection": "multiple",
                            "rowMultiSelectWithClick": True,
                            "suppressRowClickSelection": True,
                            'enableBrowserTooltips': True,
                        },
                        className="ag-theme-alpine",
                        style={'height': '45vh'}
                ),
                dbc.Button('Save Filtered Data', id='save-filter-btn', color='primary', className='mt-3'),
                dcc.ConfirmDialog(id='save-filter-alert', message='Are you sure you want to save the filtered data?'),
                ])
                ]),
            dcc.ConfirmDialog(id=Table.CONFIRM_DEL_ROW.value, message=''),
            dcc.ConfirmDialog(id=Runfile.CONFIRM_DEL_ALERT.value, message=''),

    ]),
        dbc.Modal([
            dbc.ModalHeader(
                dbc.ModalTitle("Submit Job to UNITY", className="text-primary"),
                close_button=True
            ),
            dbc.ModalBody([
                html.Div([
                    html.H5(className="mb-3 text-dark small-font", id="submit-job-confirm-text"),
                    dbc.Form([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label(
                                    "Email Notification",
                                    className="text-muted mb-2"
                                ),
                                dbc.Input(
                                    id='email-input',
                                    placeholder='your.email@example.com',
                                    type='email',
                                    className="mb-3",
                                ),
                                dbc.FormText(
                                    "You'll receive updates about your job status at this email address",
                                    color="secondary"
                                )
                            ])
                        ])
                    ])
                ]),
            html.Div(id=Session.SUBMIT_JOB.value,className='submit-job-message'),
            ],

            ),
            dbc.ModalFooter([
                dbc.Button(
                    "Cancel",
                    id="cancel-submit-job",
                    color="secondary",
                    className="me-2"
                ),
                dbc.Button(
                    [
                        html.I(className="fas fa-paper-plane me-2"),
                        "Submit Job"
                    ],
                    id='confirm-submit-job-btn',
                    color='primary'
                ),
            ])
        ],
        id='confirm-submit-job',
        is_open=False,
        size="md",
        backdrop="static",
        centered=True
        )
        ],
    id=Runfile.CONTENT_DISPLAY.value,
    className='runfile-content-container')

job_status_layout = html.Div(
    [

        html.Div(id="slurm-job-status-output", className="mt-4")
],)

def create_parameter_help(instrument):
    if instrument == 'rsr':
        # Create a list to hold all the help documentation entries
        help_entries = []

        # Iterate over the rsr_parameters and create list items dynamically
        for param_name, param_description in rsr_parameters.items():
            # If there is a description for the parameter (not empty or None)
            if param_description:
                help_entries.append(html.Li(f"{param_name}: {param_description}"))
            else:
                help_entries.append(html.Li(f"{param_name}: No description available."))

        # Return the help section with dynamically generated list items
        return html.Div(
            html.P([
                html.Ul(help_entries)
            ]),
            style={'fontSize': '1.5rem', 'max-height': '200px', 'overflow-y': 'auto'}
        )
    elif instrument == 'seq':
        # Create a list to hold all the help documentation entries
        help_entries = []

        # Iterate over the sequoia_parameters and create list items dynamically
        for param_name, param_description in sequoia_parameters.items():
            # If there is a description for the parameter (not empty or None)
            if param_description:
                help_entries.append(html.Li(f"{param_name}: {param_description}"))
            else:
                help_entries.append(html.Li(f"{param_name}: No description available."))

        # Return the help section with dynamically generated list items
        return html.Div(
            html.P([
                html.Ul(help_entries)
            ]),
            style={'fontSize': '1.5rem', 'max-height': '200px', 'overflow-y': 'auto'}
        )
    else:
        return html.P("No help available for the selected instrument.")
