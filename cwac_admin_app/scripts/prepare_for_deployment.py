#!/usr/bin/env python3
"""
Prepare CWAC-ADMIN for VPS Deployment
This script clears all scan data and results, preparing a clean installation.
"""

import os
import sqlite3
import shutil
from pathlib import Path

def clear_results_folder():
    """Clear all scan results from the results folder"""
    results_dir = Path('cwac/results')
    if results_dir.exists():
        print("📁 Clearing results folder...")
        for item in results_dir.iterdir():
            if item.is_dir() and item.name.startswith('20'):
                print(f"   Removing: {item.name}")
                shutil.rmtree(item)
            elif item.is_file() and item.name != '.gitkeep':
                print(f"   Removing: {item.name}")
                item.unlink()
        print("✅ Results folder cleared")
    else:
        print("⚠️  Results folder not found")

def clear_database():
    """Clear scan data from database while preserving schema and sites"""
    db_path = 'bi_integration/cwac_analytics.db'
    
    if not os.path.exists(db_path):
        print("⚠️  Database not found")
        return
    
    print("🗄️  Clearing database scan data...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Clear scan-related tables
    tables_to_clear = [
        'issue_details',
        'page_results', 
        'seo_results',
        'scan_results'
    ]
    
    for table in tables_to_clear:
        try:
            cursor.execute(f"DELETE FROM {table}")
            count = cursor.rowcount
            print(f"   Cleared {count} rows from {table}")
        except sqlite3.OperationalError as e:
            print(f"   ⚠️  Could not clear {table}: {e}")
    
    # Reset scan schedule run times
    try:
        cursor.execute("UPDATE scan_schedules SET last_run = NULL, next_run = NULL")
        print(f"   Reset {cursor.rowcount} scan schedules")
    except sqlite3.OperationalError:
        print("   ⚠️  Scan schedules table not found")
    
    conn.commit()
    conn.close()
    
    print("✅ Database cleared")

def clear_logs():
    """Clear old log files"""
    logs_dir = Path('logs')
    if logs_dir.exists():
        print("📋 Clearing log files...")
        for log_file in logs_dir.glob('*.log'):
            print(f"   Removing: {log_file.name}")
            log_file.unlink()
        print("✅ Logs cleared")

def show_deployment_checklist():
    """Display deployment checklist"""
    print("\n" + "="*60)
    print("🚀 DEPLOYMENT CHECKLIST")
    print("="*60)
    print("""
✅ Data Cleanup Complete
   - All scan results removed
   - Database scan data cleared
   - Log files cleared
   - Sites configuration preserved

📋 Before Deploying to Production Server:

1. Update Configuration:
   - Check admin_app.py for production settings
   - Update SECRET_KEY in .env
   - Configure proper database path

2. Transfer Files:
   rsync -avz --exclude='.git' --exclude='__pycache__' \\
         --exclude='.venv' --exclude='cwac/results/*' \\
         . user@your-server:/path/to/cwac_admin/

3. On Server - Setup:
   cd /path/to/cwac_admin
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

4. On Server - Create Systemd Service:
   sudo nano /etc/systemd/system/cwac_admin.service

5. On Server - Configure Nginx:
   sudo nano /etc/nginx/sites-available/cwac_admin

6. Change Default Password:
   - Login as admin/admin
   - Change password immediately!

7. Test Everything:
   - Run a test scan
   - Check scheduled scans
   - Verify site management

📄 Database Status:
   - Sites: Preserved
   - Scan Results: Cleared
   - Scan Schedules: Preserved (reset run times)
   - Users: Preserved

🔐 Security Reminders:
   - Change SECRET_KEY before deploying
   - Change admin password after first login
   - Set up SSL certificate
   - Configure firewall rules
   - Set DEBUG = False in production
""")
    print("="*60)

def main():
    print("\n🧹 CWAC-A11y Deployment Preparation")
    print("="*60)
    
    response = input("\n⚠️  This will DELETE all scan results and data. Continue? (yes/no): ")
    
    if response.lower() != 'yes':
        print("❌ Deployment preparation cancelled")
        return
    
    print("\n🚀 Starting cleanup...\n")
    
    clear_results_folder()
    clear_database()
    clear_logs()
    
    print("\n✅ Cleanup complete!")
    show_deployment_checklist()

if __name__ == '__main__':
    main()
