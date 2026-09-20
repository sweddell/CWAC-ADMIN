"""
Scheduled Scan Service
Manages automated scanning based on configured schedules
"""

import os
import sys
import sqlite3
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# Setup logging with absolute path
_log_dir = Path(__file__).parent.parent.parent / 'logs'
_log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(_log_dir / 'scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScanScheduler:
    """Manages scheduled scans"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        # Get paths relative to project root
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.project_root = base_dir
        self.db_path = os.path.join(base_dir, 'cwac_admin_app', 'database', 'bi_integration', 'cwac_analytics.db')
        self.scanner_script = os.path.join(base_dir, 'cwac', 'cwac.py')
        
    def start(self):
        """Start the scheduler"""
        logger.info("Starting scan scheduler...")
        schedule_ids = self.load_schedules()
        self.scheduler.start()
        
        # Update next_run times after scheduler has started
        for schedule_id in schedule_ids:
            self._update_next_run(schedule_id)
        
        logger.info("Scan scheduler started successfully")
        
    def stop(self):
        """Stop the scheduler"""
        logger.info("Stopping scan scheduler...")
        self.scheduler.shutdown()
        logger.info("Scan scheduler stopped")
        
    def load_schedules(self):
        """Load all enabled schedules from database"""
        schedule_ids = []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, config_name, config_path, schedule_type, schedule_value
                FROM scan_schedules
                WHERE enabled = 1
            """)
            
            schedules = cursor.fetchall()
            conn.close()
            
            for schedule_id, config_name, config_path, schedule_type, schedule_value in schedules:
                self.add_job(schedule_id, config_name, config_path, schedule_type, schedule_value)
                logger.info(f"Loaded schedule: {config_name} ({schedule_type}: {schedule_value})")
                schedule_ids.append(schedule_id)
                
            logger.info(f"Loaded {len(schedules)} active schedule(s)")
            
        except Exception as e:
            logger.error(f"Error loading schedules: {e}")
        
        return schedule_ids
            
    def add_job(self, schedule_id, config_name, config_path, schedule_type, schedule_value):
        """Add a scheduled job"""
        job_id = f"scan_{schedule_id}"
        
        # Remove existing job if it exists
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        
        # Create appropriate trigger
        trigger = self._create_trigger(schedule_type, schedule_value)
        
        if trigger:
            self.scheduler.add_job(
                func=self._run_scan,
                trigger=trigger,
                id=job_id,
                args=[schedule_id, config_name, config_path],
                name=f"Scan: {config_name}",
                replace_existing=True,
                misfire_grace_time=43200  # 12 hours - run missed jobs if within this window
            )
            
    def _create_trigger(self, schedule_type, schedule_value):
        """Create appropriate trigger based on schedule type"""
        try:
            if schedule_type == 'hourly':
                # Run every N hours
                hours = int(schedule_value)
                return IntervalTrigger(hours=hours)
                
            elif schedule_type == 'daily':
                # Run daily at specific time (HH:MM format)
                hour, minute = map(int, schedule_value.split(':'))
                return CronTrigger(hour=hour, minute=minute)
                
            elif schedule_type == 'weekly':
                # Run weekly on specific day and time (format: "day,HH:MM" e.g., "monday,09:00")
                day, time = schedule_value.split(',')
                hour, minute = map(int, time.split(':'))
                # Convert full day names to abbreviated format for APScheduler
                day_map = {
                    'monday': 'mon', 'tuesday': 'tue', 'wednesday': 'wed',
                    'thursday': 'thu', 'friday': 'fri', 'saturday': 'sat', 'sunday': 'sun'
                }
                day_abbr = day_map.get(day.lower(), day.lower())
                return CronTrigger(day_of_week=day_abbr, hour=hour, minute=minute)
                
            elif schedule_type == 'monthly':
                # Run monthly on specific day and time (format: "day,HH:MM" e.g., "1,09:00")
                day, time = schedule_value.split(',')
                hour, minute = map(int, time.split(':'))
                return CronTrigger(day=int(day), hour=hour, minute=minute)
                
            elif schedule_type == 'cron':
                # Custom cron expression
                return CronTrigger.from_crontab(schedule_value)
                
            else:
                logger.error(f"Unknown schedule type: {schedule_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating trigger: {e}")
            return None
            
    def _run_scan(self, schedule_id, config_name, config_path):
        """Execute a scheduled scan"""
        logger.info(f"Starting scheduled scan: {config_name}")
        
        try:
            # Update last run time
            self._update_last_run(schedule_id)
            
            # Extract just the filename from config_path (e.g., "config/config_test.json" → "config_test.json")
            config_filename = config_path.split('/')[-1] if '/' in config_path else config_path
            
            # Run the scanner - cwac.py expects just the config filename as first argument
            # IMPORTANT: Run from cwac/ directory so scanner can access its relative paths (./config/, ./chrome/, etc.)
            cwac_dir = Path(self.project_root) / 'cwac'
            result = subprocess.run(
                [sys.executable, self.scanner_script, config_filename],
                capture_output=True,
                text=True,
                cwd=cwac_dir,  # Run from cwac directory
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode == 0:
                logger.info(f"Scheduled scan completed successfully: {config_name}")
                
                # Auto-sync completed scan to database
                try:
                    self._sync_latest_scan()
                except Exception as e:
                    logger.error(f"Error syncing scan results: {e}")
            else:
                logger.error(f"Scheduled scan failed: {config_name}\nError: {result.stderr}")
                
            # Update next run time
            self._update_next_run(schedule_id)
            
        except subprocess.TimeoutExpired:
            logger.error(f"Scheduled scan timed out: {config_name}")
        except Exception as e:
            logger.error(f"Error running scheduled scan: {e}")
            
    def _update_last_run(self, schedule_id):
        """Update last run timestamp"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE scan_schedules
                SET last_run = ?, updated_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), datetime.now().isoformat(), schedule_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating last run: {e}")
            
    def _update_next_run(self, schedule_id):
        """Update next run timestamp"""
        try:
            job_id = f"scan_{schedule_id}"
            job = self.scheduler.get_job(job_id)
            
            if job and job.next_run_time:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE scan_schedules
                    SET next_run = ?, updated_at = ?
                    WHERE id = ?
                """, (job.next_run_time.isoformat(), datetime.now().isoformat(), schedule_id))
                
                conn.commit()
                conn.close()
                
        except Exception as e:
            logger.error(f"Error updating next run: {e}")
    
    def _sync_latest_scan(self):
        """Sync the most recent scan to the analytics database"""
        try:
            results_dir = Path(self.project_root) / 'cwac' / 'results'
            if not results_dir.exists():
                logger.warning("Results directory not found")
                return
            
            # Find the most recently modified scan directory with success marker
            scan_dirs = [d for d in results_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
            scan_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for scan_dir in scan_dirs:
                # Check for success marker
                if (scan_dir / '.scan_success').exists():
                    logger.info(f"Syncing scan: {scan_dir.name}")
                    
                    # Run sync script
                    sync_script = Path(self.project_root) / 'cwac_admin_app' / 'database' / 'bi_integration' / 'sync_single_scan.py'
                    if sync_script.exists():
                        result = subprocess.run(
                            [sys.executable, str(sync_script), str(scan_dir)],
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        
                        if result.returncode == 0:
                            logger.info(f"Successfully synced {scan_dir.name} to database")
                        else:
                            logger.error(f"Sync failed: {result.stderr}")
                    else:
                        logger.warning(f"Sync script not found: {sync_script}")
                    
                    break  # Only sync the latest scan
                    
        except Exception as e:
            logger.error(f"Error in auto-sync: {e}")
            
    def reload_schedule(self, schedule_id):
        """Reload a specific schedule"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT config_name, config_path, schedule_type, schedule_value, enabled
                FROM scan_schedules
                WHERE id = ?
            """, (schedule_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                config_name, config_path, schedule_type, schedule_value, enabled = result
                
                job_id = f"scan_{schedule_id}"
                
                # Remove existing job
                if self.scheduler.get_job(job_id):
                    self.scheduler.remove_job(job_id)
                
                # Add job if enabled
                if enabled:
                    self.add_job(schedule_id, config_name, config_path, schedule_type, schedule_value)
                    # Update next_run time after adding job
                    self._update_next_run(schedule_id)
                    logger.info(f"Reloaded schedule: {config_name}")
                else:
                    logger.info(f"Removed disabled schedule: {config_name}")
                    
        except Exception as e:
            logger.error(f"Error reloading schedule: {e}")
            
    def get_job_info(self, schedule_id):
        """Get information about a scheduled job"""
        job_id = f"scan_{schedule_id}"
        job = self.scheduler.get_job(job_id)
        
        if job:
            return {
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            }
        return None
        
    def list_jobs(self):
        """List all scheduled jobs"""
        jobs = self.scheduler.get_jobs()
        return [
            {
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            }
            for job in jobs
        ]

# Global scheduler instance
_scheduler = None

def get_scheduler():
    """Get or create the global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = ScanScheduler()
    return _scheduler

def start_scheduler():
    """Start the global scheduler"""
    scheduler = get_scheduler()
    scheduler.start()
    return scheduler

def stop_scheduler():
    """Stop the global scheduler"""
    global _scheduler
    if _scheduler:
        _scheduler.stop()
        _scheduler = None

if __name__ == '__main__':
    # Run as standalone service
    import time
    import signal
    
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        stop_scheduler()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create logs directory if it doesn't exist
    Path('logs').mkdir(exist_ok=True)
    
    scheduler = start_scheduler()
    logger.info("Scheduler service running. Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(60)  # Keep the service running
    except KeyboardInterrupt:
        stop_scheduler()
