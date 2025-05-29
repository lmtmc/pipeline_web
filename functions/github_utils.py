import requests
import subprocess
import logging
import os

# Configure logging
logger = logging.getLogger(__name__)

def get_github_repos(api_url, repo_prefix):
    """Get list of repositories from GitHub API."""
    try:
        all_repos = []
        next_url = api_url
        
        while next_url:
            response = requests.get(next_url)
            response.raise_for_status()
            repos = response.json()
            all_repos.extend(repos)
            
            # Check for next page in Link header
            next_url = None
            if 'Link' in response.headers:
                links = response.headers['Link'].split(',')
                for link in links:
                    if 'rel="next"' in link:
                        # Extract URL from between angle brackets
                        next_url = link.split(';')[0].strip().strip('<>')
                        break
            
        print(f"Total repos from GitHub API: {len(all_repos)}")
        
        # Filter repositories:
        # 1. Must start with repo_prefix
        # 2. Must not be lmtoy_run or lmtoy_test
        # 3. Must start with '2' after lmtoy_
        valid_repos = []
        for repo in all_repos:
            name = repo['name']
            if name.startswith(repo_prefix):
                if name in ['lmtoy_run', 'lmtoy_test']:
                    print(f"Excluding special repo: {name}")
                    continue
                if not name[len(repo_prefix):].startswith('2'):
                    print(f"Excluding non-202x repo: {name}")
                    continue
                valid_repos.append(name)
                print(f"Adding valid repo: {name}")
        
        print(f'Total valid repos: {len(valid_repos)}')
        return valid_repos
    except Exception as e:
        logger.error(f"Error fetching GitHub repositories: {str(e)}")
        return []

def clone_or_pull_repo(repo_name, target_dir):
    """Clone or pull a repository."""
    try:
        repo_path = os.path.join(target_dir, repo_name)
        if os.path.exists(repo_path):
            subprocess.run(['git', 'pull'], cwd=repo_path, check=True)
        else:
            subprocess.run(['git', 'clone', f'https://github.com/lmtoy/{repo_name}.git', repo_path], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error updating repository {repo_name}: {str(e)}")
        return False 

def update_single_repo(pid, target_dir):
    """Update a single repository by its project ID."""
    try:
        project_name = f"lmtoy_{pid}"
        project_path = os.path.join(target_dir, project_name)
        
        if not os.path.exists(project_path):
            logger.error(f"Project directory does not exist: {project_path}")
            return False, f"Project directory not found: {pid}"
            
        subprocess.run(['git', 'pull'], cwd=project_path, check=True)
        return True, f"Successfully updated project {pid}"
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Error updating project {pid}: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error updating project {pid}: {str(e)}"
        logger.error(error_msg)
        return False, error_msg 