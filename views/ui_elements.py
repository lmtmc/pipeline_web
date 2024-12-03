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
    TABLE = 'runfile-table'
    CONTENT_TITLE = 'runfile-content-title'
    CONTENT = 'runfile-content'
    DEL_BTN = 'del-runfile'
    CLONE_BTN = 'clone-runfile'
    SAVE_BTN = 'runfile-save'
    EDIT_BTN = 'runfile-edit'
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
    EDIT_TABLE = 'edit-table'
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
            dbc.NavItem(dbc.NavLink(f'Current Project: {username}', href="#", style={'color': 'black'}),
                        className='me-3'),
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
submit_job_layout = html.Div(
    [
        dbc.Card(
            [
                dbc.CardHeader(id='submit-session-job-label',className='title-link',),
                #todo select multi runfile
                dbc.CardBody(dcc.Dropdown(id = Session.RUNFILE_SELECT.value, placeholder='Select Runfiles')),
                dbc.CardFooter(dbc.Row(
                    [
                        dbc.Col(dbc.Button("Submit Job", id=Runfile.RUN_BTN.value, style={'display': 'none'})),
                        dbc.Col(dcc.Link('Open Result',
                                 href='',
                                 id='view-result-url',
                                 target='_blank',
                                 style={'display': 'none', 'color': 'grey'}),)

                    ], justify='end'),
                ),
            ],
                # className='justify-content-between align-items-end',
            ),
        html.Div(id=Session.SUBMIT_JOB.value,className='submit-job-message'),
])
def create_dropdown_parameter(col):
    return html.Div(
        [
            dbc.Label(f'{col}:'),
            dcc.Dropdown(id=f'{col}-dropdown', placeholder=f'Select {col}', className='mb-3'),
        ]
    )
def create_radio_parameter(col, options):
    return html.Div(
        [
            dbc.Label(f'{col}:'),
            dcc.RadioItems(id=f'{col}-radio', options=options,className='mb-3', inline=True),
        ]
    )
def create_input_parameter(col):
    return html.Div(
        [
            dbc.Label(f'{col}:'),
            dcc.Input(id=f'{col}-input', type='text', placeholder=f'Enter {col}', className='mb-3'),
        ]
    )
def create_checkbox_parameter(col):
    return html.Div(
        [
            dbc.Label(f'{col}:'),
            dcc.Checklist(id=f'{col}-checkbox', className='mb-3'),
        ]
    )

parameter_layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(create_dropdown_parameter('obsnum'),width=2),
                dbc.Col(create_dropdown_parameter('_s'),width=2),
                dbc.Col(create_input_parameter('badcb'),width='auto'),
                dbc.Col(create_input_parameter('srdp'),width='auto'),
                dbc.Col(create_radio_parameter('admit',['0','1']),width='auto'),
                dbc.Col(create_input_parameter('speczoom'),width='auto'),
                dbc.Col(create_input_parameter('other_rsr'),width='auto'),
                dbc.Col(create_input_parameter('other_sequoia'),width='auto'),
            ],           # className='d-flex justify-content-between'
        ),
    ],id='parameter-layout')

parameter_layout_modal = dbc.Modal(
    [
        dbc.ModalHeader('Edit Parameters'),
        dbc.ModalBody(
            html.Div([
                parameter_layout,
              ],id='layouts'),),
        dbc.ModalFooter(
                dbc.Row([
                    dbc.Col(dbc.Button('Apply', id='edit-apply', color='primary', className='mt-3'), width='auto'),
                    dbc.Col(dbc.Button('Cancel', id='edit-cancel', color='danger', className='mt-3'), width='auto'),
                    ])
        )
    ],id='parameter-edit-modal', size='xl', centered=True, scrollable=True,backdrop='static')

runfile_layout = html.Div(
    dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(dbc.Label(id=Runfile.CONTENT_TITLE.value), className='text-center my-4',width='auto'),
                        dbc.Col(
                            dbc.ButtonGroup([
                                dbc.Button(html.I(className='fas fa-edit'), id=Runfile.EDIT_BTN.value, outline=True, className='btn-icon', color='secondary'),
                                dbc.Button(html.I(className='fas fa-trash-alt'), id=Runfile.DEL_BTN.value,outline=True, className='btn-icon',color='secondary'),
                                dbc.Button(html.I(className='fas fa-clone'), id=Runfile.CLONE_BTN.value, outline=True, className='btn-icon', color='secondary'),
                            ],size='lg'
                            ),
                            width='auto', className='d-flex align-items-center'),
                    ], className='mb-3 align-items-center'
                )
            ),
            dbc.CardBody(
                [
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
                                # "pagination": True,
                                "rowSelection": "multiple",
                                "rowMultiSelectWithClick": True,
                                "suppressRowClickSelection": True,
                                # "animateRows": True,
                                # "enableCellTextSelection": True,
                                # 'undoRedoCellEditing': True,
                                'enableBrowserTooltips': True,
                                # 'skipHeaderOnAutoSize': True,
                            },
                            # columnSize='sizeToFit',
                            # columnSizeOptions = {"skipHeader": True},

                            style={
                                "height": "500px",
                                "width": "100%",
                            },
                            className="ag-theme-alpine",
                        ),
                    ]),
                parameter_layout_modal,
                ],
            ),
            clone_runfile_modal,
            dcc.ConfirmDialog(id=Runfile.CONFIRM_DEL_ALERT.value, message=''),
            dbc.Tooltip("Edit", target=Runfile.EDIT_BTN.value, placement='bottom'),
            dbc.Tooltip("Delete", target=Runfile.DEL_BTN.value, placement='bottom'),
            dbc.Tooltip("Clone", target=Runfile.CLONE_BTN.value, placement='bottom'),
        ]),
    id=Runfile.CONTENT_DISPLAY.value,
    className='runfile-content-container'
)

common_columns = ['_s', 'obsnum']
instruments = {
    'rsr': {
        'columns': common_columns + ['xlines', 'badcb', 'jitter', 'badlags', 'shortlags', 'spike', 'linecheck', 'bandzoom', 'speczoom',
                    'rthr', 'cthr', 'sgf', 'notch', 'blo','bandstats','admit','speczoom']
    },
    'sequoia': {
        'columns': common_columns + ['bank', 'exclude_beams', 'time_range', 'b_regions', 'l_regions', 'slice', 'baseline_order',
                    'dv', 'dw', 'birdie', 'rms_cut', 'stype', 'otf_cal', 'extent', 'resolution', 'cell', 'otf_select',
                    'RMS', 'restart', 'admit', 'maskmoment', 'dataverse', 'cleanup', 'edge', 'speczoom', 'badcb', 'srdp']
    }
}
custom_multiselect = {
    'cellEditor': 'agPopupSelectCellEditor',
    'cellEditorParams': {
        'values': ['Option 1', 'Option 2', 'Option 3'],  # Your options here
        'multiple': True
    }
}

def create_table(instrument, columns):
    # Define special configurations for specific columns
    special_columns_editor = {
        '_s': {
            'cellEditor': 'agSelectCellEditor',
            'cellEditorParams': {},
        },
        'obsnum': {'cellEditor': 'agSelectCellEditor','cellEditorParams': {}},
        'bank': {'cellEditor': {'function': 'RadioSelector'}, 'cellEditorParams': {'values': [0, 1]}},
        'px_list': {'cellEditor': {'function':'CheckboxSelector'}, 'cellEditorParams': {}},
        'stype': {
            'cellEditor': {'function': 'RadioSelector'},
            'cellEditorParams': {'values': ['0', '1', '2']},
        },
        'otf_cal': {
            'cellEditor': {'function': 'RadioSelector'},
            'cellEditorParams': {'values': ['0', '1']},
        },
        'otf_select': {
            'cellEditor': {'function': 'RadioSelector'},
            'cellEditorParams': {'values': ['jinc', 'gauss', 'triangle', 'box']},
        },
        'RMS': {
            'cellEditor': {'function': 'RadioSelector'},
            'cellEditorParams': {'values': ['0', '1']},
        },
        'restart': {
            'cellEditor': {'function': 'RadioSelector'},
            'cellEditorParams': {'values': ['0', '1']},
        },
        'admin': {
            'cellEditor': {'function': 'RadioSelector'},
            'cellEditorParams': {'values': ['0', '1']},
        },
        'maskmoment': {
            'cellEditor': {'function': 'RadioSelector'},
            'cellEditorParams': {'values': ['0', '1']},
        },

    }
    # Add an "index" column explicitly
    columns.insert(0, "index")

    column_defs = []

    for col in columns:
        # Default cell editor is agTextCellEditor
        cell_editor = 'agTextCellEditor'
        cell_editor_params = {}
        tooltip = col
        # Update cell editor based on special columns
        if col in special_columns_editor:
            cell_editor = special_columns_editor[col].get('cellEditor', 'agTextCellEditor')
            cell_editor_params = special_columns_editor[col].get('cellEditorParams', {})

        # Construct column definition
        column_def = {
            # "headerName": col,
            "field": col,
            "valueGetter": {"function": "params.node.rowIndex + 1"},
            "resizable": True,
            # "sortable": True,
            "filter": True,
            "editable": False,
            # "valueGetter": f"params.data.{col}",
            "cellEditorPopup": True,
            "cellEditor": cell_editor,
            "cellEditorParams": cell_editor_params,
            "headerTooltip": tooltip
        }

        column_defs.append(column_def)

    default_col_def = {
        "flex": 1,
        "minWidth": 100,
        "filter": True,
        "sortable": True,
        "resizable": True,
        "editable": True,
        'checkboxSelection': {
            'function':'params.column == params.columnApi.getAllDisplayedColumns()[0]',
        },
        'headerCheckboxSelection': {
            'function':'params.column == params.columnApi.getAllDisplayedColumns()[0]',
        },
        # "floatingFilter": True,
    }

    return html.Div([
        dcc.Store(id=f'{instrument}-table-data', data=[]),
        html.Div(
            dbc.ButtonGroup([
                dbc.Button('Delete rows', id=f'{instrument}-del-row-btn', color='secondary', outline=True,
                           className='mr-1'),
                dbc.Button('Clone rows', id=f'{instrument}-clone-row-btn', color='secondary', outline=True,
                           className='mr-1'),
            ]),
        ),
        AgGrid(
            id=f'{instrument}-table',
            columnDefs=column_defs,
            rowData=[],
            dashGridOptions={
                "pagination": True,
                "rowSelection": "multiple",
                "rowMultiSelectWithClick": True,
                "suppressRowClickSelection": True,
                "animateRows": True,
                "enableCellTextSelection": True,
                'undoRedoCellEditing': True,
                'enableBrowserTooltips': True,
                'skipHeaderOnAutoSize': True,
            },
            # columnSize='sizeToFit',
            # columnSizeOptions = {"skipHeader": True},
            getRowId="params.data.index",
            style={
                "height": "500px",
                "width": "100%",
            },
        ),

        html.Br(),
        dbc.Row([
            dbc.Col(
                html.Div(dbc.Card(
                    [
                        dbc.Label('Multi-Row-Edit', className='large-label'),
                        dbc.Row(
                            [
                                dbc.Col(dcc.Dropdown(
                                    id=f'{instrument}-edit-column',
                                    placeholder='Select column to edit', className='mb-3'), width=4),
                                dbc.Col(
                                    html.Div(dcc.Input(id=f'{instrument}-edit-value', type='text', placeholder='Enter new value',
                                               className='mb-3'),
                                            id=f'{instrument}-edit-layout'), width='auto'
                                ),

                                dbc.Col(html.Button('Apply Edit', id=f'{instrument}-apply-edit-button', n_clicks=0),
                                        width='auto'),
                            ])],
                    style={'width': '50%', 'padding': '10px'}), id=f'{instrument}-multi-edit-layout',
                    style={'display': 'none'}),
            ),
            dbc.Col(create_parameter_btns(instrument), width='auto'),
        ]),

        dcc.ConfirmDialog(id=f'{instrument}-confirm-del-row', message=''),

        dbc.Alert(id=f'{instrument}-edit-output', is_open=False, dismissable=True),
    ])

fixed_states = [State(Runfile.TABLE.value, 'data')]
# Define dynamic Output objects based on a list of field names
field_names = instruments['rsr']['columns']
dynamic_outputs = [Output(field, 'value', allow_duplicate=True) for field in field_names]
dynamic_states = [State(field, 'value') for field in field_names]
# Combine fixed and dynamic Output objects
all_states = fixed_states + dynamic_states
# Layout creation functions
tooltip_target = ['obsunms_label', 'bank_label', 'b_order_label', 'extent_label']

def create_parameter_header(instrument):
    return html.Div(
        [
            html.H5(f'{instrument} Parameter Table', id='parameter-table-location', className='parameter-table-title'),
        ],className='d-flex justify-content-between')

def create_parameter_btns(instrument):
    return html.Div(
        dbc.Row([
            dbc.Col(
                dbc.Button("Save", id=f'{instrument}-save-btn', color='primary', className='mr-2'),
                width="auto", className="ml-auto"
            ),
            dbc.Col(
                dbc.Button("Back", id=f'{instrument}-cancel-btn', color='danger'),
                width="auto"
            ),
        ], className='d-flex justify-content-end align-items-center mb-2 p-2')
    )


