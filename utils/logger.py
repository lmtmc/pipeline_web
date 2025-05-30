import logging
import sys
import os
from datetime import datetime

# Create logs directory if it doesn't exist
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

def setup_logger():
    # create logger
    logger = logging.getLogger('app')
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    c_handler = logging.StreamHandler(sys.stdout)
    f_handler = logging.FileHandler(os.path.join(log_dir, 'app.log'))
    c_handler.setLevel(logging.DEBUG)
    f_handler.setLevel(logging.DEBUG)

    # create formatter
    c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    # add handlers to logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    return logger

# Create main logger
logger = setup_logger()

# Create login logger
login_logger = logging.getLogger('login')
login_logger.setLevel(logging.INFO)
login_handler = logging.FileHandler(os.path.join(log_dir, 'login.log'))
login_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
login_logger.addHandler(login_handler)

# Create session logger
session_logger = logging.getLogger('session')
session_logger.setLevel(logging.INFO)
session_handler = logging.FileHandler(os.path.join(log_dir, 'session.log'))
session_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
session_logger.addHandler(session_handler)

def log_login_attempt(username, success, ip_address=None, user_agent=None):
    """Log login attempts with details"""
    status = "SUCCESS" if success else "FAILED"
    message = f"Login attempt - Username: {username} - Status: {status}"
    if ip_address:
        message += f" - IP: {ip_address}"
    if user_agent:
        message += f" - User Agent: {user_agent}"
    
    login_logger.info(message)

def log_session_start(username, session_id, ip_address=None):
    """Log when a session starts"""
    message = f"Session started - Username: {username} - Session ID: {session_id}"
    if ip_address:
        message += f" - IP: {ip_address}"
    session_logger.info(message)

def log_session_end(username, session_id, duration, ip_address=None):
    """Log when a session ends"""
    message = f"Session ended - Username: {username} - Session ID: {session_id} - Duration: {duration}"
    if ip_address:
        message += f" - IP: {ip_address}"
    session_logger.info(message)

def log_session_list(sessions):
    """Log the current list of active sessions"""
    if not sessions:
        session_logger.info("No active sessions")
        return
    
    session_logger.info("Active Sessions:")
    for session in sessions:
        message = f"Session ID: {session.get('session_id')} - Username: {session.get('username')}"
        if 'start_time' in session:
            message += f" - Start Time: {session['start_time']}"
        if 'ip_address' in session:
            message += f" - IP: {session['ip_address']}"
        session_logger.info(message)
