# Test Files

This directory contains test scripts and utility scripts for the pipeline_web application.

## Test Scripts

### Authentication Tests
- **test_csv_auth.py** - Tests the basic CSV authentication system
- **test_pid_auth.py** - Tests PID-based authentication functionality
- **test_app_integration.py** - Tests that PID authentication works with the main app
- **test_app_login.py** - Tests app login integration with CSV authentication
- **test_web_login.py** - Tests web app authentication for specific PIDs
- **test_specific_pid.py** - Debug script for testing specific PID login issues

### Utility Scripts
- **pid_login.py** - Simple command-line PID-based login interface
- **update_csv_config.py** - Script to update CSV authentication configuration in config.yaml

## Running Tests

To run any test script, navigate to the project root directory and run:

```bash
python tests/test_script_name.py
```

For example:
```bash
python tests/test_csv_auth.py
```

## Notes

- All test scripts are designed to work from the project root directory
- They automatically add the current directory to the Python path
- Test scripts use the CSV file specified in config.yaml
- Some scripts require the CSV file to be present in the project root 