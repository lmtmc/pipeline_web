import pandas as pd
from datetime import datetime
import os
from db.users_mgt import get_project_credentials

def get_projects_list(folder_path, repo_prefix):
    """Get a list of projects from the specified folder path."""
    try:
        if not os.path.exists(folder_path):
            return pd.DataFrame()

        target_dir = os.path.join(folder_path, 'lmtoy_run')
        if not os.path.exists(target_dir):
            return pd.DataFrame()

        projects = []
        for item in os.listdir(target_dir):
            if item.startswith(repo_prefix):
                project_path = os.path.join(target_dir, item)
                if os.path.isdir(project_path):
                    # Get last modified time
                    mtime = os.path.getmtime(project_path)
                    last_modified = datetime.fromtimestamp(mtime)

                    # Get project ID
                    pid = item.replace(repo_prefix, '')

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
        print(f"Error getting projects list: {str(e)}")
        return pd.DataFrame() 