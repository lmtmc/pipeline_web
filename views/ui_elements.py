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
            className='session-list-container',
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
            dbc.Label(label),
            dcc.Dropdown(id=f'{col}-dropdown',
                         className='mb-3',
                         options=[],
                         multi=multi,),
        ]
    )
def create_radio_parameter(col, options, **kwargs):
    return html.Div(
        [
            dbc.Label(f'{col.split("-")[-1]}:'),
            dcc.RadioItems(id=f'{col}-radio',
                           options=[{'label': opt, 'value': opt} for opt in options],
                           className='mb-3',
                           inputStyle={"margin-right": "10px"}),
        ]
    )
def create_input_parameter(col, disabled=False,**kwargs):

    label = col.split("-")[1]

    label = f'{"instrument" if label == "_io" else label}:'

    return html.Div(
        [
            dbc.Label(label),
            dcc.Input(id=f'{col}-input',
                      type='text',
                      disabled=disabled,
                      className='mb-3'),
        ]
    )
def create_textarea_parameter(col, **kwargs):
    return html.Div(
        [
            dbc.Label(f'{col.split("-")[-1]}:'),
            dcc.Textarea(id=f'{col}-textarea', placeholder=f'Enter {col}', className='mb-3'),
        ]
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

def create_label(col, **kwargs):

    return html.Div(
        [
            dbc.Label(f'{col.split("-")[-1]}:'),
            html.Div(id=f'{col}-label', className='mb-3'),
        ]
    )
# Helper function to dynamically create parameter components
# Centralized function to create parameter components based on type
def create_parameter_component(param_name, param_type, **kwargs):
    component_map = {
        'dropdown': create_dropdown_parameter,
        'input': create_input_parameter,
        'radio': create_radio_parameter,
        'textarea': create_textarea_parameter,
        'checkbox': create_checkbox_parameter,
        'label': create_label,
    }

    if param_type in component_map:
        return dbc.Col(component_map[param_type](param_name, **kwargs), width=kwargs.get('width', 'auto'))
    return None

# Configuration for each parameter
rsr_parameter_configs = [
    {'name': 'obsnum', 'type': 'dropdown', 'multi': True, 'width': 2},
    {'name': '_s', 'type': 'dropdown', 'multi': False, 'width': 2},
    {'name': '_io', 'type': 'input', 'disabled': True},
    {'name': 'xlines', 'type': 'input'},
    {'name': 'badcb', 'type': 'input'},
    {'name': 'jitter', 'type': 'input'},
    {'name': 'badlags', 'type': 'input'},
    {'name': 'shortlags2', 'type': 'input'},
    {'name': 'spike', 'type': 'input'},
    {'name': 'linecheck', 'type': 'input'},
    {'name': 'bandzoom', 'type': 'input'},
    {'name': 'rthr', 'type': 'input'},
    {'name': 'cthr', 'type': 'input'},
    {'name': 'sgf', 'type': 'input'},
    {'name': 'notch', 'type': 'input'},
    {'name': 'blo', 'type': 'input'},
    {'name': 'bandstats', 'type': 'input'},
    {'name': 'srdp', 'type': 'input'},
    {'name': 'admit', 'type': 'radio', 'options': ['0', '1']},
    {'name': 'restart', 'type': 'input'},
    {'name': 'speczoom', 'type': 'input'},
]

sequoia_parameter_configs = [
    {'name': 'obsnum', 'type': 'dropdown', 'multi': True, 'width': 2},
    {'name': '_s', 'type': 'dropdown', 'multi': False, 'width': 2},
    {'name': '_io', 'type': 'input','disabled':True},
    {'name': 'pix_list', 'type': 'checkbox',
     'options':[{'label': str(i), 'value': str(i)} for i in range(16)],'value':[],'width': 2},
    {'name': 'dv', 'type': 'input'},
    {'name': 'dw', 'type': 'input'},
    {'name': 'extent', 'type': 'input'},
    {'name': 'restart', 'type': 'input'},
    {'name': 'birdies', 'type': 'input'},
    {'name': 'public', 'type': 'input'},
    {'name': 'qagrade', 'type': 'input'},
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
                            for config in parameter_configs if config['name'] not in ['obsnum', '_s','_io']
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
        dbc.ModalHeader(dbc.Row([
            dbc.Col(html.H5('EDIT PARAMETERS'),width='auto'),
            dbc.Col(dbc.Button('Parameter Info', id='para-help-btn', color='secondary'))],className='d-flex align-items-center'),
        ),
        dbc.ModalBody(
            html.Div([
                create_instrument_parameter_layout(instrument, row_length, configs),

                html.Div(id=f'{instrument}-parameter-help',style={'display':'none'}),
                # dbc.Offcanvas(id='parameter-help-offcanvas', is_open=False, children=[]),
              ],id='layouts'),),
    ],id='parameter-edit-modal',
        size='xl',
        centered=True,
        scrollable=True,
        backdrop='static'
    )

runfile_layout = html.Div([

    dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(dbc.Label(id=Runfile.CONTENT_TITLE.value), className='text-center my-2', width='auto'),
                        dbc.Col(
                            dbc.ButtonGroup([
                                dbc.Button(html.I(className='fas fa-trash-alt'), id=Runfile.DEL_BTN.value, outline=True,
                                           className='btn-icon', color='secondary'),
                                dbc.Button(html.I(className='fas fa-clone'), id=Runfile.CLONE_BTN.value, outline=True,
                                           className='btn-icon', color='secondary'),
                            ],
                                # size='lg',
                            ),
                            width='auto', className='d-flex justify-content-center align-items-center'),
                    ], className='align-items-center'
                )
            ),
            dbc.CardBody(
                [
                    html.Div([
                       dbc.Row([
                           dbc.Col([
                               dbc.ButtonGroup([
                                   dbc.Button('Edit Row', id=Table.EDIT_BTN.value, color='primary', className='me-2'),
                                   dbc.Button('Delete Row', id=Table.DEL_ROW_BTN.value, color='danger', className='me-2'),
                                   dbc.Button('Clone Row', id=Table.CLONE_ROW_BTN.value, color='success')
                               ])
                           ], width='auto')
                       ], className='gx-2 py-2 bg-light rounded shadow-sm'),
                    ], id=Table.OPTION.value,
                      style={
                          'display': 'none',
                          'position': 'absolute',
                          'right': '20px',
                          'zIndex': 1000
                      }),
                    html.Div(
                        [
                            dbc.Alert(id=Runfile.VALIDATION_ALERT.value, is_open=False, dismissable=True),
                            AgGrid(
                                id='runfile-table',
                                rowData=[],
                                defaultColDef={
                                    "filter": True,
                                    "checkboxSelection": {
                                        "function": 'params.column == params.columnApi.getAllDisplayedColumns()[0]'
                                    },
                                    "headerCheckboxSelection": {
                                        "function": 'params.column == params.columnApi.getAllDisplayedColumns()[0]'
                                    }
                                },
                                dashGridOptions={
                                    "rowSelection": "multiple",
                                    "rowMultiSelectWithClick": True,
                                    "suppressRowClickSelection": True,
                                    'enableBrowserTooltips': True,
                                },

                                className="ag-theme-alpine",
                            ),
                        ]),

                    dcc.ConfirmDialog(id=Table.CONFIRM_DEL_ROW.value, message=''),

                ],
            ),
            clone_runfile_modal,
            dcc.ConfirmDialog(id=Runfile.CONFIRM_DEL_ALERT.value, message=''),

            dbc.Tooltip("Delete Runfile", target=Runfile.DEL_BTN.value, placement='bottom'),
            dbc.Tooltip("Clone Runfile", target=Runfile.CLONE_BTN.value, placement='bottom'),
        ], ),

],

    id=Runfile.CONTENT_DISPLAY.value,
    className='runfile-content-container'
)

submit_job_layout = html.Div(
    [
        dbc.Card(
            [
                dbc.CardHeader(id='submit-session-job-label',className='title-link',),
                #todo select multi runfile
                dbc.CardBody(
                    [
                        dbc.Row([
                            dbc.Col([
                                dbc.Label('Select Runfiles'),
                                dcc.Dropdown(id = Session.RUNFILE_SELECT.value, placeholder='Select Runfiles', style={'width':'100%'}),
                            ],width=2),
                            dbc.Col([
                                dbc.Label('Input email address for notification'),
                                dbc.Input(id='email-input', placeholder='Enter email address', type='email', style={'width':'100%'}),
                            ],width=2),
                            dbc.Col(dbc.Button("Submit Job", id=Runfile.RUN_BTN.value, disabled=True,className="w-100"), width='auto'),
                            dbc.Col(dbc.Button("Check Status", id="check-status-btn", color="primary", className="w-100"),
                                    width='auto', ),
                        ], align='end',
                        ),
                        html.Div(id="slurm-job-status-output", className="mt-4")
                    ]),

            ], style={'maxHeight': '500px'}
                # className='justify-content-between align-items-end',
            ),
        html.Div(id=Session.SUBMIT_JOB.value,className='submit-job-message'),
],)

def create_parameter_help(instrument):
    if instrument == 'rsr':
        return html.P([
            html.H5("PI Parameters:"),
            html.Ul([
                html.Li("xlines: Set to a comma-separated list of freq, dfreq pairs where strong lines are to avoid baseline fitting."),
                html.Li("badcb: Set to a comma-separated list of (chassis/board) combinations, e.g., badcb=2/3,3/5. See also 'jitter'."),
                html.Li("jitter: Jittering Tsys and BadLags. Use badcb's based on jitter. Default is 1."),
                html.Li("badlags: Set to a badlags file if to use this instead of dynamically generated. Use 0 to force not to use it (not used yet)."),
                html.Li("shortlags: Set to a short_min and short_hi to avoid flagged strong continuum source lags, e.g., shortlags=32,10.0."),
                html.Li("spike: Spikiness of bad lags that need to be flagged. Default is 3."),
                html.Li("linecheck: Set to 1 to use the source name to grab the correct xlines. Default is 0."),
                html.Li("bandzoom: The band for the zoomed window (0..5). Default is 5."),
                html.Li("speczoom: Override bandzoom with a manual speczoom=CENTER,HALF_WIDTH pair."),
                html.Li("rthr: Threshold sigma value when averaging single observation repeats (-r option for rsr_driver). Default is 0.01."),
                html.Li("cthr: Threshold sigma value when coadding all observations (-t option for rsr_driver and rsr_sum). Default is 0.01."),
                html.Li("sgf: Savitzky-Golay high pass filter; odd number > 21. Default is 0."),
                html.Li("notch: Sigma cut for notch filter to eliminate large frequency oscillations. Needs sgf > 21. Default is 0."),
                html.Li("blo: Order of polynomial baseline subtraction. Default is 1."),
                html.Li("bandstats: Also compute stats of each of the 6 RSR bands. Default is 0."),
            ])
        ])
    else:
        return html.P("No help available for the selected instrument.")