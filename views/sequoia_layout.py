import copy
from dash import dcc, html, Output, Input, State, ctx, no_update
from dash.exceptions import PreventUpdate
import functions.project_function as pf
from my_server import app
from views.ui_elements import create_table,common_columns,create_parameter_header
import dash_bootstrap_components as dbc

instrument = 'sequoia'
sequoia_columns = common_columns + [
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
sequoia_table = create_table('sequoia', sequoia_columns)

# rsr_parameter_btns = create_parameter_btns('rsr')
layout = html.Div([
        sequoia_header,
        sequoia_table,
        html.Br(),
    dcc.Location(id='project-url', refresh=True),
])

show_style = {'display': 'block'}
hide_style = {'display': 'none'}

#if open this page,get the selected runfile from stored data and show the table
@app.callback(
    Output(f'{instrument}-table', 'rowData', allow_duplicate=True),
    [
        Input('url', 'pathname'),
        Input('data-store', 'data'),
    ],
)
def update_sequoia_table(pathname, data):
    if not data or 'runfile' not in data:
        raise PreventUpdate
    # Load data from runfile
    df, _ = pf.df_runfile(data['runfile'])

    # Convert dataframe to dictionary records for rowData
    row_data = df.to_dict('records')
    # Return row_data and updated columnDefs as a tuple
    return row_data

# update the source options based on the data in the data-store
@app.callback(
    Output(f'{instrument}-table', 'columnDefs',allow_duplicate=True),
    Input('data-store', 'data'),
    State(f'{instrument}-table', 'columnDefs'),
    prevent_initial_call=True
)
def initialize_table(data, columnDefs):
    if data is None:
        raise PreventUpdate
    # Assuming 'source' data is nested within 'data' as a dictionary of lists
    s_values = data.get('source', {})
    s_values = s_values.keys()
    updated_columnDefs = columnDefs.copy()

    updated_columnDefs[0]['cellEditorParams'] = {'values': [str(s) for s in s_values]}
    return updated_columnDefs

# update the obsnum options based on the source value in the cell
@app.callback(
    Output(f'{instrument}-table', 'columnDefs'),
    Input(f'{instrument}-table', 'cellClicked'),
    State('data-store', 'data'),
    State(f'{instrument}-table', 'columnDefs'),
    State(f'{instrument}-table', 'rowData'),
    prevent_initial_call=True
)
def update_obsnum_options(cell_clicked, data, columnDefs, rowData):
    if not cell_clicked or 'colId' not in cell_clicked or cell_clicked['colId'] != 'obsnum':
        raise PreventUpdate

    updated_columnDefs = columnDefs.copy()

    for col in updated_columnDefs:
        if col['field'] == 'obsnum':
            source = rowData[cell_clicked.get('rowIndex')]['_s']
            obsnum_options = data.get('source', {}).get(source, [])
            print('obsnum_options',obsnum_options)
            col['cellEditorParams'] = {'values': obsnum_options}
    return updated_columnDefs

# if no row is selected, show add a new row button else show edit, delete, clone buttons
# if row length >1 show mutli-edit layout
@app.callback(
    Output(f'{instrument}-multi-edit-layout', 'style',allow_duplicate=True),
    Output(f'{instrument}-del-row-btn', 'style'),
    Output(f'{instrument}-clone-row-btn', 'style'),
    Output(f'{instrument}-edit-column', 'options'),
    Input(f'{instrument}-table', "selectedRows"),
    prevent_initial_call=True
)
def show_edit_row_btn(selected_rows):
    # Filter out columns that are `_s` or `obsnums`
    filtered_columns = [{'label': col, 'value': col} for col in sequoia_columns if col not in {'_s', 'obsnum'}]

    if selected_rows:
        if len(selected_rows) > 1:
            return show_style, show_style, show_style, filtered_columns
        return hide_style, show_style, show_style, filtered_columns
    return hide_style, hide_style, hide_style, filtered_columns

# delete the selected rows or colone the selected rows
@app.callback(
    Output(f'{instrument}-table', 'rowData',allow_duplicate=True),
    Input(f'{instrument}-del-row-btn', 'n_clicks'),
    Input(f'{instrument}-clone-row-btn', 'n_clicks'),
    State(f'{instrument}-table', 'selectedRows'),
    State(f'{instrument}-table', 'rowData'),
    prevent_initial_call=True
)
def delete_or_clone_rows(n1, n2, selected_rows, row_data):
    if not selected_rows:
        raise PreventUpdate

    if n1:
        # Delete selected rows
        updated_row_data = [row for row in row_data if row not in selected_rows]
    elif n2:
        # Clone selected rows
        updated_row_data = row_data + copy.deepcopy(selected_rows)
    else:
        raise PreventUpdate

    return updated_row_data

# when apply edit button is clicked, update the selected rows
@app.callback(
    Output(f'{instrument}-table', 'rowData'),
    Output(f'{instrument}-edit-output', 'is_open',allow_duplicate=True),
    Output(f'{instrument}-edit-output', 'children',allow_duplicate=True),
    Output(f'{instrument}-multi-edit-layout', 'style'),
    Input(f'{instrument}-apply-edit-button', 'n_clicks'),
    State(f'{instrument}-table', 'selectedRows'),
    State(f'{instrument}-table', 'rowData'),
    State(f'{instrument}-edit-column', 'value'),
    State(f'{instrument}-edit-value', 'value'),
    prevent_initial_call=True
)
def update_selected_rows(n_clicks, selected_rows, row_data, column, value):
    if not n_clicks:
        raise PreventUpdate

    if not selected_rows or not column or value is None:
        return no_update, True, "Please select rows, a column, and enter a value to edit.",hide_style

    # Create a deep copy of row_data to ensure we're not modifying the original data
    updated_row_data = copy.deepcopy(row_data)

    for selected_row in selected_rows:
        # Get the index of the row in the full row_data
        row_index = next(
            (index for (index, d) in enumerate(row_data) if d == selected_row),
            None
        )
        if row_index is not None:
            updated_row_data[row_index][column] = value

    return updated_row_data, True, f"Edited {len(selected_rows)} rows in column '{column}' with value '{value}'.",hide_style
#
# click cancel go back to previous page
# click save, save the data to the runfile
@app.callback(
    Output('project-url', 'pathname',allow_duplicate=True),
    Input(f'{instrument}-cancel-btn', 'n_clicks'),
    Input(f'{instrument}-save-btn', 'n_clicks'),
    State(f'{instrument}-table', 'virtualRowData'),
    State('data-store', 'data'),
    prevent_initial_call=True
)
def save_edit(n1, n2, table_data, store_data):
    if not n1 and not n2:
        raise PreventUpdate
    triggered_id = ctx.triggered_id
    if triggered_id == f'{instrument}-save-btn':
        print('save the edit')
        pf.save_runfile(table_data, store_data['runfile'])
        return no_update
    return '/pipeline_web/project'
#
# can't select rows with different _s values
@app.callback(
    Output(f'{instrument}-table', 'selectedRows'),
    Output(f'{instrument}-edit-output', 'is_open'),
    Output(f'{instrument}-edit-output', 'children'),
    Input(f'{instrument}-table', 'selectedRows'),
    State(f'{instrument}-table', 'rowData'),
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
    Output(f'{instrument}-edit-layout', 'children'),
    Input(f'{instrument}-edit-column', 'value'),
    prevent_initial_call=True
)
def update_edit_layout(selected_column):
    print('selected_column', selected_column)
    # Define layouts for each specific column
    if selected_column == 'bank' or selected_column == 'otf_cal':
        # Show radio buttons for 'bank' or 'otf_cal' with options 0, 1, "Not Apply"
        print('selected_column', selected_column)
        return dbc.RadioItems(
            options=[
                {'label': '0', 'value': 0},
                {'label': '1', 'value': 1},
                {'label': 'Not Apply', 'value': ''}
            ],
            id=f'{instrument}-edit-value',
            inline=True
        )
    elif selected_column == 'stype':
        # Show radio buttons for 'stype' with options 0, 1, 2, "Not Apply"
        return dbc.RadioItems(
            options=[
                {'label': '0', 'value': 0},
                {'label': '1', 'value': 1},
                {'label': '2', 'value': 2},
                {'label': 'Not Apply', 'value': 'not_apply'}
            ],
            id=f'{instrument}-edit-value',
            inline=True
        )
    elif selected_column == 'px_list':
        # Show checkboxes for 'px_list' with options from 0 to 15
        return dbc.Checklist(
            options=[{'label': str(i), 'value': i} for i in range(16)],
            id=f'{instrument}-edit-value',
            inline=True
        )
    # Default layout if no special column is selected
    return dbc.Input(id=f'{instrument}-edit-value', type='text', placeholder='Enter value')