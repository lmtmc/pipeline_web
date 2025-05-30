import json
import logging
import pandas as pd
from datetime import datetime
import os
import subprocess
from typing import Dict, List, Optional, Tuple, Union
from dash.exceptions import PreventUpdate
from dash import ctx
from utils.repo_utils import get_all_repos
from db.users_mgt import get_project_credentials

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ui_utils.log')
    ]
)
logger = logging.getLogger(__name__)

def get_projects_list(folder_path: str, repo_prefix: str) -> pd.DataFrame:
    """Get a list of projects from the specified folder path.
    
    Args:
        folder_path: Path to the folder containing projects
        repo_prefix: Prefix used to identify project repositories
        
    Returns:
        DataFrame containing project information
    """
    try:
        if not os.path.exists(folder_path):
            return pd.DataFrame()

        target_dir = os.path.join(folder_path, 'lmtoy_run')
        if not os.path.exists(target_dir):
            return pd.DataFrame()

        projects = []
        for item in os.listdir(target_dir):
            # Skip if not a valid project directory
            if not (item.startswith(repo_prefix) and 
                   item not in ['lmtoy_run', 'lmtoy_test']):
                continue
                
            project_path = os.path.join(target_dir, item)
            if not os.path.isdir(project_path):
                continue

            # Check if repository is empty
            try:
                result = subprocess.run(['git', 'ls-remote', '--heads', 'origin'], 
                                     cwd=project_path, 
                                     capture_output=True, 
                                     text=True)
                if not result.stdout.strip():
                    logger.info(f"Skipping empty repository in table: {item}")
                    continue
            except subprocess.CalledProcessError as e:
                logger.error(f"Error checking repository status: {item}: {str(e)}")
                continue

            # Get project ID
            pid = item.replace(repo_prefix, '')

            # Get last modified time
            mtime = os.path.getmtime(project_path)
            last_modified = datetime.fromtimestamp(mtime)

            # Get GitHub URL
            github_url = f"https://github.com/lmtoy/{item}"

            # Check if credentials exist
            creds = get_project_credentials(pid)
            profile_status = "Set" if creds['email'] or creds['password'] else "Not Set"

            projects.append({
                'No.': len(projects) + 1,
                'Project ID': pid,
                'Last Modified': last_modified,
                'GitHub': f'<a href="{github_url}" target="_blank">View</a>',
                'View/Edit': 'View/Edit',
                'Update': 'Update',
                'Profile': profile_status
            })

        df = pd.DataFrame(projects)
        if not df.empty:
            df = df.sort_values('Last Modified', ascending=False)
            df['No.'] = range(1, len(df) + 1)
        return df

    except Exception as e:
        logger.error(f"Error getting projects list: {str(e)}")
        return pd.DataFrame()

def get_project_id_from_cell(cell_data: Dict) -> Optional[str]:
    """Extract project ID from cell data.
    
    Args:
        cell_data: Dictionary containing cell data
        
    Returns:
        Project ID if found, None otherwise
    """
    if not cell_data:
        return None
    return cell_data.get('Project ID')

def get_table_data_for_year(trigger_id: str, active_cells: List[Dict], 
                          tables_data: List[List[Dict]], column_id: str) -> Dict:
    """Helper function to get active cell and table data for a specific year and column.
    
    Args:
        trigger_id: JSON string containing trigger information
        active_cells: List of active cells from all tables
        tables_data: List of table data from all tables
        column_id: ID of the column to check
        
    Returns:
        Dictionary containing row data
        
    Raises:
        PreventUpdate: If no valid cell is clicked or if the trigger is invalid
    """
    try:
        # Parse the trigger ID to get the year
        trigger_data = json.loads(trigger_id)
        year = trigger_data['year']
        
        # Get the correct table index based on year order
        repos_by_year = get_all_repos()
        sorted_years = sorted(repos_by_year.keys(), reverse=True)
        year_index = sorted_years.index(year)
        
        # Get the active cell for the correct year
        active_cell = active_cells[year_index] if year_index < len(active_cells) else None
        if not active_cell:
            raise PreventUpdate
            
        if active_cell['column_id'] != column_id:
            raise PreventUpdate
            
        # Get the table data for the active year using the same index
        table_data = tables_data[year_index] if year_index < len(tables_data) else []
        if not table_data:
            raise PreventUpdate
            
        # Get the row data directly from the table data
        if 0 <= active_cell['row'] < len(table_data):
            return table_data[active_cell['row']]
            
    except json.JSONDecodeError:
        raise PreventUpdate
        
    raise PreventUpdate

def get_project_id_from_active_cell(active_cells: List[Dict], tables_data: List[List[Dict]], 
                                  page_currents: List[int], page_sizes: List[int]) -> Tuple[Optional[str], Optional[int]]:
    """Get project ID from clicked cell in any table.
    
    Args:
        active_cells: List of active cells from all tables
        tables_data: List of table data from all tables
        page_currents: List of current page numbers
        page_sizes: List of page sizes
        
    Returns:
        tuple: (project_id, table_index) or (None, None) if not found
        
    Raises:
        PreventUpdate: If no valid cell is clicked or if the trigger is invalid
    """
    if not ctx.triggered:
        raise PreventUpdate
        
    # Get the triggered input
    trigger_id = ctx.triggered[0]['prop_id']
    if not trigger_id:
        raise PreventUpdate
        
    # Parse the trigger ID to get the year
    try:
        pattern_id = json.loads(trigger_id.split('.')[0])
        year = pattern_id['year']
        table_index = next((i for i, cell in enumerate(active_cells) if cell is not None), None)
        if table_index is None:
            raise PreventUpdate
    except (json.JSONDecodeError, KeyError, IndexError):
        raise PreventUpdate

    # Get the active cell for the triggered table
    active_cell = active_cells[table_index]
    if not active_cell:
        raise PreventUpdate

    # Get the corresponding table data and pagination info
    table_data = tables_data[table_index]
    page_current = page_currents[table_index]
    page_size = page_sizes[table_index]

    if not table_data:
        raise PreventUpdate

    # Calculate the actual row index considering pagination
    actual_row = active_cell['row'] + (page_current * page_size)
    if actual_row >= len(table_data):
        raise PreventUpdate

    row_data = table_data[actual_row]
    return row_data['Project ID'], table_index 