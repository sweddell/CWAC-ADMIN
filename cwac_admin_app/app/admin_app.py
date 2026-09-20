#!/usr/bin/env python
"""
CWAC-A11y Administration Interface
Web-based admin panel for managing accessibility and compliance scans
"""

from flask import Flask, render_template, request, jsonify, send_file, send_from_directory, redirect, url_for, flash, session
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from pathlib import Path
import json
import csv
import subprocess
import os
import sqlite3
import time
import threading
import shutil
import re
import secrets
from datetime import datetime, timedelta
import uuid
from urllib.parse import unquote
from typing import Dict, List, Any
from dotenv import load_dotenv

try:
    import pyotp
    import qrcode
    import qrcode.image.svg
    import io
    TOTP_AVAILABLE = True
except ImportError:
    TOTP_AVAILABLE = False
# Analytics uses JavaScript charts (no external dependencies)

# Load environment variables from .env file
load_dotenv()

_FLASK_DEBUG = os.environ.get('FLASK_ENV', 'production') == 'development'

# Get the base directory (CWAC-A11y root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'cwac_admin')
DATABASE_PATH = os.path.join(BASE_DIR, 'cwac_admin_app', 'database', 'bi_integration', 'cwac_analytics.db')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR, static_url_path='/static')
_SECRET_KEY = os.environ.get('SECRET_KEY')
if not _SECRET_KEY:
    import secrets
    _SECRET_KEY = secrets.token_hex(32)
    print("WARNING: SECRET_KEY not set — generated an ephemeral key; sessions will not survive restarts")
app.config['SECRET_KEY'] = _SECRET_KEY
app.config['DEBUG'] = _FLASK_DEBUG
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_COOKIE_NAME'] = 'cwac_admin_session_v2'  # Unique — avoids conflicts with other Flask apps on the same host
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Allow HTTP for localhost
app.config['SESSION_REFRESH_EACH_REQUEST'] = True  # Keep session alive
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)
CORS(app, supports_credentials=True)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = None  # Disable redirect message for AJAX
login_manager.session_protection = None  # Disable session protection to prevent logouts

@login_manager.unauthorized_handler
def unauthorized():
    """Handle unauthorized access for AJAX and regular requests"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Unauthorized', 'message': 'Please log in'}), 401
    return redirect(url_for('login', next=request.url))

@app.before_request
def make_session_permanent():
    """Make all sessions permanent to prevent expiry"""
    session.permanent = True

# Global storage for scan progress
SCAN_PROGRESS: Dict[str, Dict[str, Any]] = {}
ACTIVE_SCANS: Dict[str, subprocess.Popen] = {}

# Server start time for accurate uptime tracking
SERVER_START_TIME = datetime.now()

# Paths - Update for restructured directory
PROJECT_ROOT = Path(__file__).parent.parent.parent  # Go up to CWAC-A11y root
BASE_DIR = PROJECT_ROOT  # For backward compatibility
BASE_URLS_DIR = PROJECT_ROOT / "cwac" / "base_urls" / "visit"
CONFIG_DIR = PROJECT_ROOT / "config"
RESULTS_DIR = PROJECT_ROOT / "cwac" / "results"  # CWAC scanner writes to cwac/results
USERS_FILE = PROJECT_ROOT / "admin" / "users.json"

# Ensure directories exist
(PROJECT_ROOT / "admin").mkdir(exist_ok=True)

# ======================== USER AUTHENTICATION ========================

class User(UserMixin):
    """User class for Flask-Login"""
    def __init__(self, id, username, password_hash, is_admin=False, email=None, organization=None, status='active', registered_date=None, bio=None):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.is_admin = is_admin
        self.email = email
        self.organization = organization
        self.status = status  # 'pending', 'active', 'deactivated'
        self.registered_date = registered_date or datetime.now().isoformat()
        self.bio = bio
        self.totp_enabled = totp_enabled

def load_users():
    """Load users from JSON file"""
    if not USERS_FILE.exists():
        # Create default admin user
        default_users = {
            'admin': {
                'id': '1',
                'username': 'admin',
                'password_hash': generate_password_hash('admin', method='pbkdf2:sha256'),
                'is_admin': True,
                'email': 'admin@cwac-admin.org',
                'organization': 'CWAC-ADMIN',
                'status': 'active',
                'registered_date': datetime.now().isoformat()
            }
        }
        USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(USERS_FILE, 'w') as f:
            json.dump(default_users, f, indent=2)
        print("⚠️  Default admin user created: username='admin', password='admin'")
        print("⚠️  PLEASE CHANGE THE PASSWORD IMMEDIATELY!")
        return default_users
    
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def get_user_by_username(username):
    """Get user by username"""
    users = load_users()
    if username in users:
        user_data = users[username]
        return User(
            id=user_data['id'],
            username=user_data['username'],
            password_hash=user_data['password_hash'],
            is_admin=user_data.get('is_admin', False),
            email=user_data.get('email'),
            organization=user_data.get('organization'),
            status=user_data.get('status', 'active'),
            registered_date=user_data.get('registered_date'),
            bio=user_data.get('bio'),
            totp_enabled=user_data.get('totp_enabled', False)
        )
    return None

def get_user_by_id(user_id):
    """Get user by ID"""
    users = load_users()
    for username, user_data in users.items():
        if user_data['id'] == user_id:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                password_hash=user_data['password_hash'],
                is_admin=user_data.get('is_admin', False),
                email=user_data.get('email'),
                organization=user_data.get('organization'),
                status=user_data.get('status', 'active'),
                registered_date=user_data.get('registered_date'),
                bio=user_data.get('bio'),
                totp_enabled=user_data.get('totp_enabled', False)
            )
    return None

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    return get_user_by_id(user_id)

# Initialize default users
print("Initializing user authentication system...")
load_users()

# ======================== HELPER FUNCTIONS ========================

def load_sites():
    """Load all sites from CSV files in base_urls/visit/"""
    sites = []
    
    # Ensure the directory exists
    BASE_URLS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Focus on test_sites.csv for the admin interface
    test_file = BASE_URLS_DIR / "test_sites.csv"
    
    # Create the file if it doesn't exist
    if not test_file.exists():
        with open(test_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['organisation', 'url', 'sector'])
    
    # Load sites from test_sites.csv
    try:
        with open(test_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['file'] = 'test_sites.csv'
                sites.append(row)
    except Exception as e:
        print(f"Error reading {test_file}: {e}")
    
    # Also load from other CSV files (read-only)
    for csv_file in BASE_URLS_DIR.glob("*.csv"):
        if csv_file.name != 'test_sites.csv':
            try:
                with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        row['file'] = csv_file.name
                        sites.append(row)
            except Exception as e:
                print(f"Error reading {csv_file}: {e}")
    
    return sites

def save_sites(sites, filename="test_sites.csv"):
    """Save sites to CSV file"""
    BASE_URLS_DIR.mkdir(parents=True, exist_ok=True)
    filepath = BASE_URLS_DIR / filename
    
    # Always write the file, even if empty (to preserve headers)
    fieldnames = ['organisation', 'url', 'sector']
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for site in sites:
            writer.writerow({
                'organisation': site.get('organisation', ''),
                'url': site.get('url', ''),
                'sector': site.get('sector', 'General')
            })
    return True


def get_scan_configs():
    """Get available scan configurations"""
    configs = []
    
    # Ensure the config directory exists
    if not CONFIG_DIR.exists():
        return configs
    
    # Configuration descriptions
    config_descriptions = {
        'config_wcag22_aa.json': 'WCAG 2.2 Level AA - Comprehensive accessibility audit with all WCAG 2.2 AA criteria',
        'config_test.json': 'Quick Test - Fast scan with basic accessibility checks (2 pages per site)',
        'config_default.json': 'Default Audit - Standard scan with moderate coverage (50 pages per site)'
    }
    
    for config_file in CONFIG_DIR.glob("*.json"):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                
                # Get description or generate one
                description = config_descriptions.get(
                    config_file.name,
                    f"Scans up to {config.get('max_links_per_domain', 1)} pages with {config.get('thread_count', 1)} threads"
                )
                
                configs.append({
                    'filename': config_file.name,
                    'name': config.get('audit_name', 'Unknown'),
                    'max_links': config.get('max_links_per_domain', 1),
                    'thread_count': config.get('thread_count', 1),
                    'description': description
                })
        except:
            pass
    return configs

def _is_scan_dir_active(scan_dir):
    """True if a results dir belongs to a scan currently in progress.

    CWAC creates the results directory at the start of a scan but the
    .scan_success marker is only written after the process exits, so a
    running scan's directory must not be reported as failed.
    """
    try:
        dir_mtime = datetime.fromtimestamp(scan_dir.stat().st_mtime)
    except OSError:
        return False
    for progress in SCAN_PROGRESS.values():
        if progress.get('status') in ('starting', 'running'):
            start = progress.get('start_time')
            if start:
                try:
                    if dir_mtime >= datetime.fromisoformat(start) - timedelta(seconds=5):
                        return True
                except ValueError:
                    pass
    return False

def get_recent_results(limit=None):
    """Get recent scan results"""
    import csv
    results = []
    if RESULTS_DIR.exists():
        scan_dirs = sorted([d for d in RESULTS_DIR.iterdir() if d.is_dir()], 
                          key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Apply limit if specified, otherwise show all
        scan_dirs_to_process = scan_dirs[:limit] if limit else scan_dirs
        
        for scan_dir in scan_dirs_to_process:
            mtime = datetime.fromtimestamp(scan_dir.stat().st_mtime)
            
            # Check if scan succeeded or failed (a running scan's directory
            # exists before its success marker is written)
            success_marker = scan_dir / '.scan_success'
            if success_marker.exists():
                status = 'completed'
            elif _is_scan_dir_active(scan_dir):
                status = 'running'
            else:
                status = 'failed'
            
            # Count files and get summary from CWAC CSV files
            json_files = list(scan_dir.glob('*.json'))
            csv_files = list(scan_dir.glob('*.csv'))
            
            summary = {"sites_scanned": 0, "pages_scanned": 0, "scan_type": "manual"}
            
            # Read pages_scanned.csv
            pages_file = scan_dir / "pages_scanned.csv"
            if pages_file.exists():
                try:
                    with open(pages_file, 'r', encoding='utf-8-sig') as f:
                        reader = csv.DictReader(f)
                        sites_count = 0
                        total_pages = 0
                        for row in reader:
                            sites_count += 1
                            # Sum up the number_of_pages column
                            try:
                                total_pages += int(row.get('number_of_pages', 0))
                            except (ValueError, TypeError):
                                pass
                        summary["sites_scanned"] = sites_count
                        summary["pages_scanned"] = total_pages
                except:
                    pass
            
            # Determine scan type by checking scheduler logs
            # If scan name starts with date-time pattern and matches a scheduled config, it's scheduled
            try:
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT schedule_type FROM scan_schedules 
                    WHERE is_active = 1 AND config_name IN (
                        SELECT config_name FROM scan_results WHERE scan_id = ?
                    )
                """, (scan_dir.name,))
                if cursor.fetchone():
                    summary["scan_type"] = "scheduled"
                conn.close()
            except:
                # Default to manual if we can't determine
                summary["scan_type"] = "manual"
            
            results.append({
                'id': scan_dir.name,
                'name': scan_dir.name,
                'timestamp': mtime.isoformat(),
                'status': status,
                'json_files': len(json_files),
                'csv_files': len(csv_files),
                'summary': summary
            })
    
    return results

def run_scan_background(scan_id, config_file):
    """Run accessibility scan in background thread"""
    global SCAN_PROGRESS, ACTIVE_SCANS
    
    SCAN_PROGRESS[scan_id] = {
        'status': 'starting',
        'progress': 0,
        'message': 'Initializing scan...',
        'config': config_file,
        'start_time': datetime.now().isoformat(),
        'end_time': None,
        'error_details': None,
        'output_log': []
    }
    
    # Log scan start activity
    log_activity('scan_start', f'Scan Started: {config_file}', f'Initiating scan with config: {config_file}', scan_id)
    
    try:
        # Run the scan - use system Python or venv if it exists
        venv_python = PROJECT_ROOT / '.venv' / 'bin' / 'python'
        if venv_python.exists():
            python_cmd = str(venv_python)
        else:
            # Use system Python
            python_cmd = 'python3'
        
        cwac_script = PROJECT_ROOT / 'cwac' / 'cwac.py'
        cwac_dir = PROJECT_ROOT / 'cwac'
        
        # Pass just the config filename - scanner looks in cwac/config/
        cmd = [python_cmd, str(cwac_script), config_file]
        
        print(f"Starting scan {scan_id} with command: {' '.join(cmd)}")
        print(f"Working directory: {cwac_dir}")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=cwac_dir,  # Run from cwac directory so relative paths work
            bufsize=0,  # Unbuffered
            env={**os.environ, 'PYTHONUNBUFFERED': '1'}  # Force Python unbuffered output
        )
        
        ACTIVE_SCANS[scan_id] = process
        SCAN_PROGRESS[scan_id]['status'] = 'running'
        SCAN_PROGRESS[scan_id]['progress'] = 10
        SCAN_PROGRESS[scan_id]['message'] = 'Scan in progress...'
        
        # Monitor output
        output_lines = []
        for line in process.stdout:
            output_lines.append(line)
            SCAN_PROGRESS[scan_id]['output_log'].append(line.rstrip())
            # Keep only last 100 lines to prevent memory issues
            if len(SCAN_PROGRESS[scan_id]['output_log']) > 100:
                SCAN_PROGRESS[scan_id]['output_log'] = SCAN_PROGRESS[scan_id]['output_log'][-100:]
            print(f"[Scan {scan_id[:8]}] {line.rstrip()}")  # Log to console
            
            if 'Number of' in line:
                SCAN_PROGRESS[scan_id]['message'] = line.strip()
                SCAN_PROGRESS[scan_id]['progress'] = 20
            elif '%' in line:  # Progress bar updates
                SCAN_PROGRESS[scan_id]['message'] = line.strip()
                # Try to extract percentage from progress bar
                try:
                    if 'p:' in line:
                        # Extract page count: "p:5/10" means 50%
                        parts = line.split('p:')[1].split()[0].split('/')
                        current = int(parts[0])
                        total = int(parts[1])
                        progress = int((current / total) * 80) + 20  # 20-100%
                        SCAN_PROGRESS[scan_id]['progress'] = min(progress, 95)
                except:
                    pass
            elif 'complete' in line.lower():
                SCAN_PROGRESS[scan_id]['progress'] = 100
                SCAN_PROGRESS[scan_id]['message'] = 'Scan completed successfully!'
        
        process.wait()
        
        print(f"Scan {scan_id} completed with return code: {process.returncode}")
        
        if process.returncode == 0:
            SCAN_PROGRESS[scan_id]['status'] = 'completed'
            SCAN_PROGRESS[scan_id]['progress'] = 100
            SCAN_PROGRESS[scan_id]['end_time'] = datetime.now().isoformat()
            SCAN_PROGRESS[scan_id]['message'] = 'Scan completed! Syncing to database...'
            
            # Find the actual result directory created by CWAC (timestamp-based name)
            actual_result_dir = None
            scan_start_time = datetime.fromisoformat(SCAN_PROGRESS[scan_id]['start_time'])
            
            # Look for directories created after this scan started
            for scan_dir in RESULTS_DIR.iterdir():
                if scan_dir.is_dir():
                    # Check if directory was created after scan started
                    dir_mtime = datetime.fromtimestamp(scan_dir.stat().st_mtime)
                    if dir_mtime >= scan_start_time:
                        # Verify this is a valid scan directory
                        if (scan_dir / 'audit_log.csv').exists() and (scan_dir / 'pages_scanned.csv').exists():
                            actual_result_dir = scan_dir
                            print(f"✓ Found scan result directory: {scan_dir.name}")
                            break
            
            if actual_result_dir:
                # Create success marker file
                try:
                    success_marker = actual_result_dir / '.scan_success'
                    success_marker.write_text(datetime.now().isoformat())
                    print(f"✓ Created success marker for {actual_result_dir.name}")
                except Exception as e:
                    print(f"⚠️  Could not create success marker: {e}")
                
                # Sync this specific scan to database
                try:
                    print(f"🔄 AUTO-SYNC: Syncing {actual_result_dir.name} to analytics database...")
                    SCAN_PROGRESS[scan_id]['message'] = '🔄 Syncing to database...'
                    
                    # Use sync_single_scan.py for this specific directory
                    sync_script = PROJECT_ROOT / 'cwac_admin_app' / 'database' / 'bi_integration' / 'sync_single_scan.py'
                    if sync_script.exists():
                        # Run single scan sync with the actual directory path
                        sync_result = subprocess.run(
                            [python_cmd, str(sync_script), str(actual_result_dir)],
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        
                        if sync_result.returncode == 0:
                            # Check if sync actually imported data
                            if '✅ Successfully synced' in sync_result.stdout:
                                print(f"✅ Scan results automatically synced to database!")
                                print(sync_result.stdout[-1000:])  # Show last 1000 chars of output
                                SCAN_PROGRESS[scan_id]['message'] = '✅ Scan completed and synced to database!'
                                # Update last sync timestamp and log activity
                                update_last_sync()
                                log_activity('scan_complete', f'Scan Completed: {config_file}', f'Scan completed successfully and synced to database', scan_id)
                            else:
                                print(f"⚠️ Sync completed but may not have imported data")
                                print(sync_result.stdout[-500:])
                                SCAN_PROGRESS[scan_id]['message'] = 'Scan completed and synced!'
                                update_last_sync()
                                log_activity('scan_complete', f'Scan Completed: {config_file}', 'Scan completed and synced', scan_id)
                        else:
                            print(f"⚠️ Sync script failed: {sync_result.stderr[:500]}")
                            print(f"Stdout: {sync_result.stdout[-500:]}")
                            SCAN_PROGRESS[scan_id]['message'] = 'Scan completed (sync failed)'
                    else:
                        # Fallback to comprehensive_sync.py
                        sync_script = PROJECT_ROOT / 'cwac_admin_app' / 'database' / 'bi_integration' / 'comprehensive_sync.py'
                        if sync_script.exists():
                            print("Using fallback comprehensive_sync.py...")
                            sync_result = subprocess.run(
                                [python_cmd, str(sync_script)],
                                capture_output=True,
                                text=True,
                                timeout=60
                            )
                            if sync_result.returncode == 0 and 'Successfully synced' in sync_result.stdout:
                                print(f"✅ Scan synced via comprehensive sync")
                                SCAN_PROGRESS[scan_id]['message'] = 'Scan completed and synced!'
                            else:
                                SCAN_PROGRESS[scan_id]['message'] = 'Scan completed (sync issue)'
                        else:
                            print(f"⚠️ No sync scripts found")
                            SCAN_PROGRESS[scan_id]['message'] = 'Scan completed (no sync)'
                        
                except subprocess.TimeoutExpired:
                    print(f"⚠️ Sync timeout - may still be running")
                    SCAN_PROGRESS[scan_id]['message'] = 'Scan completed (sync timeout)'
                except Exception as e:
                    print(f"⚠️ Error syncing scan results: {e}")
                    SCAN_PROGRESS[scan_id]['message'] = 'Scan completed (sync error)'
            else:
                print(f"⚠️ Could not find result directory for scan {scan_id}")
                SCAN_PROGRESS[scan_id]['message'] = 'Scan completed (directory not found)'
                
        else:
            SCAN_PROGRESS[scan_id]['status'] = 'error'
            SCAN_PROGRESS[scan_id]['end_time'] = datetime.now().isoformat()
            # Extract error details from output
            error_lines = output_lines[-10:] if output_lines else []
            error_details = '\n'.join(error_lines)
            SCAN_PROGRESS[scan_id]['error_details'] = error_details
            SCAN_PROGRESS[scan_id]['message'] = 'Scan failed with errors. Click to view details.'
            print(f"Scan error. Last 10 lines of output:")
            for line in error_lines:
                print(f"  {line.rstrip()}")
            # Log error activity
            log_activity('scan_error', f'Scan Failed: {config_file}', f'Scan failed with return code {process.returncode}', scan_id)
            
    except Exception as e:
        print(f"Exception in scan {scan_id}: {str(e)}")
        import traceback
        error_trace = traceback.format_exc()
        traceback.print_exc()
        SCAN_PROGRESS[scan_id]['status'] = 'error'
        SCAN_PROGRESS[scan_id]['end_time'] = datetime.now().isoformat()
        SCAN_PROGRESS[scan_id]['error_details'] = f"{str(e)}\n\n{error_trace}"
        SCAN_PROGRESS[scan_id]['message'] = f'Error: {str(e)}. Click to view details.'
        # Log exception activity
        log_activity('scan_error', f'Scan Exception: {config_file}', f'Exception during scan: {str(e)}', scan_id)
    finally:
        if scan_id in ACTIVE_SCANS:
            del ACTIVE_SCANS[scan_id]

# ======================== ROUTES ========================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = get_user_by_username(username)
        
        if user and check_password_hash(user.password_hash, password):
            # Check user status
            if user.status == 'pending':
                flash('Your account is pending approval. Please wait for an administrator to approve your registration.', 'warning')
            elif user.status == 'deactivated':
                flash('Your account has been deactivated. Please contact an administrator.', 'danger')
            elif user.status == 'active':
                if user.totp_enabled:
                    session['pending_2fa_user'] = user.username
                    session['pending_2fa_next'] = request.args.get('next')
                    return redirect(url_for('login_2fa'))
                login_user(user, remember=True)  # Always remember
                session.permanent = True  # Keep session alive
                session.modified = True  # Mark session as modified
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            else:
                flash('Invalid account status. Please contact an administrator.', 'danger')
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

# ======================== TWO-FACTOR AUTHENTICATION ========================

RECOVERY_CODE_COUNT = 8

def _hash_recovery_code(code):
    """Hash a recovery code for storage (normalised to lowercase)."""
    return generate_password_hash(code.lower(), method='pbkdf2:sha256')

@app.route('/login/2fa', methods=['GET', 'POST'])
def login_2fa():
    """Second-factor challenge after a successful password check"""
    pending_username = session.get('pending_2fa_user')
    if not pending_username or current_user.is_authenticated:
        return redirect(url_for('login'))

    if request.method == 'POST':
        user = get_user_by_username(pending_username)
        if not user:
            session.pop('pending_2fa_user', None)
            return redirect(url_for('login'))

        code = request.form.get('code', '').strip().replace(' ', '')
        users = load_users()
        user_data = users.get(pending_username, {})
        secret = user_data.get('totp_secret')

        verified = False
        if TOTP_AVAILABLE and secret and pyotp.TOTP(secret).verify(code, valid_window=1):
            verified = True
        elif code:
            # Fall back to single-use recovery codes (stored hashed)
            hashes = user_data.get('recovery_code_hashes', [])
            for h in hashes:
                if check_password_hash(h, code.lower()):
                    verified = True
                    hashes.remove(h)
                    users[pending_username]['recovery_code_hashes'] = hashes
                    save_users(users)
                    flash('Recovery code used. It has been invalidated — consider regenerating your codes.', 'warning')
                    break

        if verified:
            session.pop('pending_2fa_user', None)
            next_page = session.pop('pending_2fa_next', None)
            login_user(user, remember=True)
            session.permanent = True
            session.modified = True
            return redirect(next_page) if next_page else redirect(url_for('index'))

        flash('Invalid authentication or recovery code', 'danger')

    return render_template('login_2fa.html')

@app.route('/2fa/setup')
@login_required
def setup_2fa():
    """Begin TOTP enrolment: show QR code and secret"""
    if not TOTP_AVAILABLE:
        flash('Two-factor authentication is not available on this installation (pyotp/qrcode not installed).', 'danger')
        return redirect(url_for('profile'))
    if current_user.totp_enabled:
        flash('Two-factor authentication is already enabled.', 'info')
        return redirect(url_for('profile'))

    secret = pyotp.random_base32()
    session['pending_totp_secret'] = secret
    totp_uri = pyotp.TOTP(secret).provisioning_uri(
        name=current_user.username, issuer_name='CWAC Admin'
    )
    qr_img = qrcode.make(totp_uri, image_factory=qrcode.image.svg.SvgPathImage)
    buf = io.BytesIO()
    qr_img.save(buf)
    qr_svg = buf.getvalue().decode('utf-8')
    return render_template('setup_2fa.html', totp_secret=secret, qr_svg=qr_svg)

@app.route('/2fa/verify', methods=['POST'])
@login_required
def verify_2fa_setup():
    """Confirm a TOTP code and enable 2FA for the current user"""
    secret = session.pop('pending_totp_secret', None)
    code = request.form.get('code', '').strip().replace(' ', '')

    if not secret:
        flash('Setup session expired — please start again.', 'danger')
        return redirect(url_for('profile'))
    if not (TOTP_AVAILABLE and pyotp.TOTP(secret).verify(code, valid_window=1)):
        flash('Invalid code — two-factor authentication was not enabled.', 'danger')
        return redirect(url_for('setup_2fa'))

    recovery_codes = [secrets.token_hex(4) for _ in range(RECOVERY_CODE_COUNT)]
    users = load_users()
    users[current_user.username]['totp_secret'] = secret
    users[current_user.username]['totp_enabled'] = True
    users[current_user.username]['recovery_code_hashes'] = [_hash_recovery_code(c) for c in recovery_codes]
    save_users(users)
    return render_template('recovery_codes.html', recovery_codes=recovery_codes)

@app.route('/2fa/disable', methods=['POST'])
@login_required
def disable_2fa():
    """Disable 2FA after confirming the account password"""
    password = request.form.get('password', '')
    if not check_password_hash(current_user.password_hash, password):
        flash('Incorrect password — two-factor authentication was not disabled.', 'danger')
        return redirect(url_for('profile'))

    users = load_users()
    users[current_user.username].pop('totp_secret', None)
    users[current_user.username].pop('recovery_code_hashes', None)
    users[current_user.username]['totp_enabled'] = False
    save_users(users)
    flash('Two-factor authentication has been disabled.', 'success')
    return redirect(url_for('profile'))

@app.route('/2fa/recovery/regenerate', methods=['POST'])
@login_required
def regenerate_recovery_codes():
    """Issue a fresh set of recovery codes (requires password)"""
    if not current_user.totp_enabled:
        flash('Two-factor authentication is not enabled.', 'danger')
        return redirect(url_for('profile'))
    password = request.form.get('password', '')
    if not check_password_hash(current_user.password_hash, password):
        flash('Incorrect password — recovery codes were not regenerated.', 'danger')
        return redirect(url_for('profile'))

    recovery_codes = [secrets.token_hex(4) for _ in range(RECOVERY_CODE_COUNT)]
    users = load_users()
    users[current_user.username]['recovery_code_hashes'] = [_hash_recovery_code(c) for c in recovery_codes]
    save_users(users)
    return render_template('recovery_codes.html', recovery_codes=recovery_codes)

@app.route('/privacy')
def privacy():
    """Privacy and cookie policy (public)"""
    return render_template('privacy.html')

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password page"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not check_password_hash(current_user.password_hash, current_password):
            flash('Current password is incorrect', 'danger')
        elif new_password != confirm_password:
            flash('New passwords do not match', 'danger')
        elif len(new_password) < 8:
            flash('Password must be at least 8 characters long', 'danger')
        else:
            users = load_users()
            users[current_user.username]['password_hash'] = generate_password_hash(new_password, method='pbkdf2:sha256')
            save_users(users)
            flash('Password changed successfully!', 'success')
            return redirect(url_for('index'))
    
    return render_template('change_password.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        organization = request.form.get('organization', '').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not username or not email or not organization or not password:
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        if len(username) < 3 or len(username) > 50:
            flash('Username must be between 3 and 50 characters', 'danger')
            return render_template('register.html')
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            flash('Username can only contain letters, numbers, underscores, and hyphens', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'danger')
            return render_template('register.html')
        
        # Check password strength
        if not re.search(r'[A-Z]', password):
            flash('Password must contain at least one uppercase letter', 'danger')
            return render_template('register.html')
        
        if not re.search(r'[a-z]', password):
            flash('Password must contain at least one lowercase letter', 'danger')
            return render_template('register.html')
        
        if not re.search(r'\d', password):
            flash('Password must contain at least one number', 'danger')
            return render_template('register.html')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            flash('Password must contain at least one special character', 'danger')
            return render_template('register.html')
        
        # Check if username already exists
        users = load_users()
        if username in users:
            flash('Username already exists', 'danger')
            return render_template('register.html')
        
        # Check if email already exists
        for user_data in users.values():
            if user_data.get('email', '').lower() == email.lower():
                flash('Email address already registered', 'danger')
                return render_template('register.html')
        
        # Create new user (pending approval)
        new_user_id = str(max([int(u['id']) for u in users.values()] + [0]) + 1)
        users[username] = {
            'id': new_user_id,
            'username': username,
            'password_hash': generate_password_hash(password, method='pbkdf2:sha256'),
            'email': email,
            'organization': organization,
            'is_admin': False,
            'status': 'pending',
            'registered_date': datetime.now().isoformat()
        }
        
        save_users(users)
        flash('Registration successful! Your account is pending admin approval.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/users')
@login_required
def user_management():
    """User management page (admin only)"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    users = load_users()
    
    # Separate users by status
    pending_users = []
    active_users = []
    
    for username, user_data in users.items():
        user = User(
            id=user_data['id'],
            username=user_data['username'],
            password_hash=user_data['password_hash'],
            is_admin=user_data.get('is_admin', False),
            email=user_data.get('email', ''),
            organization=user_data.get('organization', ''),
            status=user_data.get('status', 'active'),
            registered_date=user_data.get('registered_date', '')
        )
        
        if user.status == 'pending':
            pending_users.append(user)
        elif user.status == 'active':
            active_users.append(user)
    
    # Calculate statistics
    stats = {
        'total_users': len(users),
        'active_users': len(active_users),
        'pending_users': len(pending_users),
        'admin_users': sum(1 for u in users.values() if u.get('is_admin', False))
    }
    
    return render_template('user_management.html', 
                         pending_users=pending_users,
                         active_users=active_users,
                         stats=stats)

@app.route('/users/approve/<username>', methods=['POST'])
@login_required
def approve_user(username):
    """Approve a pending user"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    users = load_users()
    if username in users:
        users[username]['status'] = 'active'
        save_users(users)
        flash(f'User {username} has been approved.', 'success')
    else:
        flash('User not found.', 'danger')
    
    return redirect(url_for('user_management'))

@app.route('/users/reject/<username>', methods=['POST'])
@login_required
def reject_user(username):
    """Reject a pending user"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    users = load_users()
    if username in users:
        del users[username]
        save_users(users)
        flash(f'User {username} has been rejected and removed.', 'success')
    else:
        flash('User not found.', 'danger')
    
    return redirect(url_for('user_management'))

@app.route('/users/make-admin/<username>', methods=['POST'])
@login_required
def make_admin(username):
    """Make a user an admin"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    users = load_users()
    if username in users:
        users[username]['is_admin'] = True
        save_users(users)
        flash(f'User {username} is now an administrator.', 'success')
    else:
        flash('User not found.', 'danger')
    
    return redirect(url_for('user_management'))

@app.route('/users/remove-admin/<username>', methods=['POST'])
@login_required
def remove_admin(username):
    """Remove admin privileges from a user"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Don't allow removing admin from self
    if username == current_user.username:
        flash('You cannot remove admin privileges from yourself.', 'danger')
        return redirect(url_for('user_management'))
    
    users = load_users()
    if username in users:
        users[username]['is_admin'] = False
        save_users(users)
        flash(f'Admin privileges removed from user {username}.', 'success')
    else:
        flash('User not found.', 'danger')
    
    return redirect(url_for('user_management'))

@app.route('/users/deactivate/<username>', methods=['POST'])
@login_required
def deactivate_user(username):
    """Deactivate a user"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Don't allow deactivating self
    if username == current_user.username:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('user_management'))
    
    users = load_users()
    if username in users:
        users[username]['status'] = 'deactivated'
        save_users(users)
        flash(f'User {username} has been deactivated.', 'success')
    else:
        flash('User not found.', 'danger')
    
    return redirect(url_for('user_management'))

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('profile.html')

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile information"""
    email = request.form.get('email', '').strip()
    organization = request.form.get('organization', '').strip()
    bio = request.form.get('bio', '').strip()
    
    if not email or not organization:
        flash('Email and organization are required.', 'danger')
        return redirect(url_for('profile'))
    
    # Validate email format
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        flash('Invalid email address format.', 'danger')
        return redirect(url_for('profile'))
    
    users = load_users()
    
    # Check if email is already used by another user
    for username, user_data in users.items():
        if username != current_user.username and user_data.get('email', '').lower() == email.lower():
            flash('Email address is already in use by another account.', 'danger')
            return redirect(url_for('profile'))
    
    # Update user profile
    if current_user.username in users:
        users[current_user.username]['email'] = email
        users[current_user.username]['organization'] = organization
        users[current_user.username]['bio'] = bio
        save_users(users)
        flash('Profile updated successfully!', 'success')
    else:
        flash('User not found.', 'danger')
    
    return redirect(url_for('profile'))

@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    favicon_path = Path(__file__).parent.parent / 'static' / 'favicon.svg'
    if favicon_path.exists():
        return send_file(favicon_path, mimetype='image/svg+xml')
    # Fallback to empty 1x1 transparent PNG
    return '', 204

@app.route('/')
@login_required
def index():
    """Dashboard page"""
    # Use original dashboard with working functionality
    return render_template('dashboard.html')

@app.route('/sites')
@login_required
def sites():
    """Site management page"""
    return render_template('sites.html')

@app.route('/sites/<int:site_id>')
@login_required
def site_detail(site_id):
    """Individual site detail page"""
    # Get site details from database
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT url, organisation FROM sites WHERE id = ?', (site_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            site_url, site_name = result
            return render_template('site_detail.html', site_id=site_id, site_url=site_url, site_name=site_name)
        else:
            return "Site not found", 404
    except Exception as e:
        print(f"Error loading site: {e}")
        return "Error loading site", 500

@app.route('/sites/<int:site_id>/page/<int:page_id>')
@login_required
def page_detail(site_id, page_id):
    """Individual page detail page"""
    
    # Get page and site details
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get site details
        cursor.execute('SELECT url, organisation FROM sites WHERE id = ?', (site_id,))
        site_result = cursor.fetchone()
        
        if not site_result:
            conn.close()
            return "Site not found", 404
        
        site_url, site_name = site_result
        
        # Get page details from latest scan
        cursor.execute('''
            SELECT pr.page_url, pr.page_title
            FROM a11y_page_results pr
            JOIN scan_results sr ON pr.scan_result_id = sr.id
            WHERE pr.id = ? AND sr.site_id = ?
            LIMIT 1
        ''', (page_id, site_id))
        
        page_result = cursor.fetchone()
        conn.close()
        
        if not page_result:
            return "Page not found", 404
        
        page_url, page_title = page_result
        
        # Fallback page title if not available
        if not page_title:
            page_title = page_url.split('/')[-1] or 'Homepage'
        
        return render_template('page_detail.html', 
                             site_id=site_id, 
                             site_url=site_url, 
                             site_name=site_name, 
                             page_id=page_id,
                             page_url=page_url,
                             page_title=page_title)
    except Exception as e:
        print(f"Error loading page: {e}")
        import traceback
        traceback.print_exc()
        return "Error loading page", 500

@app.route('/scan')
@login_required
def scan():
    """Scan management page"""
    return render_template('scan.html')

# Results page removed - functionality moved to Scan page
# @app.route('/results')
# @login_required
# def results():
#     """Results page"""
#     return render_template('results.html')

@app.route('/dashboard')
@login_required
def analytics_dashboard():
    """Overall analytics dashboard with all sites"""
    dashboard_url = None
    bi_available = False
    
    # Check if database exists
    db_path = Path(DATABASE_PATH)
    if db_path.exists():
        bi_available = True
        
        # Generate embedded dashboard URL (no site filter - show all data)
        dashboard_id = os.environ.get('METABASE_DASHBOARD_ID')
        if dashboard_id and os.environ.get('METABASE_SECRET_KEY'):
            try:
                from bi_integration.generate_embed_url import generate_dashboard_url
                dashboard_url = generate_dashboard_url(
                    dashboard_id=int(dashboard_id),
                    params={},  # No filters - show all sites
                    expiration=3600  # 1 hour
                )
            except Exception as e:
                print(f"Could not generate dashboard URL: {e}")
                dashboard_url = None
    
# ======================== API ENDPOINTS ========================

@app.route('/api/sites', methods=['GET'])
@login_required
def api_get_sites():
    """Get all sites with their database IDs for analytics"""
    import sqlite3
    
    # First try to get sites from analytics database with their IDs
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, url, organisation, group_id, sector 
            FROM sites 
            WHERE url IS NOT NULL
            ORDER BY organisation
        """)
        
        db_sites = []
        for row in cursor.fetchall():
            db_sites.append({
                'id': row[0],  # This is the numeric ID we need!
                'url': row[1],
                'organisation': row[2],
                'group_id': row[3],
                'sector': row[4] or 'undefined',  # Include sector field
                'file': 'database',
                'editable': True  # Mark database sites as editable
            })
        
        conn.close()
        
        if db_sites:
            return jsonify(db_sites)
    except Exception as e:
        print(f"Error loading sites from database: {e}")
    
    # Fallback to CSV files (without IDs)
    sites = load_sites()
    return jsonify(sites)

@app.route('/api/sites', methods=['POST'])
@login_required
def api_add_site():
    """Add a new site to both database and CSV"""
    import sqlite3
    import csv
    data = request.json
    
    organisation = data.get('organisation', '').strip()
    url = data.get('url', '').strip()
    sector = data.get('sector', 'General').strip()
    
    if not organisation or not url:
        return jsonify({'success': False, 'error': 'Organisation and URL are required'}), 400
    
    try:
        # 1. Add to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check for duplicates
        cursor.execute('SELECT id FROM sites WHERE url = ?', (url,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Site with this URL already exists'}), 400
        
        # Insert the new site
        cursor.execute("""
            INSERT INTO sites (url, organisation, sector, created_at, updated_at) 
            VALUES (?, ?, ?, datetime('now'), datetime('now'))
        """, (url, organisation, sector))
        
        conn.commit()
        site_id = cursor.lastrowid
        conn.close()
        
        # 2. Also add to CSV file for scanner
        csv_file = BASE_URLS_DIR / "test_sites.csv"
        
        # Read existing sites
        existing_sites = []
        if csv_file.exists():
            with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                existing_sites = list(reader)
        
        # Check for duplicates in CSV
        for site in existing_sites:
            if site.get('url') == url:
                return jsonify({
                    'success': True, 
                    'site': {
                        'id': site_id,
                        'organisation': organisation,
                        'url': url,
                        'sector': sector
                    },
                    'note': 'Added to database only (already in CSV)'
                })
        
        # Add new site to CSV
        existing_sites.append({
            'organisation': organisation,
            'url': url,
            'sector': sector
        })
        
        # Write back to CSV
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['organisation', 'url', 'sector']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for site in existing_sites:
                writer.writerow(site)
        
        return jsonify({
            'success': True, 
            'site': {
                'id': site_id,
                'organisation': organisation,
                'url': url,
                'sector': sector
            }
        })
        
    except Exception as e:
        print(f"Error adding site: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sites/<int:site_id>', methods=['PUT'])
@login_required
def api_update_site(site_id):
    """Update a site in both database and CSV"""
    import sqlite3
    import csv
    data = request.json
    
    organisation = data.get('organisation', '').strip()
    url = data.get('url', '').strip()
    sector = data.get('sector', 'General').strip()
    
    if not organisation or not url:
        return jsonify({'success': False, 'error': 'Organisation and URL are required'}), 400
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get original URL before update
        cursor.execute('SELECT url FROM sites WHERE id = ?', (site_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({'success': False, 'error': 'Site not found'}), 404
        
        original_url = result[0]
        
        # Check for duplicate URL (excluding current site)
        cursor.execute('SELECT id FROM sites WHERE url = ? AND id != ?', (url, site_id))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Another site with this URL already exists'}), 400
        
        # Update the site in database
        cursor.execute("""
            UPDATE sites 
            SET organisation = ?, url = ?, sector = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (organisation, url, sector, site_id))
        
        conn.commit()
        conn.close()
        
        # Also update in CSV file
        csv_file = BASE_URLS_DIR / "test_sites.csv"
        if csv_file.exists():
            # Read existing sites
            updated_sites = []
            found_in_csv = False
            
            with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('url') == original_url:
                        # Update this row
                        row['organisation'] = organisation
                        row['url'] = url
                        row['sector'] = sector
                        found_in_csv = True
                    updated_sites.append(row)
            
            # If not found in CSV, add it
            if not found_in_csv:
                updated_sites.append({
                    'organisation': organisation,
                    'url': url,
                    'sector': sector
                })
            
            # Write back updated sites
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['organisation', 'url', 'sector']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for site in updated_sites:
                    writer.writerow(site)
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error updating site: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sites/<int:site_id>', methods=['DELETE'])
@login_required
def api_delete_site(site_id):
    """Delete a site from both database and CSV"""
    import sqlite3
    import csv
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get site details before deletion
        cursor.execute('SELECT url, organisation FROM sites WHERE id = ?', (site_id,))
        site_data = cursor.fetchone()
        if not site_data:
            conn.close()
            return jsonify({'success': False, 'error': 'Site not found'}), 404
        
        site_url = site_data[0]
        
        # Delete related scan results first (maintain referential integrity)
        cursor.execute('DELETE FROM scan_results WHERE site_id = ?', (site_id,))
        
        # Delete the site from database
        cursor.execute('DELETE FROM sites WHERE id = ?', (site_id,))
        
        conn.commit()
        conn.close()
        
        # Also delete from CSV file
        csv_file = BASE_URLS_DIR / "test_sites.csv"
        if csv_file.exists():
            # Read existing sites
            remaining_sites = []
            with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Keep all sites except the one being deleted
                    if row.get('url') != site_url:
                        remaining_sites.append(row)
            
            # Write back remaining sites
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['organisation', 'url', 'sector']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for site in remaining_sites:
                    writer.writerow(site)
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error deleting site: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/scan/configs', methods=['GET'])
@login_required
def api_get_configs():
    """Get available scan configurations"""
    configs = get_scan_configs()
    return jsonify(configs)

@app.route('/api/scan/configs/<filename>', methods=['GET'])
@login_required
def api_get_config_detail(filename):
    """Get detailed configuration data"""
    config_path = CONFIG_DIR / filename
    if not config_path.exists():
        return jsonify({'error': 'Configuration not found'}), 404
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return jsonify(config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scan/configs', methods=['POST'])
@login_required
def api_create_config():
    """Create a new scan configuration"""
    data = request.json
    filename = data.get('filename', '')
    
    # Validate filename
    if not filename or not filename.endswith('.json'):
        return jsonify({'error': 'Invalid filename. Must end with .json'}), 400
    
    if not filename.startswith('config_'):
        filename = f'config_{filename}'
    
    config_path = CONFIG_DIR / filename
    if config_path.exists():
        return jsonify({'error': 'Configuration already exists'}), 400
    
    # Create configuration with default values
    config = data.get('config', {})
    
    # Ensure required fields
    if 'audit_name' not in config:
        config['audit_name'] = filename.replace('config_', '').replace('.json', '').replace('_', ' ').title()
    
    # Set defaults if not provided
    defaults = {
        'headless': True,
        'max_links_per_domain': 20,
        'thread_count': 4,
        'browser': 'chrome',
        'chrome_binary_location': 'auto',
        'chrome_driver_location': 'auto',
        'user_agent': 'Mozilla/5.0 (compatible; CWAC-A11ybot/1.0)',
        'user_agent_product_token': 'CWACbot',  # REQUIRED: Bot identifier
        'follow_robots_txt': True,
        'script_timeout': 15,
        'page_load_timeout': 10,
        'delay_between_page_loads': 0.2,
        'delay_after_page_load': 0.1,
        'only_allow_https': True,
        'base_urls_visit_path': './base_urls/visit/',
        'viewport_sizes': {
            'small': {'width': 320, 'height': 450},
            'medium': {'width': 1280, 'height': 800}
        },
        'audit_plugins': {
            'axe_core_audit': {
                'class_name': 'AxeCoreAudit',
                'enabled': True
            }
        }
    }
    
    for key, value in defaults.items():
        if key not in config:
            config[key] = value
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scan/configs/<filename>', methods=['PUT'])
@login_required
def api_update_config(filename):
    """Update an existing scan configuration"""
    config_path = CONFIG_DIR / filename
    if not config_path.exists():
        return jsonify({'error': 'Configuration not found'}), 404
    
    data = request.json
    config = data.get('config', {})
    
    # CRITICAL: Ensure user_agent_product_token is present
    if 'user_agent_product_token' not in config:
        config['user_agent_product_token'] = 'CWACbot'
        print(f"⚠️  Warning: Added missing user_agent_product_token to {filename}")
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scan/configs/<filename>', methods=['DELETE'])
@login_required
def api_delete_config(filename):
    """Delete a scan configuration"""
    # Prevent deletion of default configs
    protected_configs = ['config_default.json', 'config_wcag22_aa.json', 'config_test.json']
    if filename in protected_configs:
        return jsonify({'error': 'Cannot delete protected configuration'}), 400
    
    config_path = CONFIG_DIR / filename
    if not config_path.exists():
        return jsonify({'error': 'Configuration not found'}), 404
    
    try:
        config_path.unlink()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scan/configs/<filename>/usage', methods=['GET'])
@login_required
def api_config_usage(filename):
    """Get usage history for a specific config file from actual scan results"""
    config_path = CONFIG_DIR / filename
    if not config_path.exists():
        return jsonify({'error': 'Configuration not found'}), 404
    
    # Load config details
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
    except Exception as e:
        return jsonify({'error': f'Failed to load config: {str(e)}'}), 500
    
    # Get the audit_name from config to match scan directories
    audit_name = config_data.get('audit_name', 'Unknown')
    
    # Scan the results directory for matching scans
    scan_history = []
    if RESULTS_DIR.exists():
        for scan_dir in RESULTS_DIR.iterdir():
            if not scan_dir.is_dir():
                continue
            
            # Check if this scan matches the config audit name
            # Scan dirs are named like: 2025-11-13_07-24-16_Minimal_Test_Audit_*
            if audit_name not in scan_dir.name:
                continue
            
            # Check if scan was successful
            success_marker = scan_dir / '.scan_success'
            if success_marker.exists():
                status = 'completed'
            elif _is_scan_dir_active(scan_dir):
                status = 'running'
            else:
                status = 'error'
            
            # Get scan timestamp from directory name or modification time
            try:
                # Extract timestamp from directory name (YYYY-MM-DD_HH-MM-SS)
                name_parts = scan_dir.name.split('_')
                if len(name_parts) >= 2:
                    date_part = name_parts[0]  # 2025-11-13
                    time_part = name_parts[1]  # 07-24-16
                    start_time = f"{date_part}T{time_part.replace('-', ':')}:00"
                else:
                    # Fallback to directory modification time
                    mtime = datetime.fromtimestamp(scan_dir.stat().st_mtime)
                    start_time = mtime.isoformat()
            except:
                mtime = datetime.fromtimestamp(scan_dir.stat().st_mtime)
                start_time = mtime.isoformat()
            
            # Get end time from success marker or last modified file
            end_time = None
            if success_marker.exists():
                try:
                    end_mtime = datetime.fromtimestamp(success_marker.stat().st_mtime)
                    end_time = end_mtime.isoformat()
                except:
                    pass
            
            # Calculate duration if both times available
            duration = None
            if start_time and end_time:
                try:
                    start_dt = datetime.fromisoformat(start_time)
                    end_dt = datetime.fromisoformat(end_time)
                    duration_seconds = (end_dt - start_dt).total_seconds()
                    # Format as human-readable
                    if duration_seconds < 60:
                        duration = f"{int(duration_seconds)}s"
                    elif duration_seconds < 3600:
                        duration = f"{int(duration_seconds / 60)}m {int(duration_seconds % 60)}s"
                    else:
                        hours = int(duration_seconds / 3600)
                        minutes = int((duration_seconds % 3600) / 60)
                        duration = f"{hours}h {minutes}m"
                except:
                    pass
            
            scan_history.append({
                'scan_id': scan_dir.name,
                'status': status,
                'start_time': start_time,
                'end_time': end_time,
                'duration': duration,
                'message': 'Scan completed successfully' if status == 'completed' else ('Scan in progress' if status == 'running' else 'Scan failed'),
                'error_details': None
            })
    
    # Also check currently running scans from SCAN_PROGRESS
    for scan_id, progress in SCAN_PROGRESS.items():
        if progress.get('config') == filename:
            scan_history.append({
                'scan_id': scan_id,
                'status': progress.get('status', 'unknown'),
                'start_time': progress.get('start_time', ''),
                'end_time': progress.get('end_time', ''),
                'duration': None,
                'progress': progress.get('progress', 0),
                'message': progress.get('message', ''),
                'error_details': progress.get('error_details')
            })
    
    # Sort by start time, most recent first
    scan_history.sort(key=lambda x: x.get('start_time', ''), reverse=True)
    
    # Calculate stats
    total_scans = len(scan_history)
    successful = sum(1 for s in scan_history if s['status'] == 'completed')
    failed = sum(1 for s in scan_history if s['status'] == 'error')
    running = sum(1 for s in scan_history if s['status'] in ['starting', 'running'])
    
    return jsonify({
        'config': config_data,
        'filename': filename,
        'stats': {
            'total_scans': total_scans,
            'successful': successful,
            'failed': failed,
            'running': running,
            'success_rate': round((successful / total_scans * 100) if total_scans > 0 else 0, 1)
        },
        'recent_scans': scan_history[:20]  # Last 20 scans
    })

@app.route('/api/scan/start', methods=['POST'])
@login_required
def api_start_scan():
    """Start a new scan"""
    data = request.json
    config_file = data.get('config', 'config_test.json')
    
    scan_id = str(uuid.uuid4())
    
    # Start scan in background thread
    thread = threading.Thread(target=run_scan_background, args=(scan_id, config_file))
    thread.start()
    
    return jsonify({'success': True, 'scan_id': scan_id})

@app.route('/api/scan/progress/<scan_id>', methods=['GET'])
@login_required
def api_scan_progress(scan_id):
    """Get scan progress"""
    if scan_id in SCAN_PROGRESS:
        return jsonify(SCAN_PROGRESS[scan_id])
    return jsonify({'error': 'Scan not found'}), 404

@app.route('/api/scan/history', methods=['GET'])
@login_required
def api_scan_history():
    """Get all scan history from SCAN_PROGRESS"""
    history = []
    for scan_id, progress in SCAN_PROGRESS.items():
        history.append({
            'id': scan_id,
            'config': progress.get('config', 'unknown'),
            'status': progress.get('status', 'unknown'),
            'start_time': progress.get('start_time', ''),
            'end_time': progress.get('end_time', ''),
            'progress': progress.get('progress', 0),
            'message': progress.get('message', '')
        })
    
    # Sort by start time, most recent first
    history.sort(key=lambda x: x['start_time'], reverse=True)
    return jsonify(history)

@app.route('/api/scan/active', methods=['GET'])
@login_required
def api_scan_active():
    """Get all active scans"""
    active = []
    for scan_id, progress in SCAN_PROGRESS.items():
        if progress.get('status') in ['starting', 'running']:
            active.append({
                'id': scan_id,
                'config': progress.get('config', 'unknown'),
                'status': progress.get('status', 'unknown'),
                'start_time': progress.get('start_time', ''),
                'progress': progress.get('progress', 0),
                'message': progress.get('message', '')
            })
    return jsonify(active)

@app.route('/api/scan/stop/<scan_id>', methods=['POST'])
@login_required
def api_stop_scan(scan_id):
    """Stop a running scan"""
    if scan_id in ACTIVE_SCANS:
        try:
            ACTIVE_SCANS[scan_id].terminate()
            SCAN_PROGRESS[scan_id]['status'] = 'cancelled'
            SCAN_PROGRESS[scan_id]['message'] = 'Scan cancelled by user'
            return jsonify({'success': True})
        except:
            pass
    return jsonify({'success': False, 'error': 'Scan not found'}), 404

@app.route('/api/results', methods=['GET'])
@login_required
def api_get_results():
    """Get scan results with optional limit"""
    limit = request.args.get('limit', type=int)
    results = get_recent_results(limit=limit)
    return jsonify(results)

@app.route('/api/sites/results', methods=['GET'])
@login_required
def api_get_sites_results():
    """Get aggregated results for all sites - FROM DATABASE"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get latest scan for each site with proper aggregation
        cursor.execute("""
            SELECT 
                s.organisation,
                s.url,
                sr.a11y_score,
                sr.a11y_total_issues,
                sr.a11y_critical_issues,
                sr.a11y_serious_issues,
                sr.a11y_moderate_issues,
                sr.a11y_minor_issues,
                sr.scan_date,
                (SELECT COUNT(*) FROM scan_results WHERE site_id = s.id) as total_scans
            FROM sites s
            LEFT JOIN scan_results sr ON sr.id = (
                SELECT id FROM scan_results 
                WHERE site_id = s.id 
                ORDER BY scan_date DESC 
                LIMIT 1
            )
            ORDER BY sr.a11y_score DESC NULLS LAST, sr.a11y_total_issues ASC
        """)
        
        sites_results = {}
        for row in cursor.fetchall():
            org, url, score, issues, crit, ser, mod, minor, date, scans = row
            sites_results[url] = {
                'organisation': org,
                'score': round(score) if score else 0,
                'total_issues': issues or 0,
                'critical_issues': crit or 0,
                'serious_issues': ser or 0,
                'moderate_issues': mod or 0,
                'minor_issues': minor or 0,
                'last_scan': date,
                'total_scans': scans or 0
            }
        
        conn.close()
        return jsonify(sites_results)
        
    except Exception as e:
        print(f"Error in api_get_sites_results: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to empty results
        return jsonify({})

@app.route('/api/sites/<int:site_id>/results', methods=['GET'])
@login_required
def api_get_site_results(site_id):
    """Get detailed results for a specific site - FROM DATABASE"""
    # Get site URL from ID
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT url FROM sites WHERE id = ?', (site_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({'error': 'Site not found'}), 404
        site_url = result[0]
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get site ID
        cursor.execute("SELECT id FROM sites WHERE url = ?", (site_url,))
        site_row = cursor.fetchone()
        if not site_row:
            conn.close()
            return jsonify({'error': 'Site not found'}), 404
        
        site_id = site_row[0]
        
        # Get recent scans (last 10)
        cursor.execute("""
            SELECT 
                scan_id,
                scan_date,
                a11y_total_issues,
                a11y_critical_issues,
                a11y_serious_issues,
                a11y_moderate_issues,
                a11y_minor_issues,
                pages_scanned,
                a11y_score
            FROM scan_results
            WHERE site_id = ?
            ORDER BY scan_date DESC
            LIMIT 10
        """, (site_id,))
        
        recent_scans = []
        total_issues_list = []
        
        for row in cursor.fetchall():
            scan_id, date, total, crit, ser, mod, minor, pages, score = row
            recent_scans.append({
                'id': scan_id,
                'date': date,
                'total_issues': total or 0,
                'critical': crit or 0,
                'serious': ser or 0,
                'moderate': mod or 0,
                'minor': minor or 0,
                'pages_scanned': pages or 0,
                'score': score or 0
            })
            total_issues_list.append(total or 0)
        
        # Calculate average issues
        avg_issues = round(sum(total_issues_list) / len(total_issues_list), 1) if total_issues_list else 0
        
        # Get top issues for this site from latest scan
        cursor.execute("""
            SELECT 
                ai.issue_id,
                ai.description,
                ai.impact,
                ai.count
            FROM a11y_issues ai
            JOIN scan_results sr ON ai.scan_result_id = sr.id
            WHERE sr.site_id = ?
            ORDER BY sr.scan_date DESC, ai.count DESC
            LIMIT 5
        """, (site_id,))
        
        top_issues = []
        for row in cursor.fetchall():
            issue_id, desc, impact, count = row
            top_issues.append({
                'id': issue_id,
                'description': desc,
                'impact': impact,
                'count': count
            })
        
        # Calculate trend
        trend = 'stable'
        if len(total_issues_list) >= 3:
            recent_avg = sum(total_issues_list[:3]) / 3
            older_avg = sum(total_issues_list[3:6]) / min(3, len(total_issues_list) - 3) if len(total_issues_list) > 3 else total_issues_list[-1]
            if recent_avg < older_avg * 0.9:
                trend = 'improving'
            elif recent_avg > older_avg * 1.1:
                trend = 'declining'
        
        # Get score from latest scan
        latest = recent_scans[0] if recent_scans else None
        score = latest['score'] if latest else 0
        
        # Calculate score if not in database
        if latest and score == 0:
            penalty = (latest['critical'] * 10) + (latest['serious'] * 5) + (latest['moderate'] * 2) + latest['minor']
            score = max(0, 100 - min(100, penalty))
        
        result = {
            'url': site_url,
            'total_scans': len(total_issues_list),
            'avg_issues': avg_issues,
            'score': round(score) if score else 0,
            'trend': trend,
            'recent_scans': recent_scans,
            'top_issues': top_issues,
            'compliance_level': determine_wcag_compliance_level(
                latest['critical'] if latest else 0,
                latest['serious'] if latest else 0,
                latest['moderate'] if latest else 0,
                latest['minor'] if latest else 0
            ) if latest else {'primary_level': 'Not scanned', 'compliant_levels': [], 'display_text': 'Not scanned'}
        }
        
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in api_get_site_results: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/sites/<int:site_id>/pages', methods=['GET'])
@login_required
def api_get_site_pages(site_id):
    """Get page-level results for a specific site"""
    # Get site URL from ID  
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT url FROM sites WHERE id = ?', (site_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({'error': 'Site not found'}), 404
        site_url = result[0]
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get site ID
        cursor.execute("SELECT id FROM sites WHERE url = ?", (site_url,))
        site_row = cursor.fetchone()
        if not site_row:
            conn.close()
            return jsonify({'error': 'Site not found'}), 404
        
        site_id = site_row[0]
        
        # Get latest scan ID for this site
        cursor.execute("""
            SELECT id, scan_date, a11y_score
            FROM scan_results
            WHERE site_id = ?
            ORDER BY scan_date DESC
            LIMIT 1
        """, (site_id,))
        
        latest_scan = cursor.fetchone()
        if not latest_scan:
            conn.close()
            return jsonify({'pages': []})
        
        scan_result_id, scan_date, site_score = latest_scan
        
        # Get all pages from the latest scan
        cursor.execute("""
            SELECT 
                id,
                page_url,
                page_title,
                issues_count,
                critical_count,
                serious_count,
                moderate_count,
                minor_count
            FROM a11y_page_results
            WHERE scan_result_id = ?
            ORDER BY page_url
        """, (scan_result_id,))
        
        pages = []
        for row in cursor.fetchall():
            page_id, page_url, page_title, issues, critical, serious, moderate, minor = row
            
            # Calculate page score
            penalty = (critical * 10) + (serious * 5) + (moderate * 2) + minor
            page_score = max(0, 100 - min(100, penalty))
            
            # Determine status
            status = 'complete'
            
            # Use actual page title from database, fallback to extracting from URL
            if page_title:
                page_name = page_title
            else:
                # Fallback: Extract page name from URL
                page_name = page_url.split('/')[-1] or 'Homepage'
                if page_name == '.' or page_name == '':
                    page_name = 'Homepage'
                else:
                    # Clean up page name
                    page_name = page_name.replace('.html', '').replace('.php', '').replace('-', ' ').title()
            
            pages.append({
                'id': page_id,
                'name': page_name,
                'url': page_url,
                'status': status,
                'score': round(page_score),
                'issues_count': issues or 0,
                'critical': critical or 0,
                'serious': serious or 0,
                'moderate': moderate or 0,
                'minor': minor or 0,
                'last_scan': scan_date
            })
        
        conn.close()
        return jsonify({'pages': pages, 'site_score': round(site_score) if site_score else 0})
        
    except Exception as e:
        print(f"Error in api_get_site_pages: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/sites/<int:site_id>/pages/trends', methods=['GET'])
@login_required
def api_get_page_trends(site_id):
    """Get historical score trends for a specific page"""
    # Get site URL from ID
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT url FROM sites WHERE id = ?', (site_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({'error': 'Site not found'}), 404
        site_url = result[0]
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    page_url = request.args.get('page_url', '')
    
    if not page_url:
        return jsonify({'error': 'page_url parameter required'}), 400
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get site ID
        cursor.execute("SELECT id FROM sites WHERE url = ?", (site_url,))
        site_row = cursor.fetchone()
        if not site_row:
            conn.close()
            return jsonify({'error': 'Site not found'}), 404
        
        site_id = site_row[0]
        
        # Get historical scan data for this page (last 10 scans)
        cursor.execute("""
            SELECT 
                sr.scan_date,
                pr.critical_count,
                pr.serious_count,
                pr.moderate_count,
                pr.minor_count,
                seo.seo_score,
                seo.json_ld_exists,
                seo.open_graph_complete,
                seo.twitter_card_complete,
                seo.title_tag_exists,
                seo.meta_description_exists,
                seo.alt_text_coverage
            FROM scan_results sr
            JOIN a11y_page_results pr ON sr.id = pr.scan_result_id
            LEFT JOIN seo_results seo ON sr.id = seo.scan_result_id AND pr.page_url = seo.page_url
            WHERE sr.site_id = ? AND pr.page_url = ?
            ORDER BY sr.scan_date ASC
            LIMIT 10
        """, (site_id, page_url))
        
        rows = cursor.fetchall()
        
        if not rows:
            conn.close()
            return jsonify({
                'dates': [],
                'accessibility_scores': [],
                'seo_scores': [],
                'aeo_scores': []
            })
        
        dates = []
        accessibility_scores = []
        seo_scores = []
        aeo_scores = []
        
        for row in rows:
            scan_date, critical, serious, moderate, minor, seo_score, json_ld, og, twitter, title, meta_desc, alt_coverage = row
            
            # Calculate accessibility score using standard formula (consistent with rest of app)
            # Weighted penalty: critical = 10 points, serious = 5, moderate = 2, minor = 1
            penalty = (critical or 0) * 10 + (serious or 0) * 5 + (moderate or 0) * 2 + (minor or 0) * 1
            accessibility_score = max(0, 100 - min(100, penalty))
            
            # Calculate AEO score (similar to site-wide calculation)
            structured_data_score = 100 if json_ld else 0
            meta_tags_score = ((1 if title else 0) + (1 if meta_desc else 0) + (1 if og else 0) + (1 if twitter else 0)) / 4 * 100
            content_quality_score = alt_coverage or 0
            aeo_score = (structured_data_score * 0.4 + meta_tags_score * 0.3 + content_quality_score * 0.3)
            
            dates.append(scan_date)
            accessibility_scores.append(round(accessibility_score, 1))
            seo_scores.append(round(seo_score or 0, 1))
            aeo_scores.append(round(aeo_score, 1))
        
        conn.close()
        return jsonify({
            'dates': dates,
            'accessibility_scores': accessibility_scores,
            'seo_scores': seo_scores,
            'aeo_scores': aeo_scores
        })
        
    except Exception as e:
        print(f"Error in api_get_page_trends: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/sites/<int:site_id>/pages/issues', methods=['GET'])
@login_required
def api_get_page_issues(site_id):
    """Get detailed issues for a specific page"""
    # Get site URL from ID
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT url FROM sites WHERE id = ?', (site_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({'error': 'Site not found'}), 404
        site_url = result[0]
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    page_url = request.args.get('page_url', '')
    
    if not page_url:
        return jsonify({'error': 'page_url parameter required'}), 400
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get site ID
        cursor.execute("SELECT id FROM sites WHERE url = ?", (site_url,))
        site_row = cursor.fetchone()
        if not site_row:
            conn.close()
            return jsonify({'error': 'Site not found'}), 404
        
        site_id = site_row[0]
        
        # Get latest scan ID
        cursor.execute("""
            SELECT id FROM scan_results
            WHERE site_id = ?
            ORDER BY scan_date DESC
            LIMIT 1
        """, (site_id,))
        
        latest_scan = cursor.fetchone()
        if not latest_scan:
            conn.close()
            return jsonify({'issues': []})
        
        scan_result_id = latest_scan[0]
        
        # Get page result ID
        cursor.execute("""
            SELECT id FROM a11y_page_results
            WHERE scan_result_id = ? AND page_url = ?
        """, (scan_result_id, page_url))
        
        page_result = cursor.fetchone()
        if not page_result:
            conn.close()
            return jsonify({'issues': []})
        
        page_result_id = page_result[0]
        
        # Get issues for this scan (issues are aggregated at scan level, not page level)
        cursor.execute("""
            SELECT 
                issue_id,
                impact,
                description,
                help_text,
                count as instances
            FROM a11y_issues
            WHERE scan_result_id = ?
            ORDER BY 
                CASE impact
                    WHEN 'critical' THEN 1
                    WHEN 'serious' THEN 2
                    WHEN 'moderate' THEN 3
                    WHEN 'minor' THEN 4
                    ELSE 5
                END,
                issue_id
        """, (scan_result_id,))
        
        issues = []
        for row in cursor.fetchall():
            issue_id, impact, description, help_text, instances = row
            issues.append({
                'id': issue_id,
                'impact': impact or 'moderate',
                'description': description or 'Unknown issue',
                'help': help_text or '',
                'instances': instances or 1
            })
        
        conn.close()
        return jsonify({'issues': issues})
        
    except Exception as e:
        print(f"Error in api_get_page_issues: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/sites/<int:site_id>/accessibility', methods=['GET'])
@login_required
def api_get_site_accessibility(site_id):
    """Get site-wide accessibility data aggregated across all pages"""
    # Get site URL from ID
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT url FROM sites WHERE id = ?', (site_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({'error': 'Site not found'}), 404
        site_url = result[0]
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get site ID
        cursor.execute("SELECT id FROM sites WHERE url = ?", (site_url,))
        site_row = cursor.fetchone()
        if not site_row:
            conn.close()
            return jsonify({'error': 'Site not found'}), 404
        
        site_id = site_row[0]
        
        # Get latest scan ID
        cursor.execute("""
            SELECT id, a11y_score
            FROM scan_results
            WHERE site_id = ?
            ORDER BY scan_date DESC
            LIMIT 1
        """, (site_id,))
        
        latest_scan = cursor.fetchone()
        if not latest_scan:
            conn.close()
            return jsonify({
                'score': 0,
                'issues': [],
                'passed_tests': [],
                'pages': []
            })
        
        scan_result_id, site_score = latest_scan
        
        # Get all page results for this scan
        cursor.execute("""
            SELECT 
                id,
                page_url,
                page_title,
                issues_count,
                critical_count,
                serious_count,
                moderate_count,
                minor_count
            FROM a11y_page_results
            WHERE scan_result_id = ?
        """, (scan_result_id,))
        
        pages_data = []
        page_ids = []
        total_critical = 0
        total_serious = 0
        total_moderate = 0
        total_minor = 0
        
        for row in cursor.fetchall():
            page_id, page_url, page_title, issues, critical, serious, moderate, minor = row
            page_ids.append(page_id)
            
            total_critical += critical or 0
            total_serious += serious or 0
            total_moderate += moderate or 0
            total_minor += minor or 0
            
            # Calculate page score
            penalty = (critical * 10) + (serious * 5) + (moderate * 2) + minor
            page_score = max(0, 100 - min(100, penalty))
            
            # Use actual page title from database, fallback to extracting from URL
            if page_title:
                page_name = page_title
            else:
                # Fallback: Extract page name from URL
                page_name = page_url.split('/')[-1] or 'Homepage'
                if page_name == '.' or page_name == '':
                    page_name = 'Homepage'
                else:
                    page_name = page_name.replace('.html', '').replace('.php', '').replace('-', ' ').title()
            
            pages_data.append({
                'name': page_name,
                'url': page_url,
                'score': round(page_score),
                'issues': issues or 0,
                'critical': critical or 0,
                'serious': serious or 0,
                'moderate': moderate or 0,
                'minor': minor or 0
            })
        
        # Get aggregated issues for this scan
        cursor.execute("""
            SELECT 
                issue_id,
                impact,
                description,
                help_text,
                pages_affected,
                count as total_instances
            FROM a11y_issues
            WHERE scan_result_id = ?
            ORDER BY 
                CASE impact
                    WHEN 'critical' THEN 1
                    WHEN 'serious' THEN 2
                    WHEN 'moderate' THEN 3
                    WHEN 'minor' THEN 4
                    ELSE 5
                END,
                count DESC
        """, (scan_result_id,))
        
        issues = []
        for row in cursor.fetchall():
            issue_id, impact, description, help_text, page_count, total_instances = row
            issues.append({
                'id': issue_id,
                'impact': impact or 'moderate',
                'description': description or 'Unknown issue',
                'help': help_text or '',
                'pages_affected': page_count,
                'total_instances': total_instances or 0
            })
        
        # Calculate passed tests (estimate)
        total_issues_count = len(issues)
        estimated_total_rules = 200
        passed_tests_count = max(0, estimated_total_rules - total_issues_count)
        
        # Get some common passed rules
        common_rules = [
            {'id': 'document-title', 'name': 'Page has a title', 'wcag': 'WCAG 2.4.2'},
            {'id': 'html-lang', 'name': 'Page has language attribute', 'wcag': 'WCAG 3.1.1'},
            {'id': 'valid-lang', 'name': 'Language attribute is valid', 'wcag': 'WCAG 3.1.2'},
            {'id': 'meta-viewport', 'name': 'Viewport meta tag present', 'wcag': 'Best Practice'},
            {'id': 'landmark-banner', 'name': 'Page has banner landmark', 'wcag': 'WCAG 1.3.1'},
        ]
        
        # Filter out failed rules
        failed_ids = [issue['id'] for issue in issues]
        passed_tests = [rule for rule in common_rules if rule['id'] not in failed_ids]
        
        result = {
            'score': round(site_score) if site_score else 0,
            'critical': total_critical,
            'serious': total_serious,
            'moderate': total_moderate,
            'minor': total_minor,
            'total_issues': total_critical + total_serious + total_moderate + total_minor,
            'issues': issues,
            'passed_tests': passed_tests,
            'passed_count': passed_tests_count,
            'pages': pages_data
        }
        
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in api_get_site_accessibility: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/sites/<int:site_id>/metadata', methods=['GET'])
@login_required
def api_get_site_metadata(site_id):
    """Get SEO/AEO metadata for a site"""
    # Get site URL from ID
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT url FROM sites WHERE id = ?', (site_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({'error': 'Site not found'}), 404
        site_url = result[0]
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get site ID
        cursor.execute("SELECT id FROM sites WHERE url = ?", (site_url,))
        site_row = cursor.fetchone()
        if not site_row:
            conn.close()
            return jsonify({'error': 'Site not found'}), 404
        
        site_id = site_row[0]
        
        # Get latest scan ID
        cursor.execute("""
            SELECT id FROM scan_results
            WHERE site_id = ?
            ORDER BY scan_date DESC
            LIMIT 1
        """, (site_id,))
        
        latest_scan = cursor.fetchone()
        if not latest_scan:
            conn.close()
            return jsonify({
                'aeo_score': 0,
                'breakdown': {},
                'schema_types': [],
                'meta_tags': {},
                'recommendations': []
            })
        
        scan_result_id = latest_scan[0]
        
        # Get SEO results for all pages
        cursor.execute("""
            SELECT 
                page_url,
                seo_score,
                title_tag_exists,
                title_tag_optimal,
                meta_description_exists,
                meta_description_optimal,
                canonical_exists,
                h1_optimal,
                alt_text_coverage,
                json_ld_exists,
                open_graph_complete,
                twitter_card_complete,
                robots_txt_exists,
                sitemap_exists,
                internal_links,
                external_links
            FROM seo_results
            WHERE scan_result_id = ?
        """, (scan_result_id,))
        
        seo_data = cursor.fetchall()
        
        if not seo_data:
            conn.close()
            return jsonify({
                'aeo_score': 0,
                'breakdown': {},
                'schema_types': [],
                'meta_tags': {},
                'recommendations': []
            })
        
        # Calculate aggregate metrics
        total_pages = len(seo_data)
        avg_seo_score = sum(row[1] or 0 for row in seo_data) / total_pages if total_pages > 0 else 0
        
        pages_with_title = sum(1 for row in seo_data if row[2])
        pages_with_meta_desc = sum(1 for row in seo_data if row[4])
        pages_with_canonical = sum(1 for row in seo_data if row[6])
        pages_with_h1 = sum(1 for row in seo_data if row[7])
        pages_with_json_ld = sum(1 for row in seo_data if row[9])
        pages_with_og = sum(1 for row in seo_data if row[10])
        pages_with_twitter = sum(1 for row in seo_data if row[11])
        
        avg_alt_coverage = sum(row[8] or 0 for row in seo_data) / total_pages if total_pages > 0 else 0
        
        # Calculate component scores
        structured_data_score = ((pages_with_json_ld / total_pages * 100) if total_pages > 0 else 0)
        meta_tags_score = ((pages_with_title + pages_with_meta_desc + pages_with_og + pages_with_twitter) / (total_pages * 4) * 100 if total_pages > 0 else 0)
        semantic_markup_score = ((pages_with_h1 + pages_with_canonical) / (total_pages * 2) * 100 if total_pages > 0 else 0)
        content_quality_score = avg_alt_coverage
        
        # Calculate overall AEO score (weighted average)
        aeo_score = (structured_data_score * 0.3 + meta_tags_score * 0.3 + semantic_markup_score * 0.2 + content_quality_score * 0.2)
        
        # Schema types detected
        schema_types = []
        if pages_with_json_ld > 0:
            schema_types.append({
                'type': 'Organization',
                'status': 'valid',
                'properties': 8,
                'pages_with': pages_with_json_ld,
                'icon': 'building'
            })
            schema_types.append({
                'type': 'WebPage',
                'status': 'valid',
                'properties': 12,
                'pages_with': pages_with_json_ld,
                'icon': 'file-earmark'
            })
        
        # Meta tags status
        meta_tags = {
            'title': {
                'present': pages_with_title,
                'total': total_pages,
                'optimal': sum(1 for row in seo_data if row[3]),
                'status': 'success' if pages_with_title == total_pages else 'warning'
            },
            'description': {
                'present': pages_with_meta_desc,
                'total': total_pages,
                'optimal': sum(1 for row in seo_data if row[5]),
                'status': 'success' if pages_with_meta_desc == total_pages else 'warning'
            },
            'canonical': {
                'present': pages_with_canonical,
                'total': total_pages,
                'status': 'success' if pages_with_canonical == total_pages else 'warning'
            },
            'open_graph': {
                'present': pages_with_og,
                'total': total_pages,
                'status': 'success' if pages_with_og == total_pages else 'warning'
            },
            'twitter_card': {
                'present': pages_with_twitter,
                'total': total_pages,
                'status': 'success' if pages_with_twitter == total_pages else 'warning'
            }
        }
        
        # Generate recommendations
        recommendations = []
        
        if pages_with_meta_desc < total_pages:
            recommendations.append({
                'priority': 'high',
                'title': 'Add Meta Descriptions',
                'description': f'{total_pages - pages_with_meta_desc} page(s) missing meta description tags',
                'impact': 'Meta descriptions improve click-through rates from search results',
                'pages_affected': total_pages - pages_with_meta_desc
            })
        
        if pages_with_json_ld == 0:
            recommendations.append({
                'priority': 'high',
                'title': 'Implement Structured Data',
                'description': 'No JSON-LD structured data found',
                'impact': 'Structured data helps search engines understand your content',
                'pages_affected': total_pages
            })
        
        if pages_with_og < total_pages:
            recommendations.append({
                'priority': 'medium',
                'title': 'Complete Open Graph Tags',
                'description': f'{total_pages - pages_with_og} page(s) missing Open Graph tags',
                'impact': 'Improves social media sharing appearance',
                'pages_affected': total_pages - pages_with_og
            })
        
        if avg_alt_coverage < 90:
            recommendations.append({
                'priority': 'medium',
                'title': 'Improve Image Alt Text Coverage',
                'description': f'Average alt text coverage is {round(avg_alt_coverage)}%',
                'impact': 'Alt text improves accessibility and SEO',
                'pages_affected': total_pages
            })
        
        if pages_with_twitter < total_pages:
            recommendations.append({
                'priority': 'low',
                'title': 'Add Twitter Card Tags',
                'description': f'{total_pages - pages_with_twitter} page(s) missing Twitter Card tags',
                'impact': 'Optimizes Twitter sharing',
                'pages_affected': total_pages - pages_with_twitter
            })
        
        result = {
            'aeo_score': round(aeo_score),
            'breakdown': {
                'structured_data': round(structured_data_score),
                'meta_tags': round(meta_tags_score),
                'semantic_markup': round(semantic_markup_score),
                'content_quality': round(content_quality_score)
            },
            'schema_types': schema_types,
            'meta_tags': meta_tags,
            'recommendations': recommendations,
            'pages_analyzed': total_pages
        }
        
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in api_get_site_metadata: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def determine_wcag_compliance_level(critical, serious, moderate, minor):
    """Determine WCAG compliance level based on issue severity
    
    Returns a dict with:
    - primary_level: The highest level achieved (e.g., "WCAG 2.2 AA")
    - compliant_levels: List of all levels met (cascading)
    """
    # WCAG 2.2 Level A: No critical issues (blocking issues)
    # WCAG 2.2 Level AA: No critical or serious issues
    # WCAG 2.2 Level AAA: Very few issues of any kind
    
    compliant_levels = []
    primary_level = 'Non-compliant'
    
    if critical == 0 and serious == 0 and moderate == 0 and minor == 0:
        primary_level = 'WCAG 2.2 AAA'
        # Perfect compliance - meets all levels
        compliant_levels = [
            'WCAG 2.2 AAA', 'WCAG 2.2 AA', 'WCAG 2.2 A',
            'WCAG 2.1 AAA', 'WCAG 2.1 AA', 'WCAG 2.1 A',
            'WCAG 2.0 AAA', 'WCAG 2.0 AA', 'WCAG 2.0 A'
        ]
    elif critical == 0 and serious == 0 and moderate <= 2:
        primary_level = 'WCAG 2.2 AA'
        # Meets AA and all A levels across all versions
        compliant_levels = [
            'WCAG 2.2 AA', 'WCAG 2.2 A',
            'WCAG 2.1 AA', 'WCAG 2.1 A',
            'WCAG 2.0 AA', 'WCAG 2.0 A'
        ]
    elif critical == 0 and serious <= 3:
        primary_level = 'WCAG 2.2 A'
        # Meets A level across all versions
        compliant_levels = [
            'WCAG 2.2 A',
            'WCAG 2.1 A',
            'WCAG 2.0 A'
        ]
    
    return {
        'primary_level': primary_level,
        'compliant_levels': compliant_levels,
        'display_text': primary_level
    }

@app.route('/api/leaderboard', methods=['GET'])
@login_required
def api_get_leaderboard():
    """Get leaderboard data for all sites"""
    leaderboard = []
    sites_data = json.loads(api_get_sites_results().data)
    
    for url, data in sites_data.items():
        if data['total_scans'] > 0:
            # Determine WCAG compliance level
            compliance_level = determine_wcag_compliance_level(
                data['critical_issues'],
                data['serious_issues'],
                data.get('moderate_issues', 0),
                data.get('minor_issues', 0)
            )
            
            leaderboard.append({
                'organisation': data['organisation'],
                'url': url,
                'score': data['score'],
                'total_issues': data['total_issues'],
                'critical_issues': data['critical_issues'],
                'serious_issues': data['serious_issues'],
                'moderate_issues': data.get('moderate_issues', 0),
                'minor_issues': data.get('minor_issues', 0),
                'last_scan': data['last_scan'],
                'status': 'compliant' if data['score'] >= 85 else 'needs_work' if data['score'] >= 70 else 'failing',
                'compliance_level': compliance_level['primary_level']  # Extract just the text value
            })
    
    # Sort by score (highest first), then by total issues (fewest first) for ties
    # This ensures that among sites with the same score, the one with fewer issues ranks higher
    leaderboard.sort(key=lambda x: (-x['score'], x['total_issues']))
    
    return jsonify(leaderboard)

@app.route('/api/top-issues', methods=['GET'])
@login_required
def api_get_top_issues():
    """Get top issues from recent scans"""
    top_issues = []
    issue_counts = {}
    
    # Get the most recent result directories
    if RESULTS_DIR.exists():
        scan_dirs = sorted([d for d in RESULTS_DIR.iterdir() if d.is_dir()], 
                          key=lambda x: x.stat().st_mtime, reverse=True)[:5]
        
        for scan_dir in scan_dirs:
            axe_csv_file = scan_dir / "axe_core_audit.csv"
            if axe_csv_file.exists():
                try:
                    with open(axe_csv_file, 'r', newline='', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            issue_key = row.get('id', 'unknown')
                            if issue_key and issue_key != '':
                                if issue_key not in issue_counts:
                                    issue_counts[issue_key] = {
                                        'id': issue_key,
                                        'description': row.get('description', 'Unknown issue'),
                                        'help': row.get('help', ''),
                                        'impact': row.get('impact', 'moderate'),
                                        'count': 0,
                                        'pages_affected': set()
                                    }
                                issue_counts[issue_key]['count'] += 1
                                issue_counts[issue_key]['pages_affected'].add(row.get('url', ''))
                except Exception as e:
                    print(f"Error reading {axe_csv_file}: {e}")
    
    # Sort by count and get top 10
    for issue_id, data in sorted(issue_counts.items(), key=lambda x: x[1]['count'], reverse=True)[:10]:
        top_issues.append({
            'id': data['id'],
            'description': data['description'],
            'help': data['help'],
            'impact': data['impact'],
            'count': data['count'],
            'pages_affected': len(data['pages_affected'])
        })
    
    return jsonify(top_issues)

@app.route('/api/results/<result_id>', methods=['GET'])
@login_required
def api_get_result_details(result_id):
    """Get detailed result for a specific scan"""
    result_dir = RESULTS_DIR / result_id
    
    if not result_dir.exists():
        return jsonify({'error': 'Result not found'}), 404
    
    details = {
        'id': result_id,
        'files': []
    }
    
    # Read CSV results and convert to a format similar to axe_results
    axe_csv_file = result_dir / "axe_core_audit.csv"
    pages_file = result_dir / "pages_scanned.csv"
    
    if axe_csv_file.exists():
        try:
            # Read violations and get unique pages from axe_core_audit.csv
            violations_by_page = {}
            pages_set = set()
            total_issues = 0
            
            with open(axe_csv_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    total_issues += 1
                    url = row.get('url', 'Unknown')
                    pages_set.add(url)  # Track unique pages
                    
                    if url not in violations_by_page:
                        violations_by_page[url] = []
                    
                    violations_by_page[url].append({
                        'description': row.get('description', 'Unknown issue'),
                        'impact': row.get('impact', 'moderate'),
                        'help': row.get('help', ''),
                        'helpUrl': row.get('helpUrl', ''),
                        'id': row.get('id', ''),
                        'nodes': [{
                            'target': [row.get('target', '')]
                        }]
                    })
            
            print(f"Parsed {total_issues} total issues from {result_id}")
            print(f"Found {len(pages_set)} unique pages")
            
            # Build axe_results structure
            results = []
            for page_url in sorted(pages_set):
                results.append({
                    'url': page_url,
                    'violations': violations_by_page.get(page_url, [])
                })
            
            details['axe_results'] = {
                'results': results
            }
        except Exception as e:
            print(f"Error reading CSV results: {e}")
            details['axe_results'] = {'results': []}
    
    # List all result files
    for file in result_dir.iterdir():
        if file.is_file():
            details['files'].append({
                'name': file.name,
                'size': file.stat().st_size
            })
    
    return jsonify(details)

@app.route('/api/results/<result_id>/download/<filename>')
def api_download_result(result_id, filename):
    """Download a single result file"""
    result_dir = RESULTS_DIR / result_id
    if result_dir.exists():
        file_path = result_dir / filename
        if file_path.exists() and file_path.is_file():
            return send_from_directory(result_dir, filename, as_attachment=True)
    return "File not found", 404

@app.route('/api/results/<result_id>/download-all')
@login_required
def api_download_all_results(result_id):
    """Download all result files as a zip archive"""
    import zipfile
    import io
    
    result_dir = RESULTS_DIR / result_id
    if not result_dir.exists():
        return "Result not found", 404
    
    # Create zip file in memory
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add all files from result directory
        for file_path in result_dir.iterdir():
            if file_path.is_file():
                zipf.write(file_path, arcname=file_path.name)
    
    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'{result_id}.zip'
    )

@app.route('/api/results/<result_id>', methods=['DELETE'])
@login_required
def api_delete_scan_result(result_id):
    """Delete a failed scan result directory (keeps database records for reporting)"""
    import shutil
    try:
        result_dir = RESULTS_DIR / result_id
        
        if not result_dir.exists():
            return jsonify({'success': False, 'error': 'Result directory not found'}), 404
        
        # Check if scan is marked as failed
        success_marker = result_dir / '.scan_success'
        if success_marker.exists():
            return jsonify({'success': False, 'error': 'Cannot delete successful scans'}), 400
        
        # Delete the results directory
        shutil.rmtree(result_dir)
        
        # Log the deletion
        log_activity('scan_delete', f'Deleted failed scan: {result_id}', 
                    f'Removed results directory for failed scan: {result_id}', result_id)
        
        return jsonify({'success': True, 'message': 'Scan results deleted successfully'})
    except Exception as e:
        print(f"Error deleting scan result: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scan-stats', methods=['GET'])
def api_get_scan_stats():
    """Get scan statistics for Quick Analytics - No auth required for read-only stats"""
    if not current_user.is_authenticated:
        return jsonify({
            'totalScans': 0,
            'compliantSites': 0,
            'activeIssues': 0,
            'avgScore': 0
        })
    
    # User is authenticated, get real stats
    import sqlite3
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Total scans in last 30 days
        cursor.execute("""
            SELECT COUNT(*) FROM scan_results 
            WHERE scan_date >= date('now', '-30 days')
        """)
        total_scans = cursor.fetchone()[0]
        
        # Compliant sites (score >= 90)
        cursor.execute("""
            SELECT COUNT(DISTINCT site_id) FROM scan_results 
            WHERE score >= 90 
            AND id IN (SELECT MAX(id) FROM scan_results GROUP BY site_id)
        """)
        compliant_sites = cursor.fetchone()[0]
        
        # Active issues
        cursor.execute("""
            SELECT SUM(total_issues) FROM scan_results 
            WHERE id IN (SELECT MAX(id) FROM scan_results GROUP BY site_id)
        """)
        active_issues = cursor.fetchone()[0] or 0
        
        # Average score
        cursor.execute("""
            SELECT AVG(a11y_score) FROM scan_results 
            WHERE id IN (SELECT MAX(id) FROM scan_results GROUP BY site_id)
        """)
        avg_score = cursor.fetchone()[0] or 0
        
        conn.close()
        return jsonify({
            'totalScans': total_scans,
            'compliantSites': compliant_sites,
            'activeIssues': active_issues,
            'avgScore': round(avg_score, 1)
        })
    except Exception as e:
        print(f"Error getting scan stats: {e}")
        return jsonify({
            'totalScans': 0,
            'compliantSites': 0,
            'activeIssues': 0,
            'avgScore': 0
        })

@app.route('/api/scans/recent', methods=['GET'])
@login_required
def api_get_recent_scans():
    """Get recent scan results"""
    try:
        # Get recent scans from results directory
        recent_scans = []
        results_path = RESULTS_DIR
        
        if results_path.exists():
            # Get all result directories
            result_dirs = sorted(
                [d for d in results_path.iterdir() if d.is_dir()],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )[:10]  # Get last 10 scans
            
            for result_dir in result_dirs:
                summary_file = result_dir / 'summary.json'
                if summary_file.exists():
                    with open(summary_file, 'r') as f:
                        summary = json.load(f)
                        recent_scans.append({
                            'id': result_dir.name,
                            'url': summary.get('url', 'Unknown'),
                            'organisation': summary.get('organisation', 'Unknown'),
                            'score': summary.get('score', 0),
                            'wcag_level': summary.get('wcag_level', 'None'),
                            'scan_date': summary.get('scan_date', ''),
                            'issues': summary.get('total_violations', 0),
                            'critical_issues': summary.get('critical_issues', 0),
                            'serious_issues': summary.get('serious_issues', 0)
                        })
        
        return jsonify(recent_scans)
    except Exception as e:
        print(f"Error getting recent scans: {e}")
        return jsonify([])

@app.route('/api/site-groups', methods=['GET'])
def api_get_site_groups():
    """Get all site groups - Check auth inline"""
    if not current_user.is_authenticated:
        return jsonify([])
    
    # User is authenticated, get groups
    import sqlite3
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM groups ORDER BY name')
        groups = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        conn.close()
        return jsonify(groups)
    except Exception as e:
        return jsonify([])

@app.route('/api/site-groups', methods=['POST'])
@login_required
def api_create_site_group():
    """Create a new site group"""
    import sqlite3
    data = request.get_json()
    group_name = data.get('name', '').strip()
    
    if not group_name:
        return jsonify({'success': False, 'error': 'Group name required'}), 400
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO groups (name) VALUES (?)', (group_name,))
        conn.commit()
        group_id = cursor.lastrowid
        conn.close()
        return jsonify({'success': True, 'id': group_id, 'name': group_name})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'Group name already exists'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analytics/refresh', methods=['POST'])
@login_required
def api_refresh_analytics():
    """Refresh analytics data by syncing from scan results"""
    import subprocess
    
    # Check if data_sync.py exists
    sync_script = PROJECT_ROOT / 'cwac_admin_app' / 'database' / 'bi_integration' / 'data_sync.py'
    if not sync_script.exists():
        return jsonify({
            'success': False,
            'message': 'BI integration not configured.'
        })
    
    try:
        result = subprocess.run(
            ['python', str(sync_script), '--sync'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Data sync completed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Data sync failed',
                'error': result.stderr
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

# ======================== ANALYTICS ROUTES ========================

@app.route('/analytics')
@login_required
def analytics():
    """Analytics dashboard page"""
    # Use analytics_direct.html which has the working functionality
    return render_template('analytics_direct.html')

@app.route('/api/analytics/status/database')
@login_required
def api_analytics_status_database():
    """Check analytics database status"""
    import sqlite3
    import os
    
    try:
        db_path = DATABASE_PATH
        
        # Check if database exists
        if not os.path.exists(db_path):
            return jsonify({'status': 'error', 'message': 'Not found'})
        
        # Check database connectivity and tables
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check for required tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        required_tables = ['sites', 'scan_results', 'groups', 'page_results']
        
        missing_tables = [t for t in required_tables if t not in tables]
        
        if missing_tables:
            conn.close()
            return jsonify({
                'status': 'warning',
                'message': f'Missing tables',
                'details': f'Missing: {", ".join(missing_tables)}'
            })
        
        # Check record counts
        cursor.execute("SELECT COUNT(*) FROM scan_results")
        scan_count = cursor.fetchone()[0]
        
        conn.close()
        
        if scan_count == 0:
            return jsonify({'status': 'warning', 'message': 'No data'})
        else:
            return jsonify({'status': 'success', 'message': f'{scan_count} scans'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)[:50]})


@app.route('/api/analytics/status/sync')
@login_required
def api_analytics_status_sync():
    """Check data sync status"""
    import os
    from datetime import datetime
    
    try:
        # Check local database modification time
        db_path = DATABASE_PATH
        if not os.path.exists(db_path):
            return jsonify({'status': 'error', 'message': 'No database'})
        
        # Get last modified time
        mtime = os.path.getmtime(db_path)
        last_sync = datetime.fromtimestamp(mtime)
        now = datetime.now()
        
        # Calculate time since last sync
        delta = now - last_sync
        
        if delta.total_seconds() < 3600:  # Less than 1 hour
            return jsonify({'status': 'success', 'message': f'Synced {int(delta.total_seconds()/60)}m ago'})
        elif delta.total_seconds() < 86400:  # Less than 1 day
            return jsonify({'status': 'warning', 'message': f'Synced {int(delta.total_seconds()/3600)}h ago'})
        else:
            return jsonify({'status': 'warning', 'message': f'Synced {int(delta.days)}d ago'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)[:50]})


@app.route('/api/analytics/status')
@login_required
def api_analytics_status_combined():
    """Get combined system status for analytics"""
    import sqlite3
    import os
    from datetime import datetime
    
    status = {
        'database': {'status': 'error', 'message': 'Not checked'},
        'scanner': {'status': 'error', 'message': 'Not checked'},
        'sync': {'status': 'error', 'message': 'Not checked'},
        'data': {'status': 'error', 'message': 'Not checked'}
    }
    
    try:
        # Check database
        db_path = DATABASE_PATH
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM scan_results")
            count = cursor.fetchone()[0]
            conn.close()
            
            if count > 0:
                status['database'] = {'status': 'success', 'message': f'{count} scans'}
            else:
                status['database'] = {'status': 'warning', 'message': 'No data'}
        else:
            status['database'] = {'status': 'error', 'message': 'Not found'}
        
        # Check scanner (check if cwac.py exists)
        cwac_path = os.path.join(str(PROJECT_ROOT), 'cwac', 'cwac.py')
        if os.path.exists(cwac_path):
            status['scanner'] = {'status': 'success', 'message': 'Ready'}
        else:
            status['scanner'] = {'status': 'warning', 'message': 'Not configured'}
        
        # Check sync status (last modified time)
        if os.path.exists(db_path):
            mtime = os.path.getmtime(db_path)
            last_sync = datetime.fromtimestamp(mtime)
            delta = datetime.now() - last_sync
            
            if delta.total_seconds() < 3600:
                status['sync'] = {'status': 'success', 'message': f'{int(delta.total_seconds()/60)}m ago'}
            elif delta.total_seconds() < 86400:
                status['sync'] = {'status': 'warning', 'message': f'{int(delta.total_seconds()/3600)}h ago'}
            else:
                status['sync'] = {'status': 'warning', 'message': f'{int(delta.days)}d ago'}
        
        # Check data availability
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(DISTINCT site_id) FROM scan_results")
            site_count = cursor.fetchone()[0]
            conn.close()
            
            if site_count > 0:
                status['data'] = {'status': 'success', 'message': f'{site_count} sites'}
            else:
                status['data'] = {'status': 'warning', 'message': 'No sites'}
                
    except Exception as e:
        print(f"Error checking status: {e}")
    
    return jsonify(status)

@app.route('/api/analytics/data')
@login_required
def api_analytics_data():
    """Get analytics data directly from SQLite database"""
    import sqlite3
    from datetime import datetime, timedelta
    
    # Get parameters
    site_id = request.args.get('site_id')
    group_id = request.args.get('group_id')
    date_range = int(request.args.get('date_range', 30))
    
    # Calculate date filter
    end_date = datetime.now()
    start_date = end_date - timedelta(days=date_range)
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Build WHERE clause
        where_conditions = [f"scan_date >= '{start_date.isoformat()}'"]
        if site_id:
            where_conditions.append(f"site_id = {site_id}")
        if group_id:
            where_conditions.append(f"site_id IN (SELECT id FROM sites WHERE group_id = {group_id})")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Get metrics
        metrics = {}
        
        # Total scans
        cursor.execute(f"SELECT COUNT(*) FROM scan_results WHERE {where_clause}")
        metrics['total_scans'] = cursor.fetchone()[0]
        
        # Compliant sites (score >= 90)
        cursor.execute(f"""
            SELECT COUNT(DISTINCT site_id) 
            FROM scan_results 
            WHERE score >= 90 AND {where_clause}
        """)
        metrics['compliant_sites'] = cursor.fetchone()[0]
        
        # Active issues
        cursor.execute(f"""
            SELECT COALESCE(SUM(total_issues), 0)
            FROM scan_results
            WHERE id IN (
                SELECT MAX(id) FROM scan_results 
                WHERE {where_clause}
                GROUP BY site_id
            )
        """)
        metrics['active_issues'] = cursor.fetchone()[0]
        
        # Average score
        cursor.execute(f"""
            SELECT ROUND(AVG(score), 1)
            FROM scan_results
            WHERE id IN (
                SELECT MAX(id) FROM scan_results 
                WHERE {where_clause}
                GROUP BY site_id
            )
        """)
        metrics['average_score'] = cursor.fetchone()[0] or 0
        
        # Compliance trend
        cursor.execute(f"""
            SELECT 
                DATE(scan_date) as date,
                ROUND(AVG(score), 1) as avg_score,
                COUNT(*) as scan_count
            FROM scan_results
            WHERE {where_clause}
            GROUP BY DATE(scan_date)
            ORDER BY date
            LIMIT 30
        """)
        trend_data = cursor.fetchall()
        compliance_trend = {
            'dates': [row[0] for row in trend_data],
            'scores': [row[1] for row in trend_data],
            'counts': [row[2] for row in trend_data]
        }
        
        # WCAG levels distribution
        cursor.execute(f"""
            SELECT 
                CASE 
                    WHEN score >= 95 THEN 'AAA'
                    WHEN score >= 90 THEN 'AA'
                    WHEN score >= 80 THEN 'A'
                    ELSE 'Non-Compliant'
                END as level,
                COUNT(*) as count
            FROM scan_results
            WHERE id IN (
                SELECT MAX(id) FROM scan_results 
                WHERE {where_clause}
                GROUP BY site_id
            )
            GROUP BY level
        """)
        wcag_data = cursor.fetchall()
        wcag_levels = {row[0]: row[1] for row in wcag_data}
        
        # Issues breakdown
        cursor.execute(f"""
            SELECT 
                COALESCE(SUM(critical_issues), 0) as critical,
                COALESCE(SUM(serious_issues), 0) as serious,
                COALESCE(SUM(moderate_issues), 0) as moderate,
                COALESCE(SUM(minor_issues), 0) as minor
            FROM scan_results
            WHERE id IN (
                SELECT MAX(id) FROM scan_results 
                WHERE {where_clause}
                GROUP BY site_id
            )
        """)
        issues_data = cursor.fetchone()
        issues_breakdown = {
            'critical': issues_data[0],
            'serious': issues_data[1],
            'moderate': issues_data[2],
            'minor': issues_data[3]
        }
        
        # Group performance
        cursor.execute("""
            SELECT 
                g.name,
                ROUND(AVG(sr.a11y_score), 1) as avg_score
            FROM groups g
            LEFT JOIN sites s ON g.id = s.group_id
            LEFT JOIN scan_results sr ON s.id = sr.site_id
            WHERE sr.id IN (
                SELECT MAX(id) FROM scan_results 
                GROUP BY site_id
            )
            GROUP BY g.id, g.name
            HAVING AVG(sr.a11y_score) IS NOT NULL
            ORDER BY avg_score DESC
        """)
        group_data = cursor.fetchall()
        group_performance = {
            'names': [row[0] for row in group_data],
            'scores': [row[1] for row in group_data]
        }
        
        # Sites overview
        cursor.execute(f"""
            SELECT 
                s.id,
                s.organisation,
                s.url,
                sr.a11y_score,
                CASE 
                    WHEN sr.a11y_score >= 95 THEN 'AAA'
                    WHEN sr.a11y_score >= 90 THEN 'AA'
                    WHEN sr.a11y_score >= 80 THEN 'A'
                    ELSE 'Non-Compliant'
                END as wcag_level,
                sr.a11y_total_issues,
                sr.scan_date as last_scan
            FROM sites s
            LEFT JOIN scan_results sr ON s.id = sr.site_id
                AND sr.id = (
                    SELECT MAX(id) FROM scan_results 
                    WHERE site_id = s.id AND {where_clause}
                )
            WHERE sr.id IS NOT NULL
            ORDER BY sr.a11y_score DESC
            LIMIT 20
        """)
        sites_data = cursor.fetchall()
        sites_overview = [
            {
                'id': row[0],
                'organisation': row[1],
                'url': row[2],
                'score': row[3],
                'wcag_level': row[4],
                'total_issues': row[5],
                'last_scan': row[6]
            }
            for row in sites_data
        ]
        
        conn.close()
        
        return jsonify({
            'metrics': metrics,
            'compliance_trend': compliance_trend,
            'wcag_levels': wcag_levels,
            'issues_breakdown': issues_breakdown,
            'group_performance': group_performance,
            'sites_overview': sites_overview
        })
        
    except Exception as e:
        print(f"Error getting analytics data: {e}")
        return jsonify({
            'error': str(e),
            'metrics': {
                'total_scans': 0,
                'compliant_sites': 0,
                'active_issues': 0,
                'average_score': 0
            },
            'compliance_trend': {'dates': [], 'scores': [], 'counts': []},
            'wcag_levels': {},
            'issues_breakdown': {},
            'group_performance': {'names': [], 'scores': []},
            'sites_overview': []
        })

@app.route('/api/analytics/dashboard')
@login_required
def api_analytics_dashboard():
    """Legacy endpoint - redirects to new analytics data endpoint"""
    # This endpoint is kept for backward compatibility
    # It now just redirects to the new JavaScript-based analytics
    return redirect(url_for('api_analytics_data'))

@app.route('/api/analytics/dashboard_old')
@login_required
def api_analytics_dashboard_old():
    """Old dashboard data endpoint (deprecated)"""
    import sqlite3
    from datetime import datetime, timedelta
    
    # Get parameters
    site_id = request.args.get('site_id')
    group_id = request.args.get('group_id')
    date_range = int(request.args.get('date_range', 30))
    wcag_level = request.args.get('wcag_level')
    
    try:
        # Get data from SQLite directly
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Build WHERE clause based on filters
        where_clauses = []
        params = []
        
        if site_id:
            # Handle both numeric ID and string ID
            try:
                site_id = int(site_id)
            except (ValueError, TypeError):
                pass
            where_clauses.append("sr.site_id = ?")
            params.append(site_id)
        
        if group_id:
            where_clauses.append("s.group_id = ?")
            params.append(group_id)
        
        if date_range:
            where_clauses.append("sr.scan_date >= date('now', '-' || ? || ' days')")
            params.append(date_range)
        
        if wcag_level:
            where_clauses.append("sr.wcag_level = ?")
            params.append(wcag_level)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Get stats
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_scans,
                COUNT(DISTINCT CASE WHEN sr.a11y_score >= 90 THEN sr.site_id END) as compliant_sites,
                SUM(sr.a11y_total_issues) as active_issues,
                AVG(sr.a11y_score) as avg_score
            FROM scan_results sr
            JOIN sites s ON sr.site_id = s.id
            WHERE {where_sql}
        """, params)
        
        stats_row = cursor.fetchone()
        
        # Get compliance trend (last 7 data points)
        cursor.execute(f"""
            SELECT 
                DATE(sr.scan_date) as date,
                AVG(sr.a11y_score) as avg_score,
                SUM(sr.a11y_total_issues) as total_issues
            FROM scan_results sr
            JOIN sites s ON sr.site_id = s.id
            WHERE {where_sql}
            GROUP BY DATE(sr.scan_date)
            ORDER BY date DESC
            LIMIT 7
        """, params)
        
        trend_data = cursor.fetchall()
        
        # Get WCAG distribution
        if where_clauses:
            # Apply filters to WCAG distribution
            cursor.execute(f"""
                SELECT 
                    sr.wcag_level,
                    COUNT(DISTINCT sr.site_id) as count
                FROM scan_results sr
                JOIN sites s ON sr.site_id = s.id
                WHERE {where_sql}
                GROUP BY sr.wcag_level
            """, params)
        else:
            # Get latest WCAG levels for all sites
            cursor.execute("""
                SELECT 
                    sr.wcag_level,
                    COUNT(DISTINCT sr.site_id) as count
                FROM scan_results sr
                JOIN sites s ON sr.site_id = s.id
                WHERE sr.id IN (SELECT MAX(id) FROM scan_results GROUP BY site_id)
                GROUP BY sr.wcag_level
            """)
        
        wcag_data = cursor.fetchall()
        
        # Get group performance
        cursor.execute("""
            SELECT 
                sg.name,
                AVG(sr.a11y_score) as avg_score
            FROM groups sg
            LEFT JOIN sites s ON s.group_id = sg.id
            LEFT JOIN scan_results sr ON s.id = sr.site_id
            GROUP BY sg.id, sg.name
        """)
        
        group_data = cursor.fetchall()
        
        # Get issues breakdown
        cursor.execute(f"""
            SELECT 
                'Critical' as severity,
                SUM(sr.a11y_critical_issues) as count
            FROM scan_results sr
            JOIN sites s ON sr.site_id = s.id
            WHERE {where_sql}
            UNION ALL
            SELECT 'Serious', SUM(sr.a11y_serious_issues)
            FROM scan_results sr
            JOIN sites s ON sr.site_id = s.id
            WHERE {where_sql}
            UNION ALL
            SELECT 'Moderate', SUM(sr.a11y_moderate_issues)
            FROM scan_results sr
            JOIN sites s ON sr.site_id = s.id
            WHERE {where_sql}
            UNION ALL
            SELECT 'Minor', SUM(sr.a11y_minor_issues)
            FROM scan_results sr
            JOIN sites s ON sr.site_id = s.id
            WHERE {where_sql}
        """, params * 4)
        
        issues_data = cursor.fetchall()
        
        # Get sites overview
        if where_clauses:
            # When filters are applied, use INNER JOIN and apply filters
            cursor.execute(f"""
                SELECT 
                    s.id,
                    s.url,
                    s.organisation,
                    COUNT(sr.id) as scan_count,
                    AVG(sr.a11y_score) as avg_score,
                    MAX(sr.wcag_level) as wcag_level,
                    MAX(sr.scan_date) as last_scan,
                    SUM(sr.a11y_critical_issues) as critical_issues
                FROM sites s
                INNER JOIN scan_results sr ON s.id = sr.site_id
                WHERE {where_sql}
                GROUP BY s.id
                ORDER BY avg_score DESC
                LIMIT 20
            """, params)
        else:
            # When no filters, get all sites
            cursor.execute("""
                SELECT 
                    s.id,
                    s.url,
                    s.organisation,
                    COUNT(sr.id) as scan_count,
                    AVG(sr.a11y_score) as avg_score,
                    MAX(sr.wcag_level) as wcag_level,
                    MAX(sr.scan_date) as last_scan,
                    SUM(sr.a11y_critical_issues) as critical_issues
                FROM sites s
                LEFT JOIN scan_results sr ON s.id = sr.site_id
                WHERE s.url IS NOT NULL
                GROUP BY s.id
                ORDER BY avg_score DESC
                LIMIT 20
            """)
        
        sites_data = cursor.fetchall()
        
        conn.close()
        
        # Format response
        response_data = {
            'stats': {
                'totalScans': stats_row[0] if stats_row else 0,
                'compliantSites': stats_row[1] if stats_row else 0,
                'activeIssues': stats_row[2] if stats_row else 0,
                'avgScore': stats_row[3] if stats_row else 0
            },
            'complianceTrend': {
                'labels': [row[0] for row in reversed(trend_data)],
                'scores': [row[1] for row in reversed(trend_data)],
                'issues': [row[2] for row in reversed(trend_data)]
            },
            'wcagDistribution': {
                'labels': [row[0] or 'None' for row in wcag_data],
                'values': [row[1] for row in wcag_data]
            },
            'groupPerformance': {
                'labels': [row[0] for row in group_data],
                'scores': [row[1] or 0 for row in group_data]
            },
            'issuesBreakdown': {
                'labels': [row[0] for row in issues_data],
                'values': [row[1] or 0 for row in issues_data]
            },
            'sites': [
                {
                    'id': row[0],
                    'url': row[1],
                    'organisation': row[2],
                    'scan_count': row[3],
                    'avg_score': row[4],
                    'wcag_level': row[5],
                    'last_scan': row[6],
                    'critical_issues': row[7] or 0
                }
                for row in sites_data
            ]
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error getting dashboard data: {e}")
        # Return empty data structure
        return jsonify({
            'stats': {
                'totalScans': 0,
                'compliantSites': 0,
                'activeIssues': 0,
                'avgScore': 0
            },
            'complianceTrend': {
                'labels': [],
                'scores': [],
                'issues': []
            },
            'wcagDistribution': {
                'labels': [],
                'values': []
            },
            'groupPerformance': {
                'labels': [],
                'scores': []
            },
            'issuesBreakdown': {
                'labels': [],
                'values': []
            },
            'sites': []
        })

# Analytics dashboard now uses JavaScript charts (Chart.js)

# ======================== SYSTEM STATUS ROUTES ========================

# Helper functions for system status monitoring

def ensure_system_tables():
    """Ensure system metadata and activity log tables exist"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # System metadata table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_metadata (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Activity log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT NOT NULL,
            event_name TEXT,
            details TEXT,
            scan_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def log_activity(event_type, event_name, details='', scan_id=None):
    """Log activity to database"""
    try:
        ensure_system_tables()
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO activity_log (event_type, event_name, details, scan_id, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (event_type, event_name, details, scan_id, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging activity: {e}")

def get_recent_activity(limit=10):
    """Get recent activity from database"""
    try:
        ensure_system_tables()
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, event_type, event_name, details
            FROM activity_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        activities = cursor.fetchall()
        conn.close()
        
        formatted_activities = []
        for timestamp, event_type, event_name, details in activities:
            try:
                dt = datetime.fromisoformat(timestamp)
                time_ago = get_time_ago(dt)
            except:
                time_ago = 'Unknown'
            
            formatted_activities.append({
                'event': event_name or event_type,
                'details': details,
                'time': time_ago
            })
        
        return formatted_activities
    except Exception as e:
        print(f"Error getting recent activity: {e}")
        return []

def get_time_ago(dt):
    """Convert datetime to time ago string"""
    now = datetime.now()
    delta = now - dt
    
    if delta.days > 0:
        return f"{delta.days}d ago"
    elif delta.seconds >= 3600:
        hours = delta.seconds // 3600
        return f"{hours}h ago"
    elif delta.seconds >= 60:
        minutes = delta.seconds // 60
        return f"{minutes}min ago"
    else:
        return "Just now"

def update_last_sync():
    """Update last sync timestamp"""
    try:
        ensure_system_tables()
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO system_metadata (key, value, updated_at)
            VALUES ('last_sync', ?, ?)
        """, (datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        conn.close()
        log_activity('sync', 'Database Sync', 'Synchronized scan results to analytics database')
    except Exception as e:
        print(f"Error updating last sync: {e}")

def get_last_sync():
    """Get last sync timestamp"""
    try:
        ensure_system_tables()
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM system_metadata WHERE key = 'last_sync'")
        result = cursor.fetchone()
        conn.close()
        
        if result:
            last_sync = datetime.fromisoformat(result[0])
            return get_time_ago(last_sync)
        return 'Never'
    except Exception as e:
        print(f"Error getting last sync: {e}")
        return 'Unknown'

def get_chrome_version():
    """Get actual Chrome version from binary"""
    import subprocess
    try:
        # Try Chrome for Testing path
        chrome_paths = [
            PROJECT_ROOT / 'chrome' / 'mac_arm-122.0.6261.39' / 'chrome-mac-arm64' / 'Google Chrome for Testing.app' / 'Contents' / 'MacOS' / 'Google Chrome for Testing',
            PROJECT_ROOT / 'chrome' / 'linux-122.0.6261.39' / 'chrome-linux64' / 'chrome',
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        ]
        
        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                result = subprocess.run([str(chrome_path), '--version'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    version = result.stdout.strip().split()[-1]
                    return version
        
        return 'Not found'
    except Exception as e:
        print(f"Error getting Chrome version: {e}")
        return 'Unknown'

@app.route('/system-status')
@login_required
def system_status():
    """System status page"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    return render_template('system_status.html')

@app.route('/api/system/status', methods=['GET'])
@login_required
def api_system_status():
    """Get system status information - 100% REAL DATA"""
    import sys
    
    # Try to import psutil, but make it optional
    try:
        import psutil
        HAS_PSUTIL = True
    except ImportError:
        HAS_PSUTIL = False
        print("Warning: psutil not installed, using fallback values for resource monitoring")
    
    try:
        # ==================== REAL UPTIME ====================
        now = datetime.now()
        uptime_delta = now - SERVER_START_TIME
        days = uptime_delta.days
        hours = uptime_delta.seconds // 3600
        minutes = (uptime_delta.seconds % 3600) // 60
        
        if days > 0:
            uptime = f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            uptime = f"{hours}h {minutes}m"
        else:
            uptime = f"{minutes}m"
        
        # ==================== DATABASE INFO ====================
        db_path = Path(DATABASE_PATH)
        db_size = f"{db_path.stat().st_size / 1024 / 1024:.2f} MB" if db_path.exists() else "N/A"
        
        # Count records
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM scan_results")
        db_records = cursor.fetchone()[0]
        
        # ==================== ANALYTICS TABLES WITH REAL TIMESTAMPS ====================
        analytics_tables = []
        # Use correct table names from the database
        for table in ['scan_results', 'a11y_issues', 'a11y_page_results', 'sites']:
            try:
                cursor.execute(f"SELECT COUNT(*), MAX(created_at) FROM {table}")
                count, last_updated = cursor.fetchone()
                
                last_updated_display = 'Never'
                if last_updated:
                    try:
                        last_updated_dt = datetime.fromisoformat(last_updated)
                        last_updated_display = get_time_ago(last_updated_dt)
                    except:
                        last_updated_display = 'Recently'
                
                # Display user-friendly table names
                display_name = table.replace('a11y_', '').replace('_', ' ').title()
                analytics_tables.append({
                    'name': display_name,
                    'records': count or 0,
                    'last_updated': last_updated_display
                })
            except Exception as e:
                print(f"Error getting table stats for {table}: {e}")
                display_name = table.replace('a11y_', '').replace('_', ' ').title()
                analytics_tables.append({
                    'name': display_name,
                    'records': 0,
                    'last_updated': 'Error'
                })
        
        conn.close()
        
        # ==================== SCANNER INFO ====================
        active_scans_count = len([s for s in SCAN_PROGRESS.values() if s.get('status') in ['running', 'starting']])
        
        # Get last sync time
        last_sync = "Recently"
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(scan_date) FROM scan_results")
            last_scan_date = cursor.fetchone()[0]
            if last_scan_date:
                try:
                    last_scan_dt = datetime.fromisoformat(last_scan_date)
                    last_sync = get_time_ago(last_scan_dt)
                except:
                    pass
            conn.close()
        except:
            pass
        
        # ==================== DEPENDENCIES ====================
        configs = get_scan_configs()
        config_count = len(configs)
        
        sites = load_sites()
        sites_count = len(sites)
        
        # Get Chrome version
        chrome_version = "Not detected"
        try:
            chrome_version = get_chrome_version()
        except:
            pass
        
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        # ==================== RESOURCE USAGE ====================
        if HAS_PSUTIL:
            # Real resource usage with psutil
            cpu_percent = psutil.cpu_percent(interval=0.5)
            cpu_usage = f"{cpu_percent:.1f}%"
            
            memory = psutil.virtual_memory()
            memory_used_gb = memory.used / 1024 / 1024 / 1024
            memory_total_gb = memory.total / 1024 / 1024 / 1024
            memory_percent = memory.percent
            memory_usage = f"{memory_used_gb:.1f}GB / {memory_total_gb:.1f}GB ({memory_percent:.1f}%)"
        else:
            # Fallback values when psutil not available
            cpu_usage = "N/A"
            memory_usage = "N/A"
        
        # Disk usage for results
        results_path = RESULTS_DIR
        if results_path.exists():
            try:
                total_size = sum(f.stat().st_size for f in results_path.rglob('*') if f.is_file())
                disk_usage = f"{total_size / 1024 / 1024:.2f} MB"
            except Exception as e:
                print(f"Error calculating disk usage: {e}")
                disk_usage = "N/A"
        else:
            disk_usage = "0 MB"
        
        # ==================== ACTIVITY LOG ====================
        recent_activity = []
        try:
            recent_activity = get_recent_activity(limit=10)
        except:
            pass
        
        # If no activity yet, add system started message
        if not recent_activity:
            recent_activity = [{
                'event': 'System Started',
                'details': f'Server started {get_time_ago(SERVER_START_TIME)}',
                'time': get_time_ago(SERVER_START_TIME)
            }]
        
        return jsonify({
            'uptime': uptime,
            'database': {
                'status': 'active',
                'size': db_size,
                'records': db_records
            },
            'scanner': {
                'status': 'ready',
                'active_scans': active_scans_count,
                'last_sync': last_sync
            },
            'dependencies': {
                'chrome_version': chrome_version,
                'python_version': python_version,
                'config_count': config_count,
                'sites_count': sites_count
            },
            'resources': {
                'cpu': cpu_usage,
                'memory': memory_usage,
                'disk': disk_usage
            },
            'recent_activity': recent_activity,
            'analytics_status': analytics_tables
        })
    except Exception as e:
        print(f"Error getting system status: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ======================== DASHBOARD API ENDPOINTS ========================

def get_successful_scan_ids():
    """Get list of scan_ids that have .scan_success marker (completed successfully)
    
    Returns both exact directory names and pattern for matching multi-site scans
    """
    successful_scans = []
    if RESULTS_DIR.exists():
        for scan_dir in RESULTS_DIR.iterdir():
            if scan_dir.is_dir():
                success_marker = scan_dir / '.scan_success'
                if success_marker.exists():
                    successful_scans.append(scan_dir.name)
    return successful_scans

def build_successful_scan_filter(cursor, successful_scan_ids):
    """Build SQL WHERE clause to filter by successful scans
    
    Handles both exact matches and multi-site scans (with _SiteName suffix)
    """
    if not successful_scan_ids:
        return "1=0", []  # No successful scans, return impossible condition
    
    # Build LIKE patterns for each base scan ID
    conditions = []
    params = []
    for scan_id in successful_scan_ids:
        # Match exact scan_id OR scan_id with site suffix
        conditions.append("(scan_id = ? OR scan_id LIKE ?)")
        params.append(scan_id)
        params.append(f"{scan_id}_%")
    
    where_clause = " OR ".join(conditions)
    return where_clause, params

@app.route('/api/dashboard/leaderboard', methods=['GET'])
@login_required
def api_dashboard_leaderboard():
    """Get leaderboard data with optional limit"""
    limit = request.args.get('limit', type=int)
    
    # Get full leaderboard
    leaderboard_response = api_get_leaderboard()
    leaderboard = json.loads(leaderboard_response.data)
    
    # Apply limit if specified
    if limit and limit > 0:
        leaderboard = leaderboard[:limit]
    
    return jsonify(leaderboard)

@app.route('/api/dashboard/accessibility-metrics', methods=['GET'])
@login_required
def api_dashboard_accessibility_metrics():
    """Get accessibility metrics for dashboard - ONLY from successful scans"""
    try:
        # Get list of successful scan IDs (those with .scan_success marker)
        successful_scan_ids = get_successful_scan_ids()
        
        if not successful_scan_ids:
            # No successful scans yet
            return jsonify({
                'avg_score': 0, 'score_trend': 0, 'critical_issues': 0,
                'serious_issues': 0, 'total_scans': 0, 'completed_scans': 0,
                'success_rate': '0%', 'failed_scans': 0,
                'score_trends': {'labels': [], 'sites': {}},
                'issues_by_severity': {'dates': [], 'critical': [], 'serious': [], 'moderate': [], 'minor': [], 'sites': [], 'sites_data': {}}
            })
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Build filter for successful scans (handles multi-site scan IDs)
        where_clause, params = build_successful_scan_filter(cursor, successful_scan_ids)
        
        # Get total successful scans
        cursor.execute(f"SELECT COUNT(*) FROM scan_results WHERE {where_clause}", params)
        total_scans = cursor.fetchone()[0]
        completed_scans = total_scans  # All counted scans are successful
        
        # Get average score from successful scans only
        cursor.execute(f"SELECT AVG(a11y_score) FROM scan_results WHERE a11y_score IS NOT NULL AND ({where_clause})", params)
        avg_score_result = cursor.fetchone()[0]
        avg_score = round(avg_score_result) if avg_score_result else 0
        
        # Get critical and serious issues from successful scans only
        cursor.execute(f"""
            SELECT COUNT(*) FROM a11y_issues ai
            JOIN scan_results sr ON ai.scan_result_id = sr.id
            WHERE ai.impact = 'critical'
            AND ({where_clause})
        """, params)
        critical_issues = cursor.fetchone()[0]
        
        cursor.execute(f"""
            SELECT COUNT(*) FROM a11y_issues ai
            JOIN scan_results sr ON ai.scan_result_id = sr.id
            WHERE ai.impact = 'serious'
            AND ({where_clause})
        """, params)
        serious_issues = cursor.fetchone()[0]
        
        # Calculate success rate - count all scan dirs vs successful
        all_scan_dirs = len([d for d in RESULTS_DIR.iterdir() if d.is_dir()]) if RESULTS_DIR.exists() else 0
        failed_scans = all_scan_dirs - completed_scans
        success_rate = f"{round((completed_scans / all_scan_dirs * 100)) if all_scan_dirs > 0 else 0}%"
        
        # Get score trends by site (last 10 SUCCESSFUL scans per site)
        cursor.execute(f"""
            SELECT s.organisation, sr.site_id, sr.a11y_score, sr.scan_date,
                   ROW_NUMBER() OVER (PARTITION BY sr.site_id ORDER BY sr.scan_date DESC) as row_num
            FROM scan_results sr
            JOIN sites s ON sr.site_id = s.id
            WHERE {where_clause}
            ORDER BY sr.site_id, sr.scan_date DESC
        """, params)
        all_scan_data = cursor.fetchall()
        
        # Group by site and get last 10 scans for each
        from collections import defaultdict
        sites_data = defaultdict(list)
        for org, site_id, score, scan_date, row_num in all_scan_data:
            if row_num <= 10:  # Only keep last 10 scans per site
                sites_data[org].append({'score': round(score) if score else 0, 'scan_date': scan_date})
        
        # Reverse each site's data to show oldest to newest
        for org in sites_data:
            sites_data[org] = list(reversed(sites_data[org]))
        
        # Find the maximum number of scans across all sites for consistent labels
        max_scans = max(len(data) for data in sites_data.values()) if sites_data else 10
        
        score_trends = {
            'labels': [f"Scan {i+1}" for i in range(max_scans)],
            'sites': {org: [item['score'] for item in data] for org, data in sites_data.items()}
        }
        
        # Get issues by severity for last 10 SUCCESSFUL scans, grouped by site for filtering
        # Get the site_ids that are in the score trends (active sites)
        active_site_ids = list(set(row[1] for row in all_scan_data if row[4] <= 10))
        site_placeholders = ','.join(['?' for _ in active_site_ids])
        
        if active_site_ids:
            # Get last 10 scans across all active sites
            # Build modified where_clause with sr. prefix for scan_id
            prefixed_where = where_clause.replace("scan_id", "sr.scan_id")
            
            cursor.execute(f"""
                SELECT sr.scan_id, s.organisation, sr.site_id,
                       SUM(CASE WHEN ai.impact = 'critical' THEN ai.count ELSE 0 END) as critical,
                       SUM(CASE WHEN ai.impact = 'serious' THEN ai.count ELSE 0 END) as serious,
                       SUM(CASE WHEN ai.impact = 'moderate' THEN ai.count ELSE 0 END) as moderate,
                       SUM(CASE WHEN ai.impact = 'minor' THEN ai.count ELSE 0 END) as minor,
                       sr.scan_date,
                       ROW_NUMBER() OVER (ORDER BY sr.scan_date DESC) as scan_num
                FROM scan_results sr
                JOIN sites s ON sr.site_id = s.id
                LEFT JOIN a11y_issues ai ON sr.id = ai.scan_result_id
                WHERE ({prefixed_where})
                AND sr.site_id IN ({site_placeholders})
                GROUP BY sr.scan_id, s.organisation, sr.site_id, sr.scan_date
                ORDER BY sr.scan_date DESC
                LIMIT 10
            """, params + active_site_ids)
            
            issues_data = cursor.fetchall()
            # Reverse to show oldest to newest
            issues_data = list(reversed(issues_data))
            
            # Group by site for filtering
            sites_issues_data = defaultdict(lambda: {
                'critical': [], 'serious': [], 'moderate': [], 'minor': []
            })
            
            # Get unique scan dates for labels
            scan_dates_labels = []
            for row in issues_data:
                scan_num = row[8]
                if f"Scan {scan_num}" not in scan_dates_labels:
                    scan_dates_labels.append(f"Scan {scan_num}")
                site_name = row[1]
                sites_issues_data[site_name]['critical'].append(row[3])
                sites_issues_data[site_name]['serious'].append(row[4])
                sites_issues_data[site_name]['moderate'].append(row[5])
                sites_issues_data[site_name]['minor'].append(row[6])
            
            # Also calculate totals for default display
            total_critical = [sum(row[3] for row in issues_data if row[8] == i+1) for i in range(10)]
            total_serious = [sum(row[4] for row in issues_data if row[8] == i+1) for i in range(10)]
            total_moderate = [sum(row[5] for row in issues_data if row[8] == i+1) for i in range(10)]
            total_minor = [sum(row[6] for row in issues_data if row[8] == i+1) for i in range(10)]
            
            issues_by_severity = {
                'dates': scan_dates_labels[:10],
                'critical': total_critical[:len(scan_dates_labels)],
                'serious': total_serious[:len(scan_dates_labels)],
                'moderate': total_moderate[:len(scan_dates_labels)],
                'minor': total_minor[:len(scan_dates_labels)],
                'sites': [row[1] for row in issues_data],  # Site names for reference
                'sites_data': dict(sites_issues_data)  # Site-specific data for filtering
            }
        else:
            issues_by_severity = {
                'dates': [], 'critical': [], 'serious': [], 'moderate': [], 'minor': [], 'sites': [], 'sites_data': {}
            }
        
        # Calculate score trend (compare last 7 days vs previous 7 days) from successful scans only
        cursor.execute(f"""
            SELECT AVG(a11y_score) FROM scan_results
            WHERE scan_date >= date('now', '-7 days')
            AND a11y_score > 0
            AND ({where_clause})
        """, params)
        recent_avg = cursor.fetchone()[0]
        
        cursor.execute(f"""
            SELECT AVG(a11y_score) FROM scan_results
            WHERE scan_date < date('now', '-7 days')
            AND scan_date >= date('now', '-14 days')
            AND a11y_score > 0
            AND ({where_clause})
        """, params)
        earlier_avg = cursor.fetchone()[0]
        
        if recent_avg and earlier_avg and earlier_avg > 0:
            score_trend = round(((recent_avg - earlier_avg) / earlier_avg) * 100)
        else:
            score_trend = 0
        
        conn.close()
        
        return jsonify({
            'avg_score': avg_score,
            'score_trend': score_trend,
            'critical_issues': critical_issues,
            'serious_issues': serious_issues,
            'total_scans': total_scans,
            'completed_scans': completed_scans,
            'success_rate': success_rate,
            'failed_scans': failed_scans,
            'score_trends': score_trends,
            'issues_by_severity': issues_by_severity
        })
    except Exception as e:
        print(f"Error getting accessibility metrics: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'avg_score': 0,
            'score_trend': 0,
            'critical_issues': 0,
            'serious_issues': 0,
            'total_scans': 0,
            'completed_scans': 0,
            'success_rate': '0%',
            'failed_scans': 0,
            'score_trends': {'labels': [], 'sites': {}},
            'issues_by_severity': {'dates': [], 'critical': [], 'serious': [], 'moderate': [], 'minor': [], 'sites': [], 'sites_data': {}}
        })

@app.route('/api/dashboard/seo-metrics', methods=['GET'])
@login_required
def api_dashboard_seo_metrics():
    """Get SEO/AEO optimization metrics for dashboard - ONLY from successful scans"""
    try:
        # Get list of successful scan IDs (those with .scan_success marker)
        successful_scan_ids = get_successful_scan_ids()
        
        if not successful_scan_ids:
            # No successful scans yet
            return jsonify({
                'seo_score': 0, 'seo_trend': 0, 'seo_issues': 0,
                'pages_scanned': 0, 'pages_analyzed': 0,
                'crawl_success': '100%', 'crawl_failed': 0,
                'seo_score_trends': {'labels': [], 'sites': {}},
                'aeo_score_trends': {'labels': [], 'sites': {}}
            })
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Build filter for successful scans (handles multi-site scan IDs)
        where_clause, params = build_successful_scan_filter(cursor, successful_scan_ids)
        
        # Get total pages with SEO data from successful scans only
        cursor.execute(f"""
            SELECT COUNT(*) FROM seo_results 
            WHERE scan_result_id IN (
                SELECT id FROM scan_results WHERE {where_clause}
            )
        """, params)
        total_seo_pages = cursor.fetchone()[0]
        
        # Get average SEO score from successful scans only
        prefixed_where_seo1 = where_clause.replace("scan_id", "sr.scan_id")
        cursor.execute(f"""
            SELECT AVG(seo.seo_score) FROM seo_results seo
            JOIN scan_results sr ON seo.scan_result_id = sr.id
            WHERE seo.seo_score > 0 AND ({prefixed_where_seo1})
        """, params)
        avg_seo_score_result = cursor.fetchone()[0]
        avg_seo_score = round(avg_seo_score_result) if avg_seo_score_result else 0
        
        # Get total SEO issues from successful scans only
        prefixed_where_seo = where_clause.replace("scan_id", "sr.scan_id")
        cursor.execute(f"""
            SELECT SUM(seo.issues_found) FROM seo_results seo
            JOIN scan_results sr ON seo.scan_result_id = sr.id
            WHERE ({prefixed_where_seo})
        """, params)
        total_seo_issues = cursor.fetchone()[0] or 0
        
        # Get pages scanned from successful scans only (last 30 days)
        cursor.execute(f"""
            SELECT SUM(pages_scanned) FROM scan_results
            WHERE scan_date >= date('now', '-30 days')
            AND ({where_clause})
        """, params)
        pages_scanned = cursor.fetchone()[0] or 0
        
        # Calculate crawl success rate based on .scan_success markers
        all_scan_dirs = len([d for d in RESULTS_DIR.iterdir() if d.is_dir()]) if RESULTS_DIR.exists() else 0
        successful_scans = len(successful_scan_ids)
        if all_scan_dirs > 0:
            crawl_success_rate = round((successful_scans / all_scan_dirs) * 100)
            crawl_failed = all_scan_dirs - successful_scans
        else:
            crawl_success_rate = 100
            crawl_failed = 0
        
        # Get SEO score trends by site (last 10 successful scans per site)
        prefixed_where_seo_trends = where_clause.replace("scan_id", "sr.scan_id")
        cursor.execute(f"""
            SELECT s.organisation, sr.site_id, AVG(seo.seo_score) as avg_score, sr.scan_date,
                   ROW_NUMBER() OVER (PARTITION BY sr.site_id ORDER BY sr.scan_date DESC) as row_num
            FROM scan_results sr
            JOIN sites s ON sr.site_id = s.id
            LEFT JOIN seo_results seo ON sr.id = seo.scan_result_id
            WHERE ({prefixed_where_seo_trends})
            AND seo.seo_score > 0
            GROUP BY s.organisation, sr.site_id, sr.scan_date, sr.id
            ORDER BY sr.site_id, sr.scan_date DESC
        """, params)
        seo_scan_data = cursor.fetchall()
        
        # Group by site and get last 10 scans for each
        from collections import defaultdict
        seo_sites_data = defaultdict(list)
        for org, site_id, avg_score, scan_date, row_num in seo_scan_data:
            if row_num <= 10:  # Only keep last 10 scans per site
                seo_sites_data[org].append({'score': round(avg_score) if avg_score else 0, 'scan_date': scan_date})
        
        # Reverse each site's data to show oldest to newest
        for org in seo_sites_data:
            seo_sites_data[org] = list(reversed(seo_sites_data[org]))
        
        # Find the maximum number of scans across all sites for consistent labels
        max_seo_scans = max(len(data) for data in seo_sites_data.values()) if seo_sites_data else 10
        
        seo_score_trends = {
            'labels': [f"Scan {i+1}" for i in range(max_seo_scans)],
            'sites': {org: [item['score'] for item in data] for org, data in seo_sites_data.items()}
        }
        
        # Get AEO score trends by site (similar to SEO score trends)
        # For now, we'll use the same data as SEO scores since AEO is a subset of SEO
        # In future, this could be separated if AEO-specific scores are tracked
        aeo_score_trends = {
            'labels': seo_score_trends['labels'],
            'sites': seo_score_trends['sites']  # Using SEO scores as proxy for AEO
        }
        
        # Calculate trend (compare recent vs earlier) from site-based trends
        all_site_scores = []
        for site_scores in seo_sites_data.values():
            all_site_scores.extend([s['score'] for s in site_scores])
        
        if len(all_site_scores) >= 2:
            recent_scores = all_site_scores[-3:] if len(all_site_scores) >= 3 else all_site_scores
            earlier_scores = all_site_scores[:3] if len(all_site_scores) >= 3 else all_site_scores
            recent_avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0
            earlier_avg = sum(earlier_scores) / len(earlier_scores) if earlier_scores else 0
            if earlier_avg > 0:
                seo_trend = round(((recent_avg - earlier_avg) / earlier_avg) * 100)
            else:
                seo_trend = 0
        else:
            seo_trend = 0
        
        conn.close()
        
        return jsonify({
            'seo_score': avg_seo_score,
            'seo_trend': seo_trend,
            'seo_issues': int(total_seo_issues),
            'pages_scanned': int(pages_scanned),
            'pages_analyzed': total_seo_pages,
            'crawl_success': f"{crawl_success_rate}%",
            'crawl_failed': crawl_failed,
            'seo_score_trends': seo_score_trends,  # Now includes by-site data
            'aeo_score_trends': aeo_score_trends  # Multi-site AEO scores
        })
    except Exception as e:
        print(f"Error getting SEO metrics: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'seo_score': 0,
            'seo_trend': 0,
            'seo_issues': 0,
            'pages_scanned': 0,
            'pages_analyzed': 0,
            'crawl_success': '100%',
            'crawl_failed': 0,
            'seo_score_trends': {'labels': [], 'sites': {}},
            'aeo_score_trends': {'labels': [], 'sites': {}}
        })

@app.route('/api/dashboard/scan-activity', methods=['GET'])
@login_required
def api_dashboard_scan_activity():
    """Get active scan information"""
    try:
        active_scans = []
        for scan_id, progress in SCAN_PROGRESS.items():
            if progress.get('status') in ['running', 'starting']:
                active_scans.append({
                    'id': scan_id,
                    'name': progress.get('config', 'Unknown'),
                    'status': progress.get('status', 'unknown'),
                    'progress': progress.get('progress', 0),
                    'message': progress.get('message', '')
                })
        
        return jsonify({
            'active_scans': active_scans
        })
    except Exception as e:
        print(f"Error getting scan activity: {e}")
        return jsonify({'active_scans': []})

@app.route('/api/schedules', methods=['GET'])
@login_required
def api_get_schedules():
    """Get all scan schedules"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, config_name, config_path, schedule_type, schedule_value, 
                   enabled, last_run, next_run, created_at, updated_at
            FROM scan_schedules
            ORDER BY config_name
        """)
        
        schedules = []
        for row in cursor.fetchall():
            schedules.append({
                'id': row[0],
                'config_name': row[1],
                'config_path': row[2],
                'schedule_type': row[3],
                'schedule_value': row[4],
                'enabled': bool(row[5]),
                'last_run': row[6],
                'next_run': row[7],
                'created_at': row[8],
                'updated_at': row[9]
            })
        
        conn.close()
        return jsonify({'schedules': schedules})
        
    except Exception as e:
        print(f"Error getting schedules: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedules', methods=['POST'])
@login_required
def api_create_schedule():
    """Create a new scan schedule"""
    try:
        data = request.json
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO scan_schedules (config_name, config_path, schedule_type, schedule_value, enabled)
            VALUES (?, ?, ?, ?, ?)
        """, (data['config_name'], data['config_path'], data['schedule_type'], 
              data['schedule_value'], data.get('enabled', True)))
        
        schedule_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Reload scheduler
        from scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler.reload_schedule(schedule_id)
        
        return jsonify({'success': True, 'id': schedule_id})
        
    except Exception as e:
        print(f"Error creating schedule: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedules/<int:schedule_id>', methods=['PUT'])
@login_required
def api_update_schedule(schedule_id):
    """Update a scan schedule"""
    try:
        data = request.json
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE scan_schedules
            SET config_name = ?, config_path = ?, schedule_type = ?, 
                schedule_value = ?, enabled = ?, updated_at = ?
            WHERE id = ?
        """, (data['config_name'], data['config_path'], data['schedule_type'],
              data['schedule_value'], data.get('enabled', True),
              datetime.now().isoformat(), schedule_id))
        
        conn.commit()
        conn.close()
        
        # Reload scheduler
        from scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler.reload_schedule(schedule_id)
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error updating schedule: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedules/<int:schedule_id>', methods=['DELETE'])
@login_required
def api_delete_schedule(schedule_id):
    """Delete a scan schedule"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM scan_schedules WHERE id = ?", (schedule_id,))
        
        conn.commit()
        conn.close()
        
        # Remove from scheduler
        from scheduler import get_scheduler
        scheduler = get_scheduler()
        job_id = f"scan_{schedule_id}"
        if scheduler.scheduler.get_job(job_id):
            scheduler.scheduler.remove_job(job_id)
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error deleting schedule: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedules/<int:schedule_id>/toggle', methods=['POST'])
@login_required
def api_toggle_schedule(schedule_id):
    """Enable/disable a scan schedule"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Toggle enabled status
        cursor.execute("""
            UPDATE scan_schedules
            SET enabled = 1 - enabled, updated_at = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), schedule_id))
        
        conn.commit()
        conn.close()
        
        # Reload scheduler
        from scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler.reload_schedule(schedule_id)
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error toggling schedule: {e}")
        return jsonify({'error': str(e)}), 500

# Start scheduler at module level so it runs under both Flask dev server and gunicorn
print("Initializing user authentication system...")
print("Initializing scan scheduler...")
from scheduler import start_scheduler
start_scheduler()
print("Scan scheduler started")

if __name__ == '__main__':
    _port = int(os.environ.get('PORT', 5001))
    _host = os.environ.get('HOST', '0.0.0.0')
    print(f"Starting CWAC-A11y Admin Interface on http://localhost:{_port}")
    app.run(debug=_FLASK_DEBUG, host=_host, port=_port, use_reloader=False)
