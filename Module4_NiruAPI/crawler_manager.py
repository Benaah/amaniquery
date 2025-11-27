"""
CrawlerManager - Manages crawler processes and status
Extracted from api.py for modularity
"""
import os
import sys
import json
import subprocess
import threading
import time
import psutil
from pathlib import Path
from datetime import datetime
from loguru import logger
from fastapi import HTTPException

from Module4_NiruAPI.crawler_models import CrawlerDatabaseManager


class CrawlerManager:
    """Manager for crawler processes with database-backed status tracking"""
    
    def __init__(self, database_storage=None):
        self.crawlers = {}
        self.processes = {}
        self.logs = {}
        self.status_file = Path(__file__).parent / "crawler_status.json"
        self.database_storage = database_storage
        
        # Initialize database manager
        try:
            self.db_manager = CrawlerDatabaseManager()
            if self.db_manager._initialized:
                logger.info("Using PostgreSQL for crawler status storage")
            else:
                logger.warning("PostgreSQL not available, using in-memory storage")
        except Exception as e:
            logger.warning(f"Failed to initialize crawler database manager: {e}")
            self.db_manager = None
        
        # Load status from database or migrate from file
        self.load_status()
        
        # Start background status checker
        self.status_thread = threading.Thread(target=self._status_checker, daemon=True)
        self.status_thread.start()
    
    def set_database_storage(self, database_storage):
        """Set database storage for last run times lookup"""
        self.database_storage = database_storage
    
    def load_status(self):
        """Load crawler status from database or migrate from file"""
        # Initialize default crawlers
        default_crawlers = {
            "kenya_law": {"status": "idle", "last_run": None},
            "parliament": {"status": "idle", "last_run": None},
            "news_rss": {"status": "idle", "last_run": None},
            "global_trends": {"status": "idle", "last_run": None},
            "parliament_videos": {"status": "idle", "last_run": None}
        }
        
        if self.db_manager and self.db_manager._initialized:
            # Load from database
            try:
                db_statuses = self.db_manager.get_crawler_status()
                for name, default_status in default_crawlers.items():
                    if name in db_statuses:
                        self.crawlers[name] = db_statuses[name]
                    else:
                        # Initialize new crawler in database
                        self.crawlers[name] = default_status
                        self.db_manager.update_crawler_status(
                            name,
                            default_status["status"],
                        )
                    
                    # Check for zombie processes (running in DB but not actually running)
                    if self.crawlers[name]['status'] == 'running':
                        pid = self.crawlers[name].get('pid')
                        is_running = False
                        if pid:
                            try:
                                if psutil.pid_exists(pid):
                                    # Double check if it's a python process (optional)
                                    try:
                                        proc = psutil.Process(pid)
                                        if 'python' in proc.name().lower():
                                            is_running = True
                                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                                        pass
                            except Exception:
                                pass
                        
                        if not is_running:
                            logger.warning(f"Detected zombie crawler {name} (PID: {pid}). Marking as failed.")
                            self.crawlers[name]['status'] = 'failed'
                            self.crawlers[name]['pid'] = None
                            self.db_manager.update_crawler_status(
                                name, 
                                'failed', 
                                pid=None
                            )
                            self.db_manager.add_log(name, f"System restart detected: Marked zombie process (PID: {pid}) as failed")
                
                # Load logs from database
                for name in self.crawlers.keys():
                    self.logs[name] = self.db_manager.get_logs(name, limit=100)
                
                logger.info("Loaded crawler status from PostgreSQL database")
                
                # Migrate from file if it exists (one-time migration)
                if self.status_file.exists():
                    self._migrate_from_file()
                    
            except Exception as e:
                logger.error(f"Error loading crawler status from database: {e}")
                self.crawlers = default_crawlers.copy()
                self.logs = {name: [] for name in default_crawlers.keys()}
        else:
            # Fallback to file-based storage
            try:
                if self.status_file.exists():
                    with open(self.status_file, 'r') as f:
                        data = json.load(f)
                        self.crawlers = data.get('crawlers', default_crawlers)
                        self.logs = data.get('logs', {name: [] for name in default_crawlers.keys()})
                else:
                    self.crawlers = default_crawlers.copy()
                    self.logs = {name: [] for name in default_crawlers.keys()}
            except Exception as e:
                logger.error(f"Error loading crawler status from file: {e}")
                self.crawlers = default_crawlers.copy()
                self.logs = {name: [] for name in default_crawlers.keys()}
    
    def _migrate_from_file(self):
        """Migrate data from JSON file to database (one-time operation)"""
        try:
            if not self.status_file.exists():
                return
            
            logger.info("Migrating crawler status from JSON file to database...")
            with open(self.status_file, 'r') as f:
                data = json.load(f)
                file_crawlers = data.get('crawlers', {})
                file_logs = data.get('logs', {})
            
            # Migrate crawler statuses
            for name, status in file_crawlers.items():
                last_run = None
                if status.get('last_run'):
                    try:
                        # Try parsing ISO format datetime string
                        last_run_str = status['last_run']
                        if isinstance(last_run_str, str):
                            # Remove 'Z' suffix if present and parse
                            if last_run_str.endswith('Z'):
                                last_run_str = last_run_str[:-1] + '+00:00'
                            last_run = datetime.fromisoformat(last_run_str.replace('Z', ''))
                    except Exception:
                        pass
                
                self.db_manager.update_crawler_status(
                    name,
                    status.get('status', 'idle'),
                    last_run=last_run,
                    pid=status.get('pid'),
                    start_time=None
                )
            
            # Migrate logs
            for name, logs in file_logs.items():
                for log_entry in logs:
                    # Parse timestamp from log entry
                    try:
                        if log_entry.startswith('['):
                            timestamp_str = log_entry.split(']')[0][1:]
                            message = log_entry.split(']', 1)[1].strip()
                            try:
                                # Try parsing ISO format
                                if timestamp_str.endswith('Z'):
                                    timestamp_str = timestamp_str[:-1] + '+00:00'
                                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', ''))
                            except Exception:
                                # Fallback to current time if parsing fails
                                timestamp = datetime.utcnow()
                            self.db_manager.add_log(name, message, timestamp)
                        else:
                            self.db_manager.add_log(name, log_entry)
                    except Exception as e:
                        logger.warning(f"Error migrating log entry: {e}")
                        self.db_manager.add_log(name, log_entry)
            
            # Backup and remove old file
            backup_file = self.status_file.with_suffix('.json.backup')
            if not backup_file.exists():
                import shutil
                shutil.copy2(self.status_file, backup_file)
                logger.info(f"Backed up old status file to {backup_file}")
            
            logger.info("Migration completed successfully")
        except Exception as e:
            logger.error(f"Error migrating from file to database: {e}")
    
    def save_status(self):
        """Save crawler status to database"""
        if self.db_manager and self.db_manager._initialized:
            # Save to database
            try:
                for name, status in self.crawlers.items():
                    last_run = None
                    if status.get('last_run'):
                        try:
                            last_run_str = status['last_run']
                            if isinstance(last_run_str, str):
                                if last_run_str.endswith('Z'):
                                    last_run_str = last_run_str[:-1] + '+00:00'
                                last_run = datetime.fromisoformat(last_run_str.replace('Z', ''))
                        except Exception:
                            pass
                    
                    start_time = None
                    if status.get('start_time'):
                        try:
                            start_time_str = status['start_time']
                            if isinstance(start_time_str, str):
                                if start_time_str.endswith('Z'):
                                    start_time_str = start_time_str[:-1] + '+00:00'
                                start_time = datetime.fromisoformat(start_time_str.replace('Z', ''))
                        except Exception:
                            pass
                    
                    self.db_manager.update_crawler_status(
                        name,
                        status.get('status', 'idle'),
                        last_run=last_run,
                        pid=status.get('pid'),
                        start_time=start_time
                    )
            except Exception as e:
                logger.error(f"Error saving crawler status to database: {e}")
        else:
            # Fallback to file
            try:
                data = {
                    'crawlers': self.crawlers,
                    'logs': self.logs
                }
                with open(self.status_file, 'w') as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                logger.error(f"Error saving crawler status to file: {e}")
    
    def _status_checker(self):
        """Background thread to check process status"""
        while True:
            try:
                for crawler_name, process_info in list(self.processes.items()):
                    pid = process_info['pid']
                    try:
                        # Check if process is still running
                        process = process_info['process']
                        if process.poll() is not None:
                            # Process finished
                            exit_code = process.returncode
                            last_run_time = datetime.utcnow()
                            if exit_code == 0:
                                self.crawlers[crawler_name]['status'] = 'idle'
                                self._add_log(crawler_name, f"Process completed successfully (PID: {pid})")
                            else:
                                self.crawlers[crawler_name]['status'] = 'failed'
                                self._add_log(crawler_name, f"Process failed with exit code {exit_code} (PID: {pid})")
                            
                            # Clean up
                            del self.processes[crawler_name]
                            self.crawlers[crawler_name]['last_run'] = last_run_time.isoformat() + 'Z'
                            self.crawlers[crawler_name]['pid'] = None
                            self.crawlers[crawler_name]['start_time'] = None
                            self.save_status()
                        else:
                            # Process still running
                            self.crawlers[crawler_name]['status'] = 'running'
                            self.save_status()  # Update status periodically
                    except Exception as e:
                        logger.error(f"Error checking process {pid}: {e}")
                        self.crawlers[crawler_name]['status'] = 'failed'
                        self.crawlers[crawler_name]['pid'] = None
                        self.crawlers[crawler_name]['start_time'] = None
                        self._add_log(crawler_name, f"Error monitoring process: {e}")
                        if crawler_name in self.processes:
                            del self.processes[crawler_name]
                        self.save_status()
                
                time.sleep(5)  # Check every 5 seconds
            except Exception as e:
                logger.error(f"Error in status checker: {e}")
                time.sleep(10)
    
    def _add_log(self, crawler_name: str, message: str):
        """Add a log entry for a crawler"""
        timestamp = datetime.utcnow()
        timestamp_str = timestamp.isoformat() + 'Z'
        
        if self.db_manager and self.db_manager._initialized:
            # Save to database
            try:
                self.db_manager.add_log(crawler_name, message, timestamp)
                # Update in-memory cache (last 100)
                if crawler_name not in self.logs:
                    self.logs[crawler_name] = []
                self.logs[crawler_name].append(f"[{timestamp_str}] {message}")
                if len(self.logs[crawler_name]) > 100:
                    self.logs[crawler_name] = self.logs[crawler_name][-100:]
            except Exception as e:
                logger.error(f"Error adding log to database: {e}")
                # Fallback to in-memory
                if crawler_name not in self.logs:
                    self.logs[crawler_name] = []
                self.logs[crawler_name].append(f"[{timestamp_str}] {message}")
                if len(self.logs[crawler_name]) > 100:
                    self.logs[crawler_name] = self.logs[crawler_name][-100:]
        else:
            # Fallback to in-memory
            if crawler_name not in self.logs:
                self.logs[crawler_name] = []
            self.logs[crawler_name].append(f"[{timestamp_str}] {message}")
            if len(self.logs[crawler_name]) > 100:
                self.logs[crawler_name] = self.logs[crawler_name][-100:]
    
    def get_crawler_status(self):
        """Get status of all crawlers"""
        # Initialize default crawlers if not exists
        default_crawlers = {
            "kenya_law": {"status": "idle", "last_run": None},
            "parliament": {"status": "idle", "last_run": None},
            "news_rss": {"status": "idle", "last_run": None},
            "global_trends": {"status": "idle", "last_run": None},
            "parliament_videos": {"status": "idle", "last_run": None}
        }
        
        # Load from database if available
        if self.db_manager and self.db_manager._initialized:
            try:
                db_statuses = self.db_manager.get_crawler_status()
                for name, default_status in default_crawlers.items():
                    if name in db_statuses:
                        self.crawlers[name] = db_statuses[name]
                    else:
                        self.crawlers[name] = default_status
                
                # Load logs from database
                for name in self.crawlers.keys():
                    self.logs[name] = self.db_manager.get_logs(name, limit=100)
            except Exception as e:
                logger.error(f"Error loading crawler status from database: {e}")
                # Fallback to in-memory
                for name, default_status in default_crawlers.items():
                    if name not in self.crawlers:
                        self.crawlers[name] = default_status
                        self.logs[name] = []
        else:
            # Merge with saved status (in-memory)
            for name, default_status in default_crawlers.items():
                if name not in self.crawlers:
                    self.crawlers[name] = default_status
                    self.logs[name] = []
        
        # Try to get actual last run times from database
        self._update_last_run_times()
        
        # Return current status with logs
        result = {}
        for name, status in self.crawlers.items():
            result[name] = {
                **status,
                "logs": self.logs.get(name, [])
            }
        
        return result
    
    def _update_last_run_times(self):
        """Update last run times from database"""
        try:
            if self.database_storage is None:
                logger.warning("Database storage not available, skipping last run times update")
                return
            
            # Map crawler names to database categories/sources
            crawler_mapping = {
                "kenya_law": {"category": "Kenyan Law"},
                "parliament": {"category": "Parliament"},
                "news_rss": {"source_name": "News RSS"},
                "global_trends": {"category": "Global Trend"},
                "parliament_videos": {"category": "Parliamentary Record"}
            }
            
            with self.database_storage.get_db_session() as db:
                for crawler_name, filters in crawler_mapping.items():
                    try:
                        # Query the most recent crawl_date for this crawler type
                        from sqlalchemy import func
                        from Module3_NiruDB.database_storage import RawDocument
                        
                        query = db.query(func.max(RawDocument.crawl_date))
                        
                        if "category" in filters:
                            query = query.filter(RawDocument.category == filters["category"])
                        if "source_name" in filters:
                            query = query.filter(RawDocument.source_name == filters["source_name"])
                        
                        last_run = query.scalar()
                        
                        if last_run:
                            self.crawlers[crawler_name]["last_run"] = last_run.isoformat() + 'Z'
                        else:
                            # No data found, keep as None or set to never
                            self.crawlers[crawler_name]["last_run"] = None
                            
                    except Exception as e:
                        logger.warning(f"Error getting last run time for {crawler_name}: {e}")
                        self.crawlers[crawler_name]["last_run"] = None
                        
        except Exception as e:
            logger.warning(f"Error updating last run times from database: {e}")
    
    def start_crawler(self, crawler_name: str):
        """Start a specific crawler"""
        if crawler_name not in self.crawlers:
            raise HTTPException(status_code=404, detail=f"Crawler {crawler_name} not found")
        
        # Check if already running
        if crawler_name in self.processes:
            return {"status": "already_running", "message": f"Crawler {crawler_name} is already running"}
        
        try:
            # Get spider directory
            spider_dir = Path(__file__).parent.parent / "Module1_NiruSpider"
            
            # Map crawler names to spider names
            spider_mapping = {
                "kenya_law": "kenya_law_new_spider",
                "parliament": "parliament_spider", 
                "news_rss": "news_rss_spider",
                "global_trends": "global_trends_spider",
                "parliament_videos": "parliament_video_spider"
            }
            
            if crawler_name not in spider_mapping:
                raise HTTPException(status_code=404, detail=f"Unknown crawler: {crawler_name}")
            
            spider_name = spider_mapping[crawler_name]
            
            # Start subprocess with log capture
            cmd = [sys.executable, "crawl_spider.py", spider_name]
            
            # Create subprocess with pipes for log capture
            process = subprocess.Popen(
                cmd,
                cwd=str(spider_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Merge stderr with stdout
                bufsize=1,
                universal_newlines=True
            )
            
            # Store process info
            self.processes[crawler_name] = {
                'process': process,
                'pid': process.pid,
                'start_time': datetime.utcnow().isoformat() + 'Z'
            }
            
            # Update status
            start_time = datetime.utcnow()
            self.crawlers[crawler_name]['status'] = 'running'
            self.crawlers[crawler_name]['pid'] = process.pid
            self.crawlers[crawler_name]['start_time'] = start_time.isoformat() + 'Z'
            self._add_log(crawler_name, f"Started crawler process (PID: {process.pid})")
            self.save_status()
            
            # Start log reader thread
            log_thread = threading.Thread(
                target=self._read_process_logs, 
                args=(crawler_name, process), 
                daemon=True
            )
            log_thread.start()
            
            logger.info(f"Started {crawler_name} crawler subprocess (PID: {process.pid})")
            return {
                "status": "started", 
                "message": f"Crawler {crawler_name} started successfully", 
                "pid": process.pid
            }
            
        except Exception as e:
            logger.error(f"Error starting crawler {crawler_name}: {e}")
            self.crawlers[crawler_name]['status'] = 'failed'
            self._add_log(crawler_name, f"Failed to start: {str(e)}")
            self.save_status()
            raise HTTPException(status_code=500, detail=f"Failed to start crawler: {str(e)}")
    
    def _read_process_logs(self, crawler_name: str, process: subprocess.Popen):
        """Read logs from subprocess and store them"""
        try:
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                # Clean and store log line
                clean_line = line.strip()
                if clean_line:
                    self._add_log(crawler_name, clean_line)
        except Exception as e:
            self._add_log(crawler_name, f"Error reading logs: {str(e)}")
    
    def stop_crawler(self, crawler_name: str):
        """Stop a specific crawler"""
        if crawler_name not in self.crawlers:
            raise HTTPException(status_code=404, detail=f"Crawler {crawler_name} not found")
        
        if crawler_name not in self.processes:
            return {"status": "not_running", "message": f"Crawler {crawler_name} is not running"}
        
        try:
            process_info = self.processes[crawler_name]
            process = process_info['process']
            
            # Terminate process
            process.terminate()
            
            # Wait a bit for graceful shutdown
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't respond
                process.kill()
                process.wait()
            
            # Clean up
            del self.processes[crawler_name]
            self.crawlers[crawler_name]['status'] = 'idle'
            self.crawlers[crawler_name]['pid'] = None
            self.crawlers[crawler_name]['start_time'] = None
            self.crawlers[crawler_name]['last_run'] = datetime.utcnow().isoformat() + 'Z'
            self._add_log(crawler_name, f"Process stopped (PID: {process_info['pid']})")
            self.save_status()
            
            return {"status": "stopped", "message": f"Crawler {crawler_name} stopped successfully"}
            
        except Exception as e:
            logger.error(f"Error stopping crawler {crawler_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to stop crawler: {str(e)}")
