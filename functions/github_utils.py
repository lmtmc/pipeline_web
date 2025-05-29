import requests
import subprocess
import logging
from functools import lru_cache
import os

# Configure logging
logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_github_repos(api_url, repo_prefix):
    """Get list of repositories from GitHub API."""
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        repos = response.json()
        
        # Filter repositories:
        # 1. Must start with repo_prefix
        # 2. Must not be a test repository
        # 3. Must be a valid project repository (contains valid project ID format)
        valid_repos = []
        for repo in repos:
            name = repo['name']
            if (name.startswith(repo_prefix) and 
                'test' not in name.lower() and 
                len(name.replace(repo_prefix, '')) > 0):  # Ensure there's a project ID after the prefix
                valid_repos.append(name)
        
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