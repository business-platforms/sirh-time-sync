# src/service/scheduler_service.py
import logging
import threading
import time
import schedule
from typing import Dict, Any, Optional, Callable

from src.data.repositories import ConfigRepository

logger = logging.getLogger(__name__)


class ScheduledJob:
    """Represents a scheduled job."""

    def __init__(self, name: str, interval: int, interval_unit: str, task: Callable, enabled: bool = True):
        self.name = name
        self.interval = interval
        self.interval_unit = interval_unit  # 'minutes', 'hours', or 'days'
        self.task = task
        self.enabled = enabled
        self.last_run = None
        self.next_run = None
        self.job = None


class SchedulerService:
    """Service for scheduling and managing jobs."""

    def __init__(self, config_repository: ConfigRepository):
        self.config_repository = config_repository
        self.jobs: Dict[str, ScheduledJob] = {}
        self.running = False
        self.scheduler_thread = None

    def register_job(
            self,
            name: str,
            task: Callable,
            interval: Optional[int] = None,
            interval_unit: str = 'minutes'
    ) -> None:
        """Register a job with the scheduler."""
        if name in self.jobs:
            logger.warning(f"Job {name} already registered. Updating.")

        # If interval not provided, get from config
        if interval is None:
            config = self.config_repository.get_config()
            if not config:
                logger.error(f"No configuration found for job {name}")
                return None

            # Map job name to config interval
            if name == 'attendance_collection':
                interval = config.collection_interval
                interval_unit = 'minutes'
            elif name == 'attendance_upload':
                interval = config.upload_interval
                interval_unit = 'minutes'
            elif name == 'user_import':
                interval = config.import_interval
                interval_unit = 'minutes'
            else:
                logger.error(f"Unknown job name: {name}")
                return None

        # Create job
        job = ScheduledJob(name, interval, interval_unit, task)
        self.jobs[name] = job
        logger.info(f"Registered job: {name} ({interval} {interval_unit})")

    def schedule_job(self, job: ScheduledJob) -> None:
        """Schedule a job with the scheduler library."""
        if job.interval_unit == 'minutes':
            job.job = schedule.every(job.interval).minutes.do(job.task)
        elif job.interval_unit == 'hours':
            job.job = schedule.every(job.interval).hours.do(job.task)
        elif job.interval_unit == 'days':
            job.job = schedule.every(job.interval).days.do(job.task)
        else:
            logger.error(f"Unknown interval unit: {job.interval_unit}")
            return

        logger.info(f"Scheduled job: {job.name} ({job.interval} {job.interval_unit})")

    def start(self) -> None:
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler is already running")
            return

        # Clear existing schedule
        schedule.clear()

        # Schedule all registered jobs
        for name, job in self.jobs.items():
            if job.enabled:
                self.schedule_job(job)

        # Start scheduler thread
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()

        logger.info("Scheduler started")

    def stop(self) -> None:
        """Stop the scheduler."""
        if not self.running:
            logger.warning("Scheduler is not running")
            return

        self.running = False
        schedule.clear()

        # Wait for thread to terminate
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=2.0)

        logger.info("Scheduler stopped")

    def _run_scheduler(self) -> None:
        """Run the scheduler loop."""
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def run_job_now(self, job_name: str) -> bool:
        """Run a job immediately."""
        if job_name not in self.jobs:
            logger.error(f"Job {job_name} not found")
            return False

        try:
            job = self.jobs[job_name]
            job.task()
            job.last_run = time.time()
            logger.info(f"Manually ran job: {job_name}")
            return True
        except Exception as e:
            logger.error(f"Error running job {job_name}: {e}")
            return False

    def update_job_interval(self, job_name: str, interval: int, interval_unit: str = None) -> bool:
        """Update a job's interval."""
        if job_name not in self.jobs:
            logger.error(f"Job {job_name} not found")
            return False

        job = self.jobs[job_name]
        job.interval = interval

        if interval_unit:
            job.interval_unit = interval_unit

        # If scheduler is running, reschedule the job
        if self.running and job.enabled:
            schedule.cancel_job(job.job)
            self.schedule_job(job)

        logger.info(f"Updated job interval: {job_name} ({interval} {job.interval_unit})")
        return True

    def enable_job(self, job_name: str, enabled: bool = True) -> bool:
        """Enable or disable a job."""
        if job_name not in self.jobs:
            logger.error(f"Job {job_name} not found")
            return False

        job = self.jobs[job_name]
        job.enabled = enabled

        # Update scheduler
        if self.running:
            if enabled and not job.job:
                self.schedule_job(job)
            elif not enabled and job.job:
                schedule.cancel_job(job.job)
                job.job = None

        logger.info(f"{'Enabled' if enabled else 'Disabled'} job: {job_name}")
        return True

    def get_job_status(self, job_name: str) -> Dict[str, Any]:
        """Get status information for a job."""
        if job_name not in self.jobs:
            logger.error(f"Job {job_name} not found")
            return {}

        job = self.jobs[job_name]

        return {
            'name': job.name,
            'interval': job.interval,
            'interval_unit': job.interval_unit,
            'enabled': job.enabled,
            'last_run': job.last_run,
            'next_run': job.next_run,
            'scheduled': job.job is not None
        }

    def get_all_job_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status information for all jobs."""
        return {name: self.get_job_status(name) for name in self.jobs}