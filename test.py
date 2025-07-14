import os
import subprocess
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def run_git_command(cmd: list, cwd: str, timeout: int = 30) -> Tuple[bool, str]:
    """Run a git command with improved error handling and timeout."""
    try:
        full_cmd = ['git'] + cmd
        result = subprocess.run(
            full_cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )

        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip() or result.stdout.strip()

    except subprocess.TimeoutExpired:
        return False, f"Git command timed out after {timeout} seconds"
    except Exception as e:
        return False, f"Git command failed: {str(e)}"


def get_default_branch(repo_path: str) -> str:
    """Get the default branch name more efficiently."""
    # First, try to get it from the remote HEAD reference
    success, output = run_git_command(['symbolic-ref', 'refs/remotes/origin/HEAD'], repo_path)
    if success and output.startswith('refs/remotes/origin/'):
        return output.split('/')[-1]

    # Fallback: check local branches
    success, output = run_git_command(['branch', '-r'], repo_path)
    if success:
        for line in output.split('\n'):
            line = line.strip()
            if 'origin/main' in line:
                return 'main'
            elif 'origin/master' in line:
                return 'master'

    # Final fallback
    return 'main'
repo_path='/home/lmt/work_lmt/lmtoy_run/lmtoy_2018-S1-MU-8'
print(get_default_branch(repo_path))
#
def is_git_repo(path: str) -> bool:
    """Check if a directory is a git repository."""
    return os.path.exists(os.path.join(path, '.git'))
print(is_git_repo(repo_path))
def update_single_repo(repo_name: str, work_dir: str, base_url: str) -> Tuple[bool, str]:
    """Update a single repository with improved efficiency.

    Args:
        repo_name: Name of the repository to update
        work_dir: Working directory for the repository
        base_url: Base URL for the repository (e.g., LMT_BASE_URL)

    Returns:
        Tuple of (success, message)
    """
    repo_path = os.path.join(work_dir, repo_name)
    repo_url = f"{base_url}/{repo_name}"

    try:
        # Ensure work directory exists
        os.makedirs(work_dir, exist_ok=True)

        # If repository doesn't exist, clone it
        if not os.path.exists(repo_path):
            print(f"Cloning {repo_name}...")
            success, message = run_git_command(['clone', repo_url, repo_name], work_dir)
            if not success:
                return False, f"Failed to clone {repo_name}: {message}"
            print(f"Successfully cloned {repo_name}")
            return True, f"Repository {repo_name} cloned successfully"

        # Verify it's actually a git repository
        if not is_git_repo(repo_path):
            return False, f"{repo_path} exists but is not a git repository"

        # Get current branch and default branch
        success, current_branch = run_git_command(['branch', '--show-current'], repo_path)
        if not success:
            return False, f"Failed to get current branch: {current_branch}"

        # Fetch latest changes first
        print(f"Fetching latest changes for {repo_name}...")
        success, message = run_git_command(['fetch', 'origin'], repo_path)
        if not success:
            return False, f"Failed to fetch: {message}"

        # Get default branch
        default_branch = get_default_branch(repo_path)
        print(f"Default branch for {repo_name}: {default_branch}")

        # Switch to default branch if not already on it
        if current_branch != default_branch:
            success, message = run_git_command(['checkout', default_branch], repo_path)
            if not success:
                # Try to create and checkout the branch
                success, message = run_git_command(['checkout', '-b', default_branch, f'origin/{default_branch}'],
                                                   repo_path)
                if not success:
                    return False, f"Failed to checkout {default_branch}: {message}"

        # Check if we're behind the remote
        success, output = run_git_command(['status', '--porcelain=v1', '--branch'], repo_path)
        if success and 'behind' in output:
            print(f"Pulling latest changes for {repo_name}...")
            success, message = run_git_command(['pull', '--ff-only'], repo_path)
            if not success:
                return False, f"Failed to pull changes: {message}"
            print(f"Updated {repo_name} successfully")
        else:
            print(f"{repo_name} is already up to date")

        return True, f"Repository {repo_name} updated successfully"

    except Exception as e:
        error_msg = f"Error updating repository {repo_name}: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
repo_name='lmtoy_2018-S1-MU-8'
work_dir='/home/lmt/work_lmt/lmtoy_run'

print('--- Updating single repository ---',update_single_repo(repo_name,work_dir,base_url='https://github.com/lmtoy/'))
#
#
# def update_multiple_repos(repo_names: list, work_dir: str, base_url: str) -> dict:
#     """Update multiple repositories efficiently.
#
#     Args:
#         repo_names: List of repository names to update
#         work_dir: Working directory for repositories
#         base_url: Base URL for repositories
#
#     Returns:
#         Dictionary with results for each repository
#     """
#     results = {}
#
#     for repo_name in repo_names:
#         print(f"\n--- Processing {repo_name} ---")
#         success, message = update_single_repo(repo_name, work_dir, base_url)
#         results[repo_name] = {
#             'success': success,
#             'message': message
#         }
#
#         if success:
#             print(f"✓ {message}")
#         else:
#             print(f"✗ {message}")
#
#     return results
#
#
# # Example usage:
# if __name__ == "__main__":
#     # Example configuration
#     WORK_DIR = "./repositories"
#     BASE_URL = "https://github.com/lmtoy"  # Replace with your base URL
#     REPOS = ["lmtoy_2018-S1-MU-8"]  # Replace with your repository names
#
#     # Update all repositories
#     results = update_multiple_repos(REPOS, WORK_DIR, BASE_URL)
#
#     # Print summary
#     print("\n--- Summary ---")
#     successful = sum(1 for r in results.values() if r['success'])
#     total = len(results)
#     print(f"Successfully updated {successful}/{total} repositories")
#
#     # Print failed repositories
#     failed = [name for name, result in results.items() if not result['success']]
#     if failed:
#         print(f"Failed repositories: {', '.join(failed)}")