# LMT Pipeline Web

## Introduction

This web application serves as an interface for managing pipeline jobs and configurations for the LMT (Large Millimeter Telescope) project. The application provides a user-friendly web interface for project management, session handling, and job submission with PID-based authentication.

## Features

- **PID-based Authentication**: Secure login using Project IDs (PIDs) with CSV-based user management
- **Session Management**: Create, clone, and manage project sessions
- **Runfile Management**: View, edit, clone, and delete runfiles
- **Job Submission**: Submit pipeline jobs with email notifications
- **Job Status Tracking**: Monitor job execution status
- **Table Management**: Edit, delete, and clone table rows
- **Admin Interface**: Administrative tools for user and system management

## Project Structure

```
pipeline_web/
├── app.py                 # Main Dash application
├── my_server.py          # Flask server configuration
├── config.yaml           # Application configuration
├── config_loader.py      # Configuration loading utilities
├── db/                   # Database and authentication modules
│   ├── csv_auth.py       # CSV-based authentication system
│   ├── csv_users_mgt.py  # CSV user management utilities
│   └── users_mgt.py      # Database user management
├── tests/                # Test scripts and utilities
│   ├── test_csv_auth.py  # CSV authentication tests
│   ├── test_pid_auth.py  # PID authentication tests
│   ├── pid_login.py      # Command-line login interface
│   └── update_csv_config.py # CSV configuration utility
├── views/                # Application views and layouts
├── utils/                # Utility functions
├── assets/               # Static assets (CSS, JS, images)
└── logs/                 # Application logs
```

## Setup

### Environment and Dependencies

1. **Create a virtual environment and install dependencies:**
    ```shell
    python3 -m venv env
    source env/bin/activate
    pip install -r requirements.txt
    ```

2. **Configure the application:**
    - Modify `config.yaml` to specify your environment settings:
      ```yaml
      path:
        work_lmt: /path/to/your/work/directory
        python_path: /path/to/your/python/environment
      ssh:
        username: your_ssh_username
        hostname: your_remote_server
      authentication:
        csv_path: .
        csv_file: lmt_archive_user_info_20250702.csv
      ```

3. **Set up CSV Authentication:**
    - The application uses a CSV file for PID-based authentication
    - Ensure your CSV file contains columns: `username`, `password`, `api_token`, `expiration`
    - Use the utility script to update CSV configuration:
      ```shell
      python tests/update_csv_config.py
      ```

4. **Database Setup (Optional):**
    - The repository includes a `users.db` for fallback authentication
    - To create a new database or add users, use `db/users_mgt.py`

## Running the Application

### Local Development
```shell
python app.py --port 8080
```
The application will be accessible at [http://127.0.0.1:8080](http://127.0.0.1:8080)

### Remote Server Setup
For remote server deployment, use SSH port forwarding:
```shell
# Add to your ~/.ssh/config
Host your-server
    LocalForward 5000 127.0.0.1:8000
```

Then access via [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Authentication

### PID-based Login
- Use your Project ID (PID) to log in
- Example: PID = '2023-S1-US-17', Password = 'your_password'
- The system supports both CSV-based and database authentication

### CSV Authentication Features
- Loads user data from CSV file specified in `config.yaml`
- Supports password hashing for security
- Includes API token and expiration date fields
- Automatic fallback to database authentication

### Testing Authentication
Run authentication tests to verify your setup:
```shell
# Test CSV authentication
python tests/test_csv_auth.py

# Test specific PID
python tests/test_specific_pid.py

# Test web app integration
python tests/test_app_integration.py
```

## Usage

### Login
1. Enter your PID (Project ID) in the login form
2. Enter your password
3. Optionally check "Remember Me" for persistent login
4. Click "Login" to access the application

### Session Management
- **Default Session**: `session-0` is the base session
- **Clone Session**: Click "CLONE SESSION" and enter a new session number
- **Delete Session**: Select a session and click "DELETE" to remove it
- **Session Selection**: Choose different sessions to work with different configurations

### Runfile Management
- **View Runfiles**: Available runfiles are displayed after selecting a session
- **View Content**: Click on a runfile to see its contents
- **Clone Runfile**: Click "CLONE" to create a copy
- **Delete Runfile**: Click "DELETE" to remove a runfile

### Table Management
- **Select Rows**: Click on table rows to select them
- **Edit Rows**: Modify selected row data
- **Delete Rows**: Remove selected rows
- **Clone Rows**: Create copies of selected rows

### Job Submission
1. Select a runfile
2. Enter a valid email address for notifications
3. Click "SUBMIT JOB" to start the pipeline job
4. Monitor job status using "JOB STATUS"

### Job Status
- Track job execution progress
- View job logs and output
- Monitor job completion status

## Testing

The project includes comprehensive test scripts in the `tests/` directory:

### Authentication Tests
- `test_csv_auth.py` - Basic CSV authentication functionality
- `test_pid_auth.py` - PID-based authentication tests
- `test_app_integration.py` - Integration with main application
- `test_web_login.py` - Web interface authentication tests
- `test_specific_pid.py` - Debug specific PID issues

### Utility Scripts
- `pid_login.py` - Command-line login interface
- `update_csv_config.py` - Update CSV configuration settings

### Running Tests
```shell
# Run all tests
python tests/test_csv_auth.py
python tests/test_pid_auth.py
python tests/test_app_integration.py

# Test specific functionality
python tests/pid_login.py
python tests/update_csv_config.py
```

## Configuration

### CSV Authentication
The CSV authentication system is configured in `config.yaml`:
```yaml
authentication:
  csv_path: .
  csv_file: lmt_archive_user_info_20250702.csv
```

### SSH Configuration
Remote server access settings:
```yaml
ssh:
  username: your_username
  hostname: your_server.com
```

### Path Configuration
Directory and environment settings:
```yaml
path:
  work_lmt: /path/to/work/directory
  python_path: /path/to/python/environment
```

## Troubleshooting

### Authentication Issues
1. Verify CSV file exists and is readable
2. Check CSV file format (username, password, api_token, expiration)
3. Ensure passwords are properly hashed
4. Test with `python tests/test_specific_pid.py`

### Connection Issues
1. Verify SSH configuration in `config.yaml`
2. Check network connectivity to remote server
3. Ensure proper port forwarding setup

### Job Submission Issues
1. Verify email configuration
2. Check runfile format and content
3. Monitor job logs for error messages

## Documentation

- **Flow Chart**: [Pipeline Web Flow Chart](./Pipeline_web_slide.pdf)
- **Configuration**: See `config.yaml` for all available options
- **API Documentation**: Check individual module docstrings

## Support

For issues and questions:
1. Check the test scripts for debugging
2. Review application logs in the `logs/` directory
3. Verify configuration settings in `config.yaml`