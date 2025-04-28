import dash
from flask import Flask
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
import dash_bootstrap_components as dbc
from datetime import datetime
from config_loader import load_config
from flask_caching import Cache
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
try:
    config = load_config()
except Exception as e:
    logger.error(f"Error loading configuration: {e}")
    config = {'path': {'prefix': '/'}}

# Initialize Flask app with security headers
server = Flask(__name__)
server.config.update(
    SECRET_KEY='my_secret_key',
    SQLALCHEMY_DATABASE_URI='sqlite:///users.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)

# Initialize cache
cache = Cache(server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache',
    'CACHE_DEFAULT_TIMEOUT': 300
})

db = SQLAlchemy(server)

# dash app configuration
prefix = config['path']['prefix']
app = dash.Dash(
    __name__,
    server=server,
    requests_pathname_prefix=prefix,
    routes_pathname_prefix=prefix,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.FONT_AWESOME,
        dbc.icons.BOOTSTRAP,
        'https://cdn.jsdelivr.net/npm/ag-grid-community/styles/ag-grid.css',
        'https://cdn.jsdelivr.net/npm/ag-grid-community/styles/ag-theme-alpine.css'
    ],
    external_scripts=[
        'https://cdn.jsdelivr.net/npm/ag-grid-community/dist/ag-grid-community.min.js'
    ],
    meta_tags=[
        {'charset': 'utf-8'},
        {'name': 'viewport', 'content': 'width=device-width, initial-scale=1, shrink-to-fit=yes'},
        {'http-equiv': 'X-UA-Compatible', 'content': 'IE=edge'}
    ],
    prevent_initial_callbacks="initial_duplicate",
    suppress_callback_exceptions=True,
    update_title=None
)

# Flask-Login configuration
login_manager = LoginManager(server)
login_manager.login_view = f'{prefix}/login'
login_manager.session_protection = 'strong'

# Create User class with UserMixin
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, index=True)
    email = db.Column(db.String(50), unique=True, index=True)
    password = db.Column(db.String(80))
    is_admin = db.Column(db.Boolean, default=False)
    jobs = db.relationship('Job', backref="user", lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, username, password, email, is_admin=False):
        self.username = username
        self.password = generate_password_hash(password, method='pbkdf2:sha256')
        self.email = email
        self.is_admin = is_admin

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Job(db.Model):
    __tablename__ = 'job'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, index=True)
    session = db.Column(db.Text, nullable=False)
    create_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    username = db.Column(db.String(50), db.ForeignKey('user.username', ondelete='CASCADE'), nullable=False)

    def __init__(self, title, session, create_time, username):
        self.title = title
        self.session = session
        self.create_time = create_time
        self.username = username

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {
            'id': self.id,
            'title': self.title,
            'create_time': self.create_time.isoformat(),
            'username': self.username
        }

# Create database tables
with server.app_context():
    db.create_all()

@login_manager.user_loader
@cache.memoize(timeout=300)  # Cache user lookup for 5 minutes
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        logger.error(f"Error loading user {user_id}: {e}")
        return None

# Error handlers
@server.errorhandler(404)
def not_found_error(error):
    return {'error': 'Not Found'}, 404

@server.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return {'error': 'Internal Server Error'}, 500
