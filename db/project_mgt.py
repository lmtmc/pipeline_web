import os
from my_server import server
from datetime import datetime

def get_projects_list(folder_path):
    """Get list of projects from a folder path."""
    try:
        if not os.path.exists(folder_path):
            return []
        
        # Get all directories in the folder path
        projects = [d for d in os.listdir(folder_path) 
                   if os.path.isdir(os.path.join(folder_path, d))]
        
        # Get project details
        project_details = []
        for project in projects:
            project_path = os.path.join(folder_path, project)
            created_time = datetime.fromtimestamp(os.path.getctime(project_path))
            modified_time = datetime.fromtimestamp(os.path.getmtime(project_path))
            
            project_details.append({
                'name': project,
                'path': project_path,
                'created_time': created_time,
                'modified_time': modified_time
            })
        
        return project_details
    except Exception as e:
        print(f"Error getting projects list: {e}")
        return []

def get_project_details(project_path):
    """Get detailed information about a specific project."""
    try:
        if not os.path.exists(project_path):
            return None
        
        return {
            'name': os.path.basename(project_path),
            'path': project_path,
            'created_time': datetime.fromtimestamp(os.path.getctime(project_path)),
            'modified_time': datetime.fromtimestamp(os.path.getmtime(project_path)),
            'files': [f for f in os.listdir(project_path) 
                     if os.path.isfile(os.path.join(project_path, f))]
        }
    except Exception as e:
        print(f"Error getting project details: {e}")
        return None 