import copy
from dash import dcc, html, Output, Input, State, ctx, no_update
from dash.exceptions import PreventUpdate
import functions.project_function as pf
from my_server import app
from views.ui_elements import create_table,common_columns,create_parameter_header
import dash_bootstrap_components as dbc

INSTRUMENT = 'sequoia'
SEQUOIA_COLUMNS = common_columns + [
    # Section1: Select which beam
    'bank',  # 2 radiobutton (bank 1 or bank 2)
    'px_list',  # 3 with all checklist (0-15) and an all beam?
    'time_range',  # 4 a slider
    # Section2: Select baseline and spectral range
    # baseline
    'b_regions',  # 5 input box
    'l_regions',  # 6 input box
    'slice',  # 7 input box
    'baseline_order',  # 8 number inputbox
    # dv dw around vlsr
    'dv',  # 9 input box
    'dw',  # 10 input box
    # Section3: Calibration
    'birdie',  # 11 input box
    'rms_cut',  # 12 input box
    'stype',  # 13 radio button 1 0 2
    'otf_cal',  # 14 radio button 0 1
    # Section4: Gridding
    'extent',  # 15 label input Map Extent
    'resolution',  # 16 label input Resolution
    'cell',  # 17 label input cell
    'otf_select',  # 18 radio button jinc gauss triangle box
    'RMS',  # 19 RMS weighted checkbox yes
    # Section5: Advance Output
    'restart',  # 20 checkbox
    'admit',  # 21
    'maskmoment',  # 22
    'dataverse',  # 23
    'cleanup',  # 24
    # Section6: Others
    'edge',  # 25
    'speczoom',  # 26
    'badcb',  # 27
    'srdp',  # 28
]
sequoia_header = create_parameter_header('SEQUOIA')
sequoia_table = create_table('sequoia', SEQUOIA_COLUMNS)

SHOW_STYLE = {'display': 'block'}
HIDE_STYLE = {'display': 'none'}

layout = html.Div(
    [
        sequoia_header,
        sequoia_table,
        html.Br(),
        dcc.Location(id='project-url', refresh=True),
])

# Helper Functions
def update_column_defs(columnDefs, col_name, options):
    """Update columnDefs for a specific column with new options."""
    for col in columnDefs:
        if col['field'] == col_name:
            col['cellEditorParams'] = {'values': options}
    return columnDefs

def get_filtered_columns(columns, exclude):
    """Filter out specific columns from a list."""
    return [{'label': col, 'value': col} for col in columns if col not in exclude]

#if open this page,get the selected runfile from stored data and show the table
@app.callback(
    Output(f'{INSTRUMENT}-table', 'rowData', allow_duplicate=True),
    [
        Input('url', 'pathname'),
        Input('data-store', 'data'),
    ],
)
def update_sequoia_table(pathname, data):
    if not data or 'runfile' not in data:
        raise PreventUpdate
    # Load data from runfile
    df, _ = pf.df_runfile(data['selected_runfile'])
    return df.to_dict('records')

# update the source options based on the data in the data-store
@app.callback(
    Output(f'{INSTRUMENT}-table', 'columnDefs',allow_duplicate=True),
    Input('data-store', 'data'),
    State(f'{INSTRUMENT}-table', 'columnDefs'),
    prevent_initial_call=True
)
def initialize_table(data, columnDefs):
    if not data:
        raise PreventUpdate
    return update_column_defs(columnDefs, '_s', [str(s) for s in data.get('source', {}).keys()])

# update the obsnum options based on the source value in the cell
@app.callback(
    Output(f'{INSTRUMENT}-table', 'columnDefs'),
    Input(f'{INSTRUMENT}-table', 'cellClicked'),
    [
        State('data-store', 'data'),
        State(f'{INSTRUMENT}-table', 'columnDefs'),
        State(f'{INSTRUMENT}-table', 'rowData')
    ],
    prevent_initial_call=True
)
def update_obsnum_options(cell_clicked, data, columnDefs, rowData):
    if not cell_clicked or 'colId' not in cell_clicked or cell_clicked['colId'] != 'obsnum':
        raise PreventUpdate

    # updated_columnDefs = columnDefs.copy()

    source = rowData[cell_clicked.get('rowIndex')]['_s']
    obsnum_options = data.get('source', {}).get(source, [])
    return update_column_defs(columnDefs, 'obsnum', obsnum_options)

# if no row is selected, show add a new row button else show edit, delete, clone buttons
# if row length >1 show mutli-edit layout
@app.callback(
    [
        Output(f'{INSTRUMENT}-multi-edit-layout', 'style', allow_duplicate=True),
        Output(f'{INSTRUMENT}-del-row-btn', 'style'),
        Output(f'{INSTRUMENT}-clone-row-btn', 'style'),
        Output(f'{INSTRUMENT}-edit-column', 'options')
    ],
    Input(f'{INSTRUMENT}-table', "selectedRows"),
    prevent_initial_call=True
)
def show_edit_row_btn(selected_rows):
    options = get_filtered_columns(SEQUOIA_COLUMNS, {'_s', 'obsnum'})
    if selected_rows:
        style = SHOW_STYLE if len(selected_rows) > 1 else HIDE_STYLE
        return style, SHOW_STYLE, SHOW_STYLE, options
    return HIDE_STYLE, HIDE_STYLE, HIDE_STYLE, options

# delete the selected rows or colone the selected rows
@app.callback(
    Output(f'{INSTRUMENT}-table', 'rowData', allow_duplicate=True),
    [Input(f'{INSTRUMENT}-del-row-btn', 'n_clicks'), Input(f'{INSTRUMENT}-clone-row-btn', 'n_clicks')],
    [State(f'{INSTRUMENT}-table', 'selectedRows'), State(f'{INSTRUMENT}-table', 'rowData')],
    prevent_initial_call=True
)
def delete_or_clone_rows(del_clicks, clone_clicks, selected_rows, row_data):
    if not selected_rows:
        raise PreventUpdate
    if del_clicks:
        return [row for row in row_data if row not in selected_rows]
    elif clone_clicks:
        return row_data + copy.deepcopy(selected_rows)
    raise PreventUpdate

# when apply edit button is clicked, update the selected rows
@app.callback(
    [
        Output(f'{INSTRUMENT}-table', 'rowData'),
        Output(f'{INSTRUMENT}-edit-output', 'is_open', allow_duplicate=True),
        Output(f'{INSTRUMENT}-edit-output', 'children', allow_duplicate=True),
        Output(f'{INSTRUMENT}-multi-edit-layout', 'style')
    ],
    Input(f'{INSTRUMENT}-apply-edit-button', 'n_clicks'),
    [
        State(f'{INSTRUMENT}-table', 'selectedRows'),
        State(f'{INSTRUMENT}-table', 'rowData'),
        State(f'{INSTRUMENT}-edit-column', 'value'),
        State(f'{INSTRUMENT}-edit-value', 'value')
    ],
    prevent_initial_call=True
)
def update_selected_rows(n_clicks, selected_rows, row_data, column, value):
    if not n_clicks or not selected_rows or not column or value is None:
        return no_update, True, "Invalid input!", HIDE_STYLE

    updated_data = copy.deepcopy(row_data)
    for row in selected_rows:
        idx = next((i for i, r in enumerate(row_data) if r == row), None)
        if idx is not None:
            if isinstance(value, list):
                value = ','.join(map(str, value))
            updated_data[idx][column] = value
    return updated_data, True, f"Updated {len(selected_rows)} rows.", HIDE_STYLE


# click cancel go back to previous page
# click save, save the data to the runfile
@app.callback(
    Output('project-url', 'pathname',allow_duplicate=True),
    Input(f'{INSTRUMENT}-cancel-btn', 'n_clicks'),
    Input(f'{INSTRUMENT}-save-btn', 'n_clicks'),
    State(f'{INSTRUMENT}-table', 'virtualRowData'),
    State('data-store', 'data'),
    prevent_initial_call=True
)
def save_edit(n1, n2, table_data, store_data):
    if not n1 and not n2:
        raise PreventUpdate
    triggered_id = ctx.triggered_id
    if triggered_id == f'{INSTRUMENT}-save-btn':
        print('save the edit')
        pf.save_runfile(table_data, store_data['selected_runfile'])
        return no_update
    return '/pipeline_web/project'
#
# can't select rows with different _s values
@app.callback(
    Output(f'{INSTRUMENT}-table', 'selectedRows'),
    Output(f'{INSTRUMENT}-edit-output', 'is_open'),
    Output(f'{INSTRUMENT}-edit-output', 'children'),
    Input(f'{INSTRUMENT}-table', 'selectedRows'),
    State(f'{INSTRUMENT}-table', 'rowData'),
    prevent_initial_call=True
)
def verify_selected_rows(selected_rows, row_data):
    if not selected_rows:
        return no_update, False, ''
    s_values = set([row['_s'] for row in selected_rows if row['_s'] is not None])
    if len(s_values) > 1:
        return [], True, 'Please select rows with the same source!'
    return selected_rows, False, ''

@app.callback(
    Output(f'{INSTRUMENT}-edit-layout', 'children'),
    Input(f'{INSTRUMENT}-edit-column', 'value'),
    prevent_initial_call=True
)
def update_edit_layout(selected_column):
    options = {
        'bank': [{'label': '0', 'value': 0}, {'label': '1', 'value': 1}, {'label': 'Not Apply', 'value': ''}],
        'stype': [{'label': str(i), 'value': i} for i in range(3)] + [{'label': 'Not Apply', 'value': ''}],
        'px_list': [{'label': str(i), 'value': i} for i in range(16)]
    }
    if selected_column in options:
        component = dbc.RadioItems if selected_column != 'px_list' else dbc.Checklist
        return component(options=options[selected_column], id=f'{INSTRUMENT}-edit-value', inline=True)
    return dbc.Input(id=f'{INSTRUMENT}-edit-value', type='text', placeholder='Enter value')