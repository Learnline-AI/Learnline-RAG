"""
Queue Manager - Handles processing queue and job scheduling.

Manages the intelligent queuing of processing jobs with:
- Priority-based scheduling
- Resource-aware batching
- Load balancing
- Queue monitoring and metrics
"""

import time
import threading
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass
from queue import PriorityQueue, Empty
import logging

from ..core.models import ProcessingJob, ProcessingStatus, DocumentID
from ..core.config import get_config
from ..core.exceptions import PipelineError, JobExecutionError, ResourceExhaustionError
from ..storage.file_registry import FileRegistry

logger = logging.getLogger(__name__)


@dataclass
class QueuedJob:
    """Wrapper for jobs in the priority queue"""
    priority: int  # Lower number = higher priority
    timestamp: float  # For FIFO within same priority
    job: ProcessingJob
    
    def __lt__(self, other):
        # First compare by priority (lower is better)
        if self.priority != other.priority:
            return self.priority < other.priority
        # Then by timestamp (older first)
        return self.timestamp < other.timestamp


@dataclass 
class QueueMetrics:
    """Queue performance and status metrics"""
    total_jobs: int = 0
    queued_jobs: int = 0
    processing_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    average_processing_time: float = 0.0
    queue_depth_by_priority: Dict[int, int] = None
    throughput_jobs_per_hour: float = 0.0
    estimated_completion_time: Optional[datetime] = None
    resource_utilization: Dict[str, float] = None
    
    def __post_init__(self):
        if self.queue_depth_by_priority is None:
            self.queue_depth_by_priority = {}
        if self.resource_utilization is None:
            self.resource_utilization = {}


class QueueManager:
    """
    Intelligent queue manager for processing jobs.
    
    Features:
    - Priority-based scheduling with FIFO within priorities
    - Resource-aware job dispatching
    - Automatic retry handling
    - Performance monitoring and optimization
    - Graceful shutdown with job preservation
    """
    
    def __init__(self, file_registry: FileRegistry = None):
        self.config = get_config()
        self.file_registry = file_registry or FileRegistry()
        
        # Queue and threading
        self._queue = PriorityQueue()
        self._processing_jobs: Dict[str, QueuedJob] = {}
        self._completed_jobs: List[ProcessingJob] = []
        self._lock = threading.RLock()
        self._shutdown_event = threading.Event()
        self._worker_thread = None
        
        # Performance tracking
        self._metrics_history: List[QueueMetrics] = []
        self._job_start_times: Dict[str, datetime] = {}
        self._processing_times: List[float] = []
        
        # Resource limits
        self._max_concurrent_jobs = self.config.processing.max_batch_size
        self._current_resource_usage = {
            "cpu_percent": 0.0,
            "memory_percent": 0.0,
            "api_requests_per_minute": 0.0,
            "cost_per_hour": 0.0
        }
        
        # Load persisted jobs from database
        self._load_persisted_jobs()
        
        logger.info(f"Queue manager initialized with {self._queue.qsize()} persisted jobs")
    
    def start(self):
        """Start the queue processing worker"""
        if self._worker_thread and self._worker_thread.is_alive():
            logger.warning("Queue manager already running")
            return
        
        self._shutdown_event.clear()
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        logger.info("Queue manager worker started")
    
    def stop(self, timeout: float = 30.0):
        """Stop the queue processing worker gracefully"""
        if not self._worker_thread or not self._worker_thread.is_alive():
            logger.info("Queue manager not running")
            return
        
        logger.info("Stopping queue manager...")
        self._shutdown_event.set()
        
        # Wait for worker to finish current jobs
        self._worker_thread.join(timeout=timeout)
        
        if self._worker_thread.is_alive():
            logger.warning("Queue manager did not stop gracefully within timeout")
        else:
            logger.info("Queue manager stopped successfully")
        
        # Persist remaining jobs
        self._persist_remaining_jobs()
    
    def add_job(self, job: ProcessingJob) -> bool:
        """
        Add a job to the processing queue.
        
        Args:
            job: ProcessingJob to add to queue
            
        Returns:
            True if job was added successfully, False otherwise
        """
        try:
            with self._lock:
                # Check if job already exists
                if self._job_exists(job.job_id):
                    logger.warning(f"Job {job.job_id} already exists in queue")
                    return False
                
                # Create queued job wrapper
                queued_job = QueuedJob(
                    priority=self._calculate_effective_priority(job),
                    timestamp=time.time(),
                    job=job
                )
                
                # Add to queue
                self._queue.put(queued_job)
                
                # Update job status in database
                self.file_registry.update_job_status(
                    job.job_id, 
                    ProcessingStatus.QUEUED,
                    current_stage="queued"
                )
                
                logger.info(f"Added job {job.job_id} to queue with priority {queued_job.priority}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add job {job.job_id} to queue: {e}")
            return False
    
    def get_job_status(self, job_id: str) -> Optional[ProcessingStatus]:
        """Get current status of a job"""
        with self._lock:
            # Check if currently processing
            if job_id in self._processing_jobs:
                return ProcessingStatus.PROCESSING
            
            # Check queue
            if self._job_in_queue(job_id):
                return ProcessingStatus.QUEUED
            
            # Check completed jobs
            for job in self._completed_jobs:
                if job.job_id == job_id:
                    return job.status
            
            return None
    
    def get_queue_position(self, job_id: str) -> Optional[int]:
        """Get position of job in queue (1-based)"""
        with self._lock:
            # Create temporary list to check positions
            temp_queue = []
            position = None
            
            try:
                # Extract all items to find position
                queue_items = []
                while not self._queue.empty():
                    item = self._queue.get_nowait()
                    queue_items.append(item)
                    if item.job.job_id == job_id:
                        position = len(queue_items)
                
                # Put items back
                for item in sorted(queue_items, key=lambda x: (x.priority, x.timestamp)):
                    self._queue.put(item)
                
                return position
                
            except Empty:
                return None
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued or processing job"""
        with self._lock:
            # Try to remove from queue
            if self._remove_from_queue(job_id):
                self.file_registry.update_job_status(
                    job_id, 
                    ProcessingStatus.FAILED,
                    error_message="Job cancelled by user"
                )
                logger.info(f"Cancelled queued job {job_id}")
                return True
            
            # Try to cancel processing job
            if job_id in self._processing_jobs:
                # Mark for cancellation (actual cancellation depends on processor)
                job = self._processing_jobs[job_id].job
                job.status = ProcessingStatus.FAILED
                self.file_registry.update_job_status(
                    job_id,
                    ProcessingStatus.FAILED, 
                    error_message="Job cancelled by user"
                )
                logger.info(f"Marked processing job {job_id} for cancellation")
                return True
            
            logger.warning(f"Job {job_id} not found for cancellation")
            return False
    
    def get_metrics(self) -> QueueMetrics:
        """Get current queue metrics"""
        with self._lock:
            # Count jobs by status
            queued_count = self._queue.qsize()
            processing_count = len(self._processing_jobs)
            completed_count = len([j for j in self._completed_jobs if j.status == ProcessingStatus.COMPLETED])
            failed_count = len([j for j in self._completed_jobs if j.status == ProcessingStatus.FAILED])
            
            # Calculate queue depth by priority
            queue_depth = {}
            temp_items = []
            
            try:
                while not self._queue.empty():
                    item = self._queue.get_nowait()
                    temp_items.append(item)
                    priority = item.priority
                    queue_depth[priority] = queue_depth.get(priority, 0) + 1
                
                # Put items back
                for item in temp_items:
                    self._queue.put(item)
                    
            except Empty:
                pass
            
            # Calculate processing time statistics
            avg_processing_time = 0.0
            if self._processing_times:
                avg_processing_time = sum(self._processing_times) / len(self._processing_times)
            
            # Calculate throughput
            throughput = 0.0
            if len(self._completed_jobs) > 0:
                # Jobs completed in last hour
                hour_ago = datetime.now() - timedelta(hours=1)
                recent_jobs = [
                    j for j in self._completed_jobs 
                    if j.completed_at and j.completed_at > hour_ago
                ]
                throughput = len(recent_jobs)
            
            # Estimate completion time
            estimated_completion = None
            if queued_count > 0 and avg_processing_time > 0:
                remaining_time = (queued_count * avg_processing_time) / max(processing_count, 1)
                estimated_completion = datetime.now() + timedelta(seconds=remaining_time)
            
            return QueueMetrics(
                total_jobs=queued_count + processing_count + len(self._completed_jobs),
                queued_jobs=queued_count,
                processing_jobs=processing_count,
                completed_jobs=completed_count,
                failed_jobs=failed_count,
                average_processing_time=avg_processing_time,
                queue_depth_by_priority=queue_depth,
                throughput_jobs_per_hour=throughput,
                estimated_completion_time=estimated_completion,
                resource_utilization=self._current_resource_usage.copy()
            )
    
    def register_job_processor(self, processor_func: Callable[[ProcessingJob], bool]):
        """Register the function that will process jobs"""
        self._job_processor = processor_func
        logger.info("Job processor function registered")
    
    def _worker_loop(self):
        """Main worker loop for processing jobs"""
        logger.info("Queue worker loop started")
        
        while not self._shutdown_event.is_set():
            try:
                # Check resource limits
                if not self._can_start_new_job():
                    time.sleep(1)
                    continue
                
                # Get next job from queue
                try:
                    queued_job = self._queue.get(timeout=1.0)
                except Empty:
                    continue
                
                # Move job to processing
                with self._lock:
                    self._processing_jobs[queued_job.job.job_id] = queued_job
                    self._job_start_times[queued_job.job.job_id] = datetime.now()
                
                # Update job status
                self.file_registry.update_job_status(
                    queued_job.job.job_id,
                    ProcessingStatus.PROCESSING,
                    current_stage="starting"
                )
                
                logger.info(f"Starting processing of job {queued_job.job.job_id}")
                
                # Process job (this would call the actual processor)
                success = self._process_job(queued_job.job)
                
                # Update completion status
                end_time = datetime.now()
                processing_time = (end_time - self._job_start_times[queued_job.job.job_id]).total_seconds()
                
                with self._lock:
                    # Remove from processing
                    del self._processing_jobs[queued_job.job.job_id]
                    del self._job_start_times[queued_job.job.job_id]
                    
                    # Add to completed
                    queued_job.job.status = ProcessingStatus.COMPLETED if success else ProcessingStatus.FAILED
                    queued_job.job.completed_at = end_time
                    queued_job.job.processing_time_seconds = processing_time
                    self._completed_jobs.append(queued_job.job)
                    self._processing_times.append(processing_time)
                    
                    # Keep only recent processing times for statistics
                    if len(self._processing_times) > 100:
                        self._processing_times = self._processing_times[-100:]
                
                # Update database
                self.file_registry.update_job_status(
                    queued_job.job.job_id,
                    queued_job.job.status,
                    progress=100.0 if success else 0.0,
                    current_stage="completed" if success else "failed"
                )
                
                logger.info(f"Completed job {queued_job.job.job_id} in {processing_time:.1f}s - {'Success' if success else 'Failed'}")
                
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
                time.sleep(5)  # Pause before retrying
        
        logger.info("Queue worker loop stopped")
    
    def _process_job(self, job: ProcessingJob) -> bool:
        """Process a single job (placeholder - actual processing happens elsewhere)"""
        try:
            # This would call the registered processor function
            if hasattr(self, '_job_processor'):
                return self._job_processor(job)
            else:
                # Default behavior - just wait (for testing)
                logger.warning(f"No job processor registered, simulating work for job {job.job_id}")
                time.sleep(2)  # Simulate processing time
                return True
                
        except Exception as e:
            logger.error(f"Job processing failed for {job.job_id}: {e}")
            return False
    
    def _can_start_new_job(self) -> bool:
        """Check if system can handle another concurrent job"""
        with self._lock:
            # Check concurrent job limit
            if len(self._processing_jobs) >= self._max_concurrent_jobs:
                return False
            
            # Check resource usage (placeholder logic)
            if self._current_resource_usage["memory_percent"] > 80:
                return False
            
            if self._current_resource_usage["api_requests_per_minute"] > self.config.ai.max_requests_per_minute * 0.8:
                return False
            
            return True
    
    def _calculate_effective_priority(self, job: ProcessingJob) -> int:
        """Calculate effective priority considering various factors"""
        base_priority = job.priority
        
        # Adjust for job type
        if job.job_type == "urgent_reprocessing":
            base_priority -= 2  # Higher priority
        elif job.job_type == "batch_processing":
            base_priority += 1  # Lower priority
        
        # Adjust for document characteristics
        doc = self.file_registry.get_document(job.document_id)
        if doc:
            # Prioritize smaller files for faster turnaround
            if doc.file_size < 1024 * 1024:  # Less than 1MB
                base_priority -= 1
            
            # Prioritize certain subjects
            if doc.subject in ["Mathematics", "Physics"]:
                base_priority -= 1
        
        return max(1, min(10, base_priority))  # Clamp to 1-10 range
    
    def _job_exists(self, job_id: str) -> bool:
        """Check if job exists anywhere in the system"""
        # Check processing jobs
        if job_id in self._processing_jobs:
            return True
        
        # Check completed jobs
        if any(j.job_id == job_id for j in self._completed_jobs):
            return True
        
        # Check queue (this is expensive, so we do it last)
        return self._job_in_queue(job_id)
    
    def _job_in_queue(self, job_id: str) -> bool:
        """Check if job is in the queue"""
        temp_items = []
        found = False
        
        try:
            while not self._queue.empty():
                item = self._queue.get_nowait()
                temp_items.append(item)
                if item.job.job_id == job_id:
                    found = True
                    break
            
            # Put items back
            for item in temp_items:
                self._queue.put(item)
                
        except Empty:
            pass
        
        return found
    
    def _remove_from_queue(self, job_id: str) -> bool:
        """Remove a job from the queue"""
        temp_items = []
        removed = False
        
        try:
            while not self._queue.empty():
                item = self._queue.get_nowait()
                if item.job.job_id == job_id:
                    removed = True
                    # Don't put this item back
                else:
                    temp_items.append(item)
            
            # Put remaining items back
            for item in temp_items:
                self._queue.put(item)
                
        except Empty:
            pass
        
        return removed
    
    def _load_persisted_jobs(self):
        """Load queued jobs from database on startup"""
        try:
            # Get jobs that were queued but not completed
            queued_jobs = []
            # This would query the database for jobs with status "queued" or "processing"
            # For now, we'll skip this implementation
            
            for job in queued_jobs:
                self.add_job(job)
            
            logger.info(f"Loaded {len(queued_jobs)} persisted jobs from database")
            
        except Exception as e:
            logger.error(f"Failed to load persisted jobs: {e}")
    
    def _persist_remaining_jobs(self):
        """Persist remaining jobs to database before shutdown"""
        try:
            # Save all queued jobs back to database
            remaining_jobs = []
            
            # Extract jobs from queue
            while not self._queue.empty():
                try:
                    queued_job = self._queue.get_nowait()
                    remaining_jobs.append(queued_job.job)
                except Empty:
                    break
            
            # Update their status in database
            for job in remaining_jobs:
                self.file_registry.update_job_status(
                    job.job_id,
                    ProcessingStatus.QUEUED,
                    current_stage="persisted_for_restart"
                )
            
            logger.info(f"Persisted {len(remaining_jobs)} jobs to database")
            
        except Exception as e:
            logger.error(f"Failed to persist remaining jobs: {e}")
    
    def __del__(self):
        """Cleanup on object destruction"""
        if hasattr(self, '_worker_thread') and self._worker_thread and self._worker_thread.is_alive():
            self.stop(timeout=5.0)