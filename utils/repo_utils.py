import os
import subprocess
from datetime import datetime
import logging
from typing import Dict, List, Tuple, Optional
from config_loader import load_config

# Create cache directory if it doesn't exist
CACHE_DIR = 'cache'  # Use relative path in the application root
if not os.path.exists(CACHE_DIR):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
    except Exception as e:
        logging.error(f'Error creating cache directory: {str(e)}')

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG to see all updates
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('repo_utils.log'),
        logging.StreamHandler()  # Add console output
    ]
)
logger = logging.getLogger(__name__)

# Load configuration
try:
    config = load_config()
except Exception as e:
    logger.error(f"Error loading configuration: {e}")
    config = {}

# Constants
LMT_BASE_URL = "https://github.com/lmtoy"
WORK_DIR = config.get('path', {}).get('work_lmt', '')
LMTOY_RUN_DIR = os.path.join(WORK_DIR, 'lmtoy_run')
MAKEFILE_PATH = os.path.join(LMTOY_RUN_DIR, 'Makefile')
GITHUB_API_URL = config.get('github', {}).get('api_url', 'https://api.github.com/orgs/lmtoy/repos')
REPO_PREFIX = config.get('github', {}).get('repo_prefix', 'lmtoy_')


def run_git_command(cmd: List[str], cwd: str) -> Tuple[bool, str]:
    """Run a git command and return its result.

    Args:
        cmd: List of command arguments
        cwd: Working directory for the command

    Returns:
        Tuple of (success, output/error message)
    """
    try:
        logger.debug(f"Running git command: {' '.join(['git', '-C', cwd] + cmd)}")
        result = subprocess.run(['git', '-C', cwd] + cmd,
                                capture_output=True, text=True)
        if result.returncode != 0:
            logger.debug(f"Git command failed with error: {result.stderr}")
            return False, result.stderr
        logger.debug(f"Git command output: {result.stdout}")
        return True, result.stdout
    except Exception as e:
        logger.debug(f"Exception in git command: {str(e)}")
        return False, str(e)


def parse_makefile() -> List[str]:
    """Parse the Makefile to extract repository names.

    Returns:
        List of valid repository names
    """
    if not os.path.exists(MAKEFILE_PATH):
        logger.error(f"Makefile not found at: {MAKEFILE_PATH}")
        return []

    try:
        with open(MAKEFILE_PATH, 'r') as f:
            content = f.read()

        all_repos = []
        for line in content.split('\n'):
            line = line.strip()

            # Skip empty lines, comments, and lines ending with colon
            if not line or line.startswith('#') or line.endswith(':'):
                continue

            # Remove backslash if present
            if line.endswith('\\'):
                line = line[:-1].strip()

            # Filter valid repository names
            repos = [repo.strip() for repo in line.split()
                     if repo.strip()
                     and repo.startswith('lmtoy_')
                     and 'commission' not in repo.lower()
                     and repo != 'lmtoy_run']
            all_repos.extend(repos)

        return all_repos
    except Exception as e:
        logger.error(f"Error reading Makefile at {MAKEFILE_PATH}: {str(e)}")
        return []


def get_lmt_repos_by_year() -> Dict[str, List[str]]:
    """Get LMT repositories organized by year from the Makefile configuration.
    Only includes repositories that exist in the filesystem.

    Returns:
        Dictionary with years as keys and lists of repository names as values
    """
    repos_by_year = {}

    # Ensure lmtoy_run directory exists
    os.makedirs(LMTOY_RUN_DIR, exist_ok=True)

    # Get repositories from Makefile
    all_repos = parse_makefile()

    # Organize repositories by year, only including those that exist
    for repo in all_repos:
        repo_path = os.path.join(LMTOY_RUN_DIR, repo)
        if not os.path.exists(repo_path):
            logger.info(f"Skipping non-existent repository: {repo}")
            continue

        try:
            year = repo.split('_')[1].split('-')[0]
            if year.isdigit():
                if year not in repos_by_year:
                    repos_by_year[year] = []
                repos_by_year[year].append(repo)
        except Exception as e:
            logger.warning(f"Could not extract year from repository name: {repo}")
            continue

    return repos_by_year


def get_single_repo_status(repo_name: str) -> tuple[bool, str]:
    """Check the status of a single repository."""
    logger.debug(f"Checking status for repository: {repo_name}")
    repo_path = os.path.join(LMTOY_RUN_DIR, repo_name)
    if not os.path.exists(repo_path):
        logger.debug(f"Repository path does not exist: {repo_path}")
        return False, "Not tracked"

    success, output = run_git_command(['status', '-uno'], repo_path)
    if not success:
        logger.debug(f"Failed to get repository status: {output}")
        return False, "Error checking status"

    if "Your branch is behind" in output:
        logger.debug(f"Repository {repo_name} needs update")
        return True, "Needs update"
    logger.debug(f"Repository {repo_name} is up to date")
    return True, "Up to date"


def get_all_repos_status() -> str:
    """Check the status of all repositories and return a summary."""
    repos = get_lmt_repos_by_year()  # Only returns existing repos
    total = sum(len(year_repos) for year_repos in repos.values())
    up_to_date = 0
    needs_update = 0

    for year_repos in repos.values():
        for repo in year_repos:
            repo_path = os.path.join(LMTOY_RUN_DIR, repo)
            success, output = run_git_command(['status', '-uno'], repo_path)
            if not success:
                continue

            if "Your branch is behind" in output:
                needs_update += 1
            else:
                up_to_date += 1

    return f"Total: {total}, Up to date: {up_to_date}, Needs update: {needs_update}"


def get_repo_status(repo_name: Optional[str] = None) -> str:
    """Get the status of a specific repository or all repositories."""
    try:
        if repo_name:
            return get_single_repo_status(repo_name)
        else:
            return get_all_repos_status()
    except Exception as e:
        logger.error(f"Error checking repository status: {str(e)}")
        return "Error checking status"


def update_single_repo(repo_name: str, work_dir: str) -> Tuple[bool, str]:
    """Update a single repository.

    Args:
        repo_name: Name of the repository to update
        work_dir: Working directory for the repository

    Returns:
        Tuple of (success, message)
    """
    try:
        logger.debug(f"Starting update for repository: {repo_name}")
        repo_path = os.path.join(work_dir, repo_name)

        # If repository doesn't exist, clone it
        if not os.path.exists(repo_path):
            logger.debug(f"Repository does not exist, cloning: {repo_name}")
            success, message = run_git_command(['clone', f"{LMT_BASE_URL}/{repo_name}", repo_path], work_dir)
            if not success:
                logger.debug(f"Failed to clone repository: {message}")
                return False, message

        # Set up tracking for main branch
        logger.debug("Setting up tracking for main branch")
        success, message = run_git_command(['branch', '--set-upstream-to=origin/main', 'main'], repo_path)
        if not success:
            logger.debug(f"Failed to set up tracking: {message}")
            return False, message

        # Pull latest changes
        logger.debug("Pulling latest changes")
        success, message = run_git_command(['pull', 'origin', 'main'], repo_path)
        if not success:
            logger.debug(f"Failed to pull changes: {message}")
            return False, message

        logger.debug(f"Successfully updated repository: {repo_name}")
        return True, f"Repository {repo_name} updated successfully"
    except Exception as e:
        error_msg = f"Error updating repository {repo_name}: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def pull_lmtoy_run() -> Tuple[bool, str]:
    """Pull latest changes from lmtoy_run repository.

    Returns:
        Tuple of (success, message)
    """
    try:
        # Check if lmtoy_run exists, if not clone it
        if not os.path.exists(LMTOY_RUN_DIR):
            success, message = run_git_command(['clone', f"{LMT_BASE_URL}/lmtoy_run", LMTOY_RUN_DIR], WORK_DIR)
            if not success:
                return False, message

        # Set up tracking for main branch
        success, message = run_git_command(['branch', '--set-upstream-to=origin/main', 'main'], LMTOY_RUN_DIR)
        if not success:
            return False, message

        # Pull latest changes
        success, message = run_git_command(['pull', 'origin', 'main'], LMTOY_RUN_DIR)
        if not success:
            return False, message

        return True, "Successfully pulled latest changes from lmtoy_run"
    except Exception as e:
        error_msg = f"Error pulling latest changes: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def get_all_repos() -> Dict[str, List[str]]:
    """Get all repositories from the Makefile.

    Returns:
        Dictionary with years as keys and lists of repository names as values
    """
    return get_lmt_repos_by_year() 