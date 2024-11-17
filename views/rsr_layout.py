import copy
import os
import flask
from dash import dcc, html, Output, Input, State, ctx, no_update
from dash.exceptions import PreventUpdate
import functions.project_function as pf
from my_server import app
from views.ui_elements import create_table,common_columns,create_parameter_header

instrument = 'rsr'
rsr_columns = common_columns + ['xlines', 'badcb', 'srdp', 'jitter', 'badlags', 'shortlags', 'spike', 'linecheck', 'bandzoom', 'speczoom',
                    'rthr', 'cthr', 'sgf', 'notch', 'blo','bandstats','admit']
rsr_header = create_parameter_header('RSR')
rsr_table = create_table('rsr', rsr_columns)

# rsr_parameter_btns = create_parameter_btns('rsr')
layout = html.Div([
        rsr_header,
        rsr_table,
        html.Br(),
    dcc.Location(id='project-url', refresh=True),
])

show_style = {'display': 'block'}
hide_style = {'display': 'none'}

# if open this page, get the source and obsnum from the data_store and show the table
@app.callback(
    [
        Output(f'{instrument}-table', 'rowData',allow_duplicate=True),
        Output(f'{instrument}-table', 'columnDefs',allow_duplicate=True)
    ],
    [
        Input('url', 'pathname'),
        Input('data-store', 'data')
    ],
    State(f'{instrument}-table', 'columnDefs'),
)
def update_rsr_table(pathname, data, columnDefs):
    if not data or 'runfile' not in data:
        raise PreventUpdate

    # Load data from runfile
    df, _ = pf.df_runfile(data['runfile'])

    # Get s_values from data store
    s_values = data.get('source', {})

    # Ensure s_values is a dictionary
    if not isinstance(s_values, dict):
        s_values = {}

    # Update column definitions
    for col in columnDefs:
        if col['field'] == '_s':
            col['cellEditorParams'] = {'values': list(s_values.keys())}
        elif col['field'] == 'obsnum':
            # Initialize with an empty list, will be updated when '_s' is selected
            col['cellEditorParams'] = {'values': []}

    # Ensure all required columns are present in the dataframe
    for col in [col['field'] for col in columnDefs]:
        if col not in df.columns:
            df[col] = ''

    # Convert dataframe to dictionary records
    row_data = df.to_dict('records')

    return row_data, columnDefs

# update obsnum options based on the source selected
@app.callback(
    Output(f'{instrument}-table', 'columnDefs' ),
    Input(f'{instrument}-table', 'cellValueChanged'),
    State('data-store', 'data'),
    State(f'{instrument}-table', 'columnDefs'),
    prevent_initial_call=True
)
def update_obsnum_options(cell_changed, data, columnDefs):
    if not cell_changed or 'colId' not in cell_changed or cell_changed['colId'] != '_s':
        raise PreventUpdate

    s_values = data.get('source', {})
    new_source = cell_changed.get('value')

    if new_source is None:
        raise PreventUpdate

    for col in columnDefs:
        if col['field'] == 'obsnum':
            col['cellEditorParams'] = {'values': s_values.get(new_source, [])}

    return columnDefs

# if no row is selected, show add a new row button else show edit, delete, clone buttons
# if row length >1 show mutli-edit layout
@app.callback(
    Output(f'{instrument}-multi-edit-layout', 'style',allow_duplicate=True),
    Output(f'{instrument}-del-row-btn', 'style'),
    Output(f'{instrument}-clone-row-btn', 'style'),
    Output(f'{instrument}-add-row-btn', 'style'),
    Output(f'{instrument}-edit-column', 'options'),
    Input(f'{instrument}-table', "selectedRows"),
    prevent_initial_call=True
)
def show_edit_row_btn(selected_rows):
    if selected_rows:
        if len(selected_rows) > 1:
            return show_style, show_style, show_style, hide_style, [{'label': col, 'value': col} for col in rsr_columns]
        return hide_style, show_style, show_style, hide_style, [{'label': col, 'value': col} for col in rsr_columns]
    return hide_style, hide_style, hide_style, show_style, [{'label': col, 'value': col} for col in rsr_columns]

# todo update the select rows based on the select/deseletct all button
@app.callback(
    Output(f'{instrument}-table', 'selectedRows',allow_duplicate=True),
    Input(f'{instrument}-select-all-btn', 'n_clicks'),
    State(f'{instrument}-table', 'rowData'),
    State(f'{instrument}-table', 'selectedRows'),
    prevent_initial_call=True
)
def update_selected_row(n_clicks, rows, selected_rows):
    if not n_clicks:
        raise PreventUpdate
    # If selected_rows is empty, select all rows
    if n_clicks % 2 == 1:
        return rows
    else:
        return []



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

# if _s or obsnum is selected in the multi-edit layout, show the dropdown options for source and obsnum
# verify each column

# click cancel go back to previous page
# click save, save the data to the runfile
@app.callback(
    Output('project-url', 'pathname'),
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
        pf.save_runfile(table_data, store_data['runfile'])
    return '/pipeline_web/project'

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
    if not selected_rows or not row_data:
        return no_update, False, ''
    s_values = set([row['_s'] for row in selected_rows if row.get('_s') is not None])
    if len(s_values) > 1:
        return [], True, 'Please select rows with the same source!'
    return selected_rows, False, ''