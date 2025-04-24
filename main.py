import os
import time
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import threading
import schedule
import logging
from functools import wraps
import zipfile
import shutil
import pickle

# Flask and authentication imports
from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import re
from flask_wtf.csrf import CSRFProtect, generate_csrf

# Create necessary directories
os.makedirs('logs', exist_ok=True)
os.makedirs('config', exist_ok=True)
os.makedirs('config/ssl', exist_ok=True)
os.makedirs('data', exist_ok=True)
os.makedirs('backups', exist_ok=True)
os.makedirs('models/saved_models', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/system.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create Backup System class
class BackupSystem:
    """System for backing up and restoring application data"""
    
    def __init__(self, config_dir='config', data_dir='data', backup_dir='backups'):
        """Initialize the backup system
        
        Args:
            config_dir: Directory containing configuration files
            data_dir: Directory containing data files
            backup_dir: Directory to store backups
        """
        self.config_dir = config_dir
        self.data_dir = data_dir
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
        logger.info(f"Backup system initialized with backup directory: {backup_dir}")
    
    def create_backup(self):
        """Create a backup of configuration and data
        
        Returns:
            str: Path to the created backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{self.backup_dir}/backup_{timestamp}.zip"
        
        try:
            # Ensure backup directory exists
            os.makedirs(self.backup_dir, exist_ok=True)
            
            with zipfile.ZipFile(backup_filename, 'w') as backup_zip:
                # Backup configuration files
                if os.path.exists(self.config_dir):
                    for root, _, files in os.walk(self.config_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                if os.path.isfile(file_path):
                                    arc_name = os.path.relpath(file_path)
                                    backup_zip.write(file_path, arc_name)
                            except Exception as e:
                                logger.warning(f"Failed to backup file {file_path}: {e}")
                else:
                    logger.warning(f"Configuration directory {self.config_dir} not found")
                
                # Backup data files
                if os.path.exists(self.data_dir):
                    for root, _, files in os.walk(self.data_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                if os.path.isfile(file_path):
                                    arc_name = os.path.relpath(file_path)
                                    backup_zip.write(file_path, arc_name)
                            except Exception as e:
                                logger.warning(f"Failed to backup file {file_path}: {e}")
                else:
                    logger.warning(f"Data directory {self.data_dir} not found")
            
            logger.info(f"Backup created: {backup_filename}")
            return backup_filename
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            if os.path.exists(backup_filename):
                try:
                    os.remove(backup_filename)
                except:
                    pass
            raise
    
    def restore_backup(self, backup_file):
        """Restore from a backup file
        
        Args:
            backup_file: Path to the backup file
            
        Returns:
            bool: True if restoration was successful
        """
        if not os.path.exists(backup_file):
            logger.error(f"Backup file {backup_file} not found")
            return False
            
        # Validate the backup file
        if not zipfile.is_zipfile(backup_file):
            logger.error(f"File {backup_file} is not a valid ZIP file")
            return False
            
        # Create temporary restore directory
        restore_dir = f"{self.backup_dir}/restore_temp"
        if os.path.exists(restore_dir):
            shutil.rmtree(restore_dir)
        os.makedirs(restore_dir, exist_ok=True)
        
        try:
            # Extract backup
            with zipfile.ZipFile(backup_file, 'r') as backup_zip:
                backup_zip.extractall(restore_dir)
            
            # Validate backup structure
            if not (os.path.exists(f"{restore_dir}/{self.config_dir}") or 
                   os.path.exists(f"{restore_dir}/{self.data_dir}")):
                logger.error(f"Backup {backup_file} does not contain required directories")
                shutil.rmtree(restore_dir)
                return False
            
            # Create backup of current data before restoration
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pre_restore_backup = f"{self.backup_dir}/pre_restore_{timestamp}.zip"
            
            with zipfile.ZipFile(pre_restore_backup, 'w') as backup_zip:
                # Backup configuration files
                if os.path.exists(self.config_dir):
                    for root, _, files in os.walk(self.config_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arc_name = os.path.relpath(file_path)
                            backup_zip.write(file_path, arc_name)
                
                # Backup data files
                if os.path.exists(self.data_dir):
                    for root, _, files in os.walk(self.data_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arc_name = os.path.relpath(file_path)
                            backup_zip.write(file_path, arc_name)
            
            # Restore configuration
            if os.path.exists(f"{restore_dir}/{self.config_dir}"):
                if os.path.exists(self.config_dir):
                    shutil.rmtree(self.config_dir)
                shutil.copytree(f"{restore_dir}/{self.config_dir}", self.config_dir)
                
            # Restore data
            if os.path.exists(f"{restore_dir}/{self.data_dir}"):
                if os.path.exists(self.data_dir):
                    shutil.rmtree(self.data_dir)
                shutil.copytree(f"{restore_dir}/{self.data_dir}", self.data_dir)
                
            # Clean up
            shutil.rmtree(restore_dir)
            
            logger.info(f"Restored from backup: {backup_file}")
            logger.info(f"Pre-restore backup created at: {pre_restore_backup}")
            return True
            
        except Exception as e:
            logger.error(f"Error during backup restoration: {e}")
            if os.path.exists(restore_dir):
                shutil.rmtree(restore_dir)
            return False

# Create user database manager
class UserDatabase:
    """Manages persistent user storage"""
    
    def __init__(self, db_file='data/users.db'):
        """Initialize the user database
        
        Args:
            db_file: Path to the database file
        """
        self.db_file = db_file
        self.users = {}
        self.lock = threading.Lock()  # Thread safety for database operations
        self.load()
    
    def load(self):
        """Load users from file"""
        with self.lock:
            try:
                if os.path.exists(self.db_file):
                    with open(self.db_file, 'rb') as f:
                        self.users = pickle.load(f)
                    logger.info(f"Loaded {len(self.users)} users from database")
                else:
                    logger.info("No existing user database found, creating new")
                    self.users = {}
                    # Create default admin user
                    self.users['admin@example.com'] = {
                        'password': generate_password_hash('Admin123'),
                        'role': 'admin'
                    }
                    self.save()
            except Exception as e:
                logger.error(f"Error loading user database: {e}")
                # Create backup of corrupted file if it exists
                if os.path.exists(self.db_file):
                    corrupt_backup = f"{self.db_file}.corrupted.{int(time.time())}"
                    try:
                        shutil.copy2(self.db_file, corrupt_backup)
                        logger.info(f"Created backup of corrupted database: {corrupt_backup}")
                    except Exception as backup_err:
                        logger.error(f"Failed to backup corrupted database: {backup_err}")
                
                # Reset to default state
                self.users = {
                    'admin@example.com': {
                        'password': generate_password_hash('Admin123'),
                        'role': 'admin'
                    }
                }
                self.save()
    
    def save(self):
        """Save users to file"""
        with self.lock:
            try:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
                
                # Create a temporary file first
                temp_file = f"{self.db_file}.tmp"
                with open(temp_file, 'wb') as f:
                    pickle.dump(self.users, f)
                
                # Rename temp file to target (atomic operation on most systems)
                os.replace(temp_file, self.db_file)
                
                logger.info(f"Saved {len(self.users)} users to database")
            except Exception as e:
                logger.error(f"Error saving user database: {e}")
                # Try to clean up temp file if it exists
                if os.path.exists(f"{self.db_file}.tmp"):
                    try:
                        os.remove(f"{self.db_file}.tmp")
                    except:
                        pass
                raise
    
    def add_user(self, email, password_hash, role='user'):
        """Add a new user
        
        Args:
            email: User email
            password_hash: Hashed password
            role: User role (default: user)
            
        Returns:
            bool: True if successful
        """
        with self.lock:
            if email in self.users:
                return False
            
            self.users[email] = {
                'password': password_hash,
                'role': role
            }
            self.save()
            return True
    
    def get_user(self, email):
        """Get user by email
        
        Args:
            email: User email
            
        Returns:
            dict: User data or None
        """
        with self.lock:
            return self.users.get(email)
    
    def verify_password(self, email, password):
        """Verify user password
        
        Args:
            email: User email
            password: Plain password to check
            
        Returns:
            bool: True if password matches
        """
        user = self.get_user(email)
        if not user:
            return False
        
        return check_password_hash(user['password'], password)
    
    def is_admin(self, email):
        """Check if user is an admin
        
        Args:
            email: User email
            
        Returns:
            bool: True if user is an admin
        """
        user = self.get_user(email)
        if not user:
            return False
        
        return user.get('role') == 'admin'

# Create input validation system
class InputValidator:
    """System for validating user inputs"""
    
    @staticmethod
    def validate_email(email):
        """Validate email format
        
        Args:
            email: Email address to validate
            
        Returns:
            bool: True if valid
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_password(password):
        """Validate password strength
        
        Args:
            password: Password to validate
            
        Returns:
            tuple: (bool, str) - Success flag and message (if failed)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
            
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
            
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
            
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
            
        return True, ""
    
    @staticmethod
    def sanitize_input(input_str):
        """Sanitize input to prevent XSS
        
        Args:
            input_str: Input string to sanitize
            
        Returns:
            str: Sanitized string
        """
        if not isinstance(input_str, str):
            return input_str
            
        # Dictionary of replacements
        replacements = {
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;',
            '&': '&amp;',
            '/': '&#47;',
            '\\': '&#92;'
        }
        
        # Replace potentially dangerous characters
        sanitized = input_str
        for char, replacement in replacements.items():
            sanitized = sanitized.replace(char, replacement)
            
        # Remove JavaScript event handlers
        js_event_pattern = r'on\w+="[^"]*"'
        sanitized = re.sub(js_event_pattern, '', sanitized)
        
        # Remove embedded script tags
        script_pattern = r'<script>.*?</script>'
        sanitized = re.sub(script_pattern, '', sanitized, flags=re.DOTALL)
        
        return sanitized.strip()

# Create Flask app with proper template and static folders
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Setup CSRF protection
csrf = CSRFProtect(app)

# Setup secret key from file or generate a new one
def setup_secret_key():
    """Set up a persistent secret key for the Flask application"""
    key_file = 'config/flask_secret_key.txt'
    
    # Create the config directory if it doesn't exist
    os.makedirs(os.path.dirname(key_file), exist_ok=True)
    
    if os.path.exists(key_file):
        # Read existing secret key
        try:
            with open(key_file, 'r') as f:
                app.config['SECRET_KEY'] = f.read().strip()
            logger.info("Loaded existing Flask secret key")
            return
        except Exception as e:
            logger.error(f"Failed to load existing secret key: {e}")
    
    # Generate a new secret key
    new_key = secrets.token_hex(32)  # 32 bytes = 256 bits
    app.config['SECRET_KEY'] = new_key
    
    # Save it to file
    try:
        with open(key_file, 'w') as f:
            f.write(new_key)
        logger.info("Generated and saved new Flask secret key")
    except Exception as e:
        logger.error(f"Failed to save new secret key: {e}. Using temporary key for this session.")

# Setup the secret key
setup_secret_key()

# Initialize user database
user_db = UserDatabase()

# Authentication decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login_page'))
        if not user_db.is_admin(session['user']):
            return render_template('error.html', error="Access Denied", 
                                 message="You do not have permission to access this area.")
        return f(*args, **kwargs)
    return decorated_function

# Flask routes
@app.route('/')
def index():
    """Home page route"""
    if 'user' in session:
        is_admin = user_db.is_admin(session['user'])
        return render_template('index.html', user=session['user'], is_admin=is_admin, csrf_token=generate_csrf())
    else:
        return redirect(url_for('login_page'))

@app.route('/login', methods=['GET'])
def login_page():
    """Login page route"""
    return render_template('login.html', csrf_token=generate_csrf())

@app.route('/register', methods=['GET'])
def register_page():
    """Registration page route"""
    return render_template('register.html', csrf_token=generate_csrf())

@app.route('/admin/backup', methods=['GET'])
@admin_required
def admin_backup_page():
    """Admin backup management page route"""
    # List existing backups
    backup_dir = 'backups'
    backup_files = []
    if os.path.exists(backup_dir):
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith('backup_') and f.endswith('.zip')]
        backup_files.sort(reverse=True)
    
    return render_template('admin/backup.html', backup_files=backup_files, csrf_token=generate_csrf())

@app.route('/logout')
def logout():
    """Logout route"""
    session.pop('user', None)
    return redirect(url_for('login_page'))

@app.route('/dashboard')
@login_required
def dashboard_web():
    """Web dashboard route"""
    return render_template('dashboard.html')

# API routes
@app.route('/api/login', methods=['POST'])
@csrf.exempt
def api_login():
    """API endpoint for login"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        email = InputValidator.sanitize_input(data.get('email', ''))
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        if user_db.verify_password(email, password):
            session['user'] = email
            return jsonify({'message': 'Login successful', 'csrf_token': generate_csrf()})
        
        return jsonify({'error': 'Invalid email or password'}), 401
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Server error during login'}), 500

@app.route('/api/register', methods=['POST'])
@csrf.exempt
def api_register():
    """API endpoint for registration"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        email = InputValidator.sanitize_input(data.get('email', ''))
        password = data.get('password', '')
        
        # Validate inputs
        if not email or not password:
            return jsonify({'error': 'All fields are required'}), 400
        
        if not InputValidator.validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        is_valid_password, password_error = InputValidator.validate_password(password)
        if not is_valid_password:
            return jsonify({'error': password_error}), 400
        
        if user_db.get_user(email):
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create user
        password_hash = generate_password_hash(password)
        if user_db.add_user(email, password_hash):
            return jsonify({
                'message': 'Registration successful! You can now log in.',
                'email': email,
                'csrf_token': generate_csrf()
            })
        else:
            return jsonify({'error': 'Failed to register user'}), 500
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Server error during registration'}), 500

@app.route('/api/backup/create', methods=['POST'])
@csrf.exempt
@admin_required
def api_backup_create():
    """API endpoint to create a backup"""
    try:
        backup_system = BackupSystem()
        backup_file = backup_system.create_backup()
        
        if not backup_file or not os.path.exists(backup_file):
            return jsonify({'error': 'Failed to create backup file'}), 500
            
        return jsonify({
            'message': f'Backup created successfully: {os.path.basename(backup_file)}',
            'file': os.path.basename(backup_file),
            'csrf_token': generate_csrf()
        })
    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        return jsonify({'error': f'Failed to create backup: {str(e)}'}), 500

@app.route('/api/backup/restore', methods=['POST'])
@csrf.exempt
@admin_required
def api_backup_restore():
    """API endpoint to restore from a backup"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        file = InputValidator.sanitize_input(data.get('file', ''))
        
        if not file or not file.startswith('backup_') or not file.endswith('.zip'):
            return jsonify({'error': 'Invalid backup file'}), 400
        
        backup_system = BackupSystem()
        backup_path = os.path.join('backups', file)
        
        if not os.path.exists(backup_path):
            return jsonify({'error': 'Backup file not found'}), 404
            
        if backup_system.restore_backup(backup_path):
            return jsonify({'message': 'Backup restored successfully', 'csrf_token': generate_csrf()})
        else:
            return jsonify({'error': 'Failed to restore backup'}), 500
    except Exception as e:
        logger.error(f"Backup restoration failed: {e}")
        return jsonify({'error': f'Failed to restore backup: {str(e)}'}), 500

@app.route('/api/backup/delete', methods=['POST'])
@csrf.exempt
@admin_required
def api_backup_delete():
    """API endpoint to delete a backup"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        file = InputValidator.sanitize_input(data.get('file', ''))
        
        if not file or not file.startswith('backup_') or not file.endswith('.zip'):
            return jsonify({'error': 'Invalid backup file'}), 400
        
        backup_path = os.path.join('backups', file)
        
        if not os.path.exists(backup_path):
            return jsonify({'error': 'Backup file not found'}), 404
            
        os.remove(backup_path)
        return jsonify({'message': 'Backup deleted successfully', 'csrf_token': generate_csrf()})
    except Exception as e:
        logger.error(f"Backup deletion failed: {e}")
        return jsonify({'error': f'Failed to delete backup: {str(e)}'}), 500

def scheduled_backup():
    """Create a scheduled backup"""
    try:
        backup_system = BackupSystem()
        backup_file = backup_system.create_backup()
        logger.info(f"Scheduled backup created: {backup_file}")
        
        # Cleanup old backups - keep only the latest 10
        backup_dir = 'backups'
        if os.path.exists(backup_dir):
            backup_files = [f for f in os.listdir(backup_dir) if f.startswith('backup_') and f.endswith('.zip')]
            backup_files.sort(reverse=True)  # Newest first
            
            # Delete old backups beyond the first 10
            for old_file in backup_files[10:]:
                try:
                    os.remove(os.path.join(backup_dir, old_file))
                    logger.info(f"Deleted old backup: {old_file}")
                except Exception as e:
                    logger.error(f"Failed to delete old backup {old_file}: {e}")
                    
    except Exception as e:
        logger.error(f"Scheduled backup failed: {e}")
        # Notify admin or take remedial action here if needed

def run_scheduler():
    """Run the scheduler for automated tasks"""
    # Schedule daily backup at midnight
    schedule.every().day.at("00:00").do(scheduled_backup)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    # Check if SSL certificate exists, generate if not
    cert_file = 'config/ssl/cert.pem'
    key_file = 'config/ssl/key.pem'
    if not (os.path.exists(cert_file) and os.path.exists(key_file)):
        try:
            from OpenSSL import crypto
            # Create a key pair
            k = crypto.PKey()
            k.generate_key(crypto.TYPE_RSA, 4096)
            
            # Create a self-signed cert
            cert = crypto.X509()
            cert.get_subject().C = "US"
            cert.get_subject().ST = "State"
            cert.get_subject().L = "City"
            cert.get_subject().O = "Smart Traffic Management"
            cert.get_subject().OU = "Traffic System"
            cert.get_subject().CN = "localhost"
            cert.set_serial_number(1000)
            cert.gmtime_adj_notBefore(0)
            cert.gmtime_adj_notAfter(10*365*24*60*60)  # 10 years
            cert.set_issuer(cert.get_subject())
            cert.set_pubkey(k)
            cert.sign(k, 'sha256')
            
            # Write certificate and key files
            with open(cert_file, "wb") as f:
                f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
            
            with open(key_file, "wb") as f:
                f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
                
            logger.info(f"Generated self-signed SSL certificate: {cert_file}")
        except Exception as e:
            logger.error(f"Failed to generate SSL certificate: {e}")
            logger.warning("Continuing without HTTPS support")
    
    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    # Start the web server
    host = '0.0.0.0'
    port = 5000
    print(f"Starting web server on {host}:{port}")
    print(f"Default admin login: admin@example.com / Admin123")
    ssl_context = (cert_file, key_file) if os.path.exists(cert_file) and os.path.exists(key_file) else None
    app.run(host=host, port=port, ssl_context=ssl_context, debug=False)