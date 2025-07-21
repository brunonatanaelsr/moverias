"""
Background Jobs System for Move Marias
Advanced task management and scheduling system
"""
import threading
import time
import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.conf import settings
from django.core.mail import send_mass_mail
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model
from typing import Dict, List, Callable, Any
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)
User = get_user_model()

class JobStatus:
    """Job status constants"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

class BackgroundJob:
    """Individual background job"""
    
    def __init__(self, job_id: str, func: Callable, args: tuple = (), kwargs: dict = None, 
                 priority: int = 1, retry_count: int = 0, max_retries: int = 3):
        self.job_id = job_id
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.priority = priority
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.status = JobStatus.PENDING
        self.created_at = timezone.now()
        self.started_at = None
        self.completed_at = None
        self.error = None
        self.result = None
        
    def to_dict(self):
        """Convert job to dictionary for serialization"""
        return {
            'job_id': self.job_id,
            'func_name': f"{self.func.__module__}.{self.func.__name__}" if hasattr(self.func, '__name__') else str(self.func),
            'args': self.args,
            'kwargs': self.kwargs,
            'priority': self.priority,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error': self.error,
            'result': str(self.result) if self.result else None
        }

class JobScheduler:
    """Job scheduler and executor"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.jobs: Dict[str, BackgroundJob] = {}
        self.job_queue: List[BackgroundJob] = []
        self.running_jobs: Dict[str, threading.Thread] = {}
        self.shutdown = False
        self.worker_thread = None
        
        # Job persistence
        self.job_file = Path(settings.BASE_DIR) / 'logs' / 'background_jobs.json'
        self.job_file.parent.mkdir(exist_ok=True)
        
        # Load existing jobs
        self._load_jobs()
        
    def add_job(self, job_id: str, func: Callable, args: tuple = (), kwargs: dict = None, 
                priority: int = 1, delay: int = 0, max_retries: int = 3) -> BackgroundJob:
        """Add a new job to the queue"""
        
        # Check if job already exists
        if job_id in self.jobs:
            logger.warning(f"Job {job_id} already exists")
            return self.jobs[job_id]
        
        job = BackgroundJob(job_id, func, args, kwargs, priority, max_retries=max_retries)
        
        # Add delay if specified
        if delay > 0:
            job.created_at = timezone.now() + timedelta(seconds=delay)
        
        self.jobs[job_id] = job
        self.job_queue.append(job)
        
        # Sort by priority (higher priority first)
        self.job_queue.sort(key=lambda x: x.priority, reverse=True)
        
        logger.info(f"Added job {job_id} with priority {priority}")
        self._save_jobs()
        
        return job
    
    def start_scheduler(self):
        """Start the job scheduler"""
        if self.worker_thread and self.worker_thread.is_alive():
            logger.warning("Job scheduler already running")
            return
        
        self.shutdown = False
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info("Job scheduler started")
    
    def stop_scheduler(self):
        """Stop the job scheduler"""
        self.shutdown = True
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        self.executor.shutdown(wait=True)
        logger.info("Job scheduler stopped")
    
    def _worker_loop(self):
        """Main worker loop"""
        while not self.shutdown:
            try:
                # Process next job
                job = self._get_next_job()
                if job:
                    self._execute_job(job)
                else:
                    time.sleep(1)  # No jobs available, wait
                    
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _get_next_job(self) -> BackgroundJob:
        """Get the next job to execute"""
        if not self.job_queue:
            return None
        
        # Find next job that's ready to run
        current_time = timezone.now()
        for i, job in enumerate(self.job_queue):
            if (job.status == JobStatus.PENDING and 
                job.created_at <= current_time and
                len(self.running_jobs) < self.max_workers):
                
                # Remove from queue
                self.job_queue.pop(i)
                return job
        
        return None
    
    def _execute_job(self, job: BackgroundJob):
        """Execute a job"""
        try:
            job.status = JobStatus.RUNNING
            job.started_at = timezone.now()
            self.running_jobs[job.job_id] = threading.current_thread()
            
            logger.info(f"Executing job {job.job_id}")
            
            # Execute the job function
            result = job.func(*job.args, **job.kwargs)
            
            # Job completed successfully
            job.status = JobStatus.COMPLETED
            job.completed_at = timezone.now()
            job.result = result
            
            logger.info(f"Job {job.job_id} completed successfully")
            
        except Exception as e:
            # Job failed
            job.error = str(e)
            job.retry_count += 1
            
            if job.retry_count < job.max_retries:
                # Retry the job
                job.status = JobStatus.PENDING
                job.created_at = timezone.now() + timedelta(seconds=30)  # Retry after 30 seconds
                self.job_queue.append(job)
                logger.warning(f"Job {job.job_id} failed, retrying ({job.retry_count}/{job.max_retries})")
            else:
                # Max retries exceeded
                job.status = JobStatus.FAILED
                job.completed_at = timezone.now()
                logger.error(f"Job {job.job_id} failed permanently: {e}")
        
        finally:
            # Remove from running jobs
            if job.job_id in self.running_jobs:
                del self.running_jobs[job.job_id]
            
            # Save job state
            self._save_jobs()
    
    def get_job_status(self, job_id: str) -> dict:
        """Get the status of a job"""
        if job_id not in self.jobs:
            return {'error': 'Job not found'}
        
        return self.jobs[job_id].to_dict()
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        if job_id not in self.jobs:
            return False
        
        job = self.jobs[job_id]
        
        if job.status == JobStatus.RUNNING:
            # Can't cancel running job easily, mark as cancelled
            job.status = JobStatus.CANCELLED
            return True
        elif job.status == JobStatus.PENDING:
            # Remove from queue
            if job in self.job_queue:
                self.job_queue.remove(job)
            job.status = JobStatus.CANCELLED
            return True
        
        return False
    
    def get_job_statistics(self) -> dict:
        """Get job statistics"""
        total_jobs = len(self.jobs)
        if total_jobs == 0:
            return {'total_jobs': 0}
        
        status_counts = {}
        for job in self.jobs.values():
            status_counts[job.status] = status_counts.get(job.status, 0) + 1
        
        return {
            'total_jobs': total_jobs,
            'status_counts': status_counts,
            'queue_size': len(self.job_queue),
            'running_jobs': len(self.running_jobs),
            'max_workers': self.max_workers
        }
    
    def cleanup_old_jobs(self, days: int = 7):
        """Clean up old completed/failed jobs"""
        cutoff_date = timezone.now() - timedelta(days=days)
        jobs_to_remove = []
        
        for job_id, job in self.jobs.items():
            if (job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED] and 
                job.created_at < cutoff_date):
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.jobs[job_id]
        
        logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
        self._save_jobs()
        
        return len(jobs_to_remove)
    
    def _save_jobs(self):
        """Save jobs to file"""
        try:
            jobs_data = {job_id: job.to_dict() for job_id, job in self.jobs.items()}
            with open(self.job_file, 'w') as f:
                json.dump(jobs_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save jobs: {e}")
    
    def _load_jobs(self):
        """Load jobs from file"""
        try:
            if self.job_file.exists():
                with open(self.job_file, 'r') as f:
                    jobs_data = json.load(f)
                
                # Only load pending jobs (others are historical)
                for job_id, job_data in jobs_data.items():
                    if job_data.get('status') == JobStatus.PENDING:
                        # Would need to reconstruct function references
                        # For now, just load the data
                        logger.info(f"Found pending job {job_id} - manual restart required")
                        
        except Exception as e:
            logger.error(f"Failed to load jobs: {e}")

# Common job functions
def send_bulk_email(subject: str, message: str, recipient_list: List[str], from_email: str = None):
    """Send bulk email job"""
    try:
        from django.core.mail import send_mail
        
        if not from_email:
            from_email = settings.DEFAULT_FROM_EMAIL
        
        messages = []
        for recipient in recipient_list:
            messages.append((subject, message, from_email, [recipient]))
        
        send_mass_mail(messages, fail_silently=False)
        logger.info(f"Sent bulk email to {len(recipient_list)} recipients")
        
        return {
            'success': True,
            'recipients_count': len(recipient_list),
            'subject': subject
        }
        
    except Exception as e:
        logger.error(f"Bulk email job failed: {e}")
        raise

def cleanup_cache():
    """Cache cleanup job"""
    try:
        cache.clear()
        logger.info("Cache cleared successfully")
        return {'success': True, 'message': 'Cache cleared'}
    except Exception as e:
        logger.error(f"Cache cleanup failed: {e}")
        raise

def generate_report(report_type: str, **kwargs):
    """Generate report job"""
    try:
        # This would be implemented based on specific report types
        logger.info(f"Generating report: {report_type}")
        
        # Simulate report generation
        time.sleep(5)  # Simulate work
        
        return {
            'success': True,
            'report_type': report_type,
            'generated_at': timezone.now().isoformat(),
            'parameters': kwargs
        }
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise

def process_uploaded_file(file_path: str, user_id: int):
    """Process uploaded file job"""
    try:
        logger.info(f"Processing file: {file_path}")
        
        # Simulate file processing
        time.sleep(3)
        
        return {
            'success': True,
            'file_path': file_path,
            'user_id': user_id,
            'processed_at': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"File processing failed: {e}")
        raise

# Global job scheduler instance
job_scheduler = JobScheduler(max_workers=4)

# Convenience functions
def schedule_job(job_id: str, func: Callable, args: tuple = (), kwargs: dict = None, 
                priority: int = 1, delay: int = 0, max_retries: int = 3):
    """Schedule a background job"""
    return job_scheduler.add_job(job_id, func, args, kwargs, priority, delay, max_retries)

def get_job_status(job_id: str):
    """Get job status"""
    return job_scheduler.get_job_status(job_id)

def cancel_job(job_id: str):
    """Cancel a job"""
    return job_scheduler.cancel_job(job_id)

def get_job_stats():
    """Get job statistics"""
    return job_scheduler.get_job_statistics()

def start_background_jobs():
    """Start the background job system"""
    job_scheduler.start_scheduler()

def stop_background_jobs():
    """Stop the background job system"""
    job_scheduler.stop_scheduler()

# Auto-start the scheduler when module is imported
if hasattr(settings, 'BACKGROUND_JOBS_AUTO_START') and settings.BACKGROUND_JOBS_AUTO_START:
    start_background_jobs()
