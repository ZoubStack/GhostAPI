"""
Asynchronous Task Queue module for GhostAPI.

Supports:
- Celery
- Redis Queue (RQ)

Example:
    from ghostapi.tasks import task, AsyncRunner
    
    # Define a background task
    @task
    def generate_report(data):
        # Process in background
        report = create_report(data)
        return report
    
    # Use the async runner
    runner = AsyncRunner()
    
    @app.post(\"/generate-report\")
    async def create_report_endpoint(data: dict):
        # Launch task asynchronously
        job = runner.enqueue(generate_report, data)
        return {"job_id": job.id, "status": "pending"}
"""

import os
import uuid
import json
from typing import Optional, Any, Callable, Dict
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import threading
import queue


class TaskBackend(str, Enum):
    """Supported task backends."""
    CELERY = "celery"
    RQ = "rq"
    IN_MEMORY = "memory"


class TaskStatus(str, Enum):
    """Task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskResult:
    """Task execution result."""
    id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class InMemoryTaskQueue:
    """
    In-memory task queue for simple async execution.
    
    Useful for development and testing.
    """
    
    def __init__(self, max_workers: int = 4):
        self._queue = queue.Queue()
        self._results: Dict[str, TaskResult] = {}
        self._workers: list = []
        self._running = True
        self._max_workers = max_workers
        
        # Start workers
        for i in range(max_workers):
            worker = threading.Thread(target=self._worker, daemon=True)
            worker.start()
            self._workers.append(worker)
    
    def _worker(self):
        """Worker thread that processes tasks."""
        while self._running:
            try:
                item = self._queue.get(timeout=1)
                if item is None:
                    break
                
                task_id, func, args, kwargs = item
                
                # Update status to running
                self._results[task_id].status = TaskStatus.RUNNING
                
                try:
                    result = func(*args, **kwargs)
                    self._results[task_id].result = result
                    self._results[task_id].status = TaskStatus.COMPLETED
                except Exception as e:
                    self._results[task_id].error = str(e)
                    self._results[task_id].status = TaskStatus.FAILED
                
                self._results[task_id].completed_at = datetime.utcnow()
                self._queue.task_done()
                
            except queue.Empty:
                continue
    
    def enqueue(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> TaskResult:
        """Enqueue a task."""
        task_id = str(uuid.uuid4())
        
        result = TaskResult(
            id=task_id,
            status=TaskStatus.PENDING
        )
        self._results[task_id] = result
        
        self._queue.put((task_id, func, args, kwargs))
        
        return result
    
    def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Get task result."""
        return self._results.get(task_id)
    
    def stop(self):
        """Stop workers."""
        self._running = False
        for _ in self._workers:
            self._queue.put(None)


class CeleryTaskQueue:
    """
    Celery task queue implementation.
    
    Requires celery and redis to be installed.
    """
    
    def __init__(
        self,
        broker_url: str = "redis://localhost:6379/0",
        result_backend: str = "redis://localhost:6379/1",
        app_name: str = "ghostapi"
    ):
        self.broker_url = broker_url
        self.result_backend = result_backend
        self.app_name = app_name
        self._celery_app = None
    
    def _get_celery_app(self):
        """Get or create Celery app."""
        if self._celery_app is None:
            try:
                from celery import Celery
                
                self._celery_app = Celery(
                    self.app_name,
                    broker=self.broker_url,
                    backend=self.result_backend
                )
            except ImportError:
                raise ImportError(
                    "celery not installed. Install with: pip install celery"
                )
        
        return self._celery_app
    
    def enqueue(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Enqueue a task using Celery."""
        celery_app = self._get_celery_app()
        
        # If func is a decorated celery task, use it directly
        if hasattr(func, "delay"):
            return func.delay(*args, **kwargs)
        
        # Otherwise, create a task
        task = celery_app.task(func)
        return task.delay(*args, **kwargs)
    
    def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Get task result."""
        celery_app = self._get_celery_app()
        
        try:
            async_result = celery_app.AsyncResult(task_id)
            
            status = TaskStatus.PENDING
            if async_result.ready():
                status = TaskStatus.COMPLETED
                if async_result.successful():
                    result = async_result.result
                    error = None
                else:
                    result = None
                    error = str(async_result.info)
                    status = TaskStatus.FAILED
            elif async_result.state == "STARTED":
                status = TaskStatus.RUNNING
            
            return TaskResult(
                id=task_id,
                status=status,
                result=result if status == TaskStatus.COMPLETED else None,
                error=error
            )
        except Exception:
            return None


class RQTaskQueue:
    """
    Redis Queue (RQ) implementation.
    
    Requires redis and rq to be installed.
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        queue_name: str = "default"
    ):
        self.redis_url = redis_url
        self.queue_name = queue_name
        self._connection = None
        self._queue = None
    
    def _get_queue(self):
        """Get or create RQ queue."""
        if self._queue is None:
            try:
                import redis
                from rq import Queue
                
                self._connection = redis.from_url(self.redis_url)
                self._queue = Queue(
                    self.queue_name,
                    connection=self._connection
                )
            except ImportError:
                raise ImportError(
                    "rq not installed. Install with: pip install rq"
                )
        
        return self._queue
    
    def enqueue(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Enqueue a task using RQ."""
        queue = self._get_queue()
        job = queue.enqueue(func, *args, **kwargs)
        return job
    
    def get_result(self, job_id: str) -> Optional[TaskResult]:
        """Get task result."""
        queue = self._get_queue()
        
        try:
            job = queue.fetch_job(job_id)
            
            if job is None:
                return None
            
            status = TaskStatus.PENDING
            if job.is_finished:
                status = TaskStatus.COMPLETED
            elif job.is_failed:
                status = TaskStatus.FAILED
            elif job.is_started:
                status = TaskStatus.RUNNING
            
            return TaskResult(
                id=job_id,
                status=status,
                result=job.result if job.is_finished else None,
                error=job.exc_info if job.is_failed else None
            )
        except Exception:
            return None


# Task decorator
def task(
    backend: TaskBackend = TaskBackend.IN_MEMORY,
    queue_name: str = "default",
    **backend_kwargs
):
    """
    Decorator to mark a function as an async task.
    
    Example:
        @task(backend=TaskBackend.RQ)
        def generate_report(data):
            return create_report(data)
        
        # In FastAPI endpoint:
        job = generate_report.delay(data)
        return {"job_id": job.id}
    
    Args:
        backend: Task backend to use
        queue_name: Name of the queue
        **backend_kwargs: Backend-specific configuration
    """
    def decorator(func: Callable) -> Callable:
        # Create task queue based on backend
        if backend == TaskBackend.CELERY:
            task_queue = CeleryTaskQueue(**backend_kwargs)
        elif backend == TaskBackend.RQ:
            task_queue = RQTaskQueue(queue_name=queue_name, **backend_kwargs)
        else:
            task_queue = InMemoryTaskQueue()
        
        # Create delay method
        def delay(*args, **kwargs):
            return task_queue.enqueue(func, *args, **kwargs)
        
        func.delay = delay
        func.task_queue = task_queue
        
        return func
    
    return decorator


# Async Runner for managing tasks
class AsyncRunner:
    """
    Manager for async task execution.
    
    Example:
        runner = AsyncRunner(backend=TaskBackend.RQ)
        
        # Enqueue task
        job = runner.enqueue(generate_report, data)
        
        # Get result
        result = runner.get_result(job.id)
        
        # Wait for result
        result = runner.wait_for_result(job.id, timeout=30)
    """
    
    def __init__(
        self,
        backend: TaskBackend = TaskBackend.IN_MEMORY,
        **kwargs
    ):
        if backend == TaskBackend.CELERY:
            self._queue = CeleryTaskQueue(**kwargs)
        elif backend == TaskBackend.RQ:
            self._queue = RQTaskQueue(**kwargs)
        else:
            self._queue = InMemoryTaskQueue()
    
    def enqueue(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Enqueue a task."""
        return self._queue.enqueue(func, *args, **kwargs)
    
    def get_result(self, job_id: str) -> Optional[TaskResult]:
        """Get task result."""
        return self._queue.get_result(job_id)
    
    def wait_for_result(
        self,
        job_id: str,
        timeout: int = 30,
        poll_interval: float = 0.5
    ) -> Optional[TaskResult]:
        """Wait for task to complete."""
        import time
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result = self.get_result(job_id)
            
            if result and result.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                return result
            
            time.sleep(poll_interval)
        
        return None
    
    def get_job_status(self, job_id: str) -> Optional[TaskStatus]:
        """Get job status."""
        result = self.get_result(job_id)
        return result.status if result else None


# Background task execution for FastAPI
class BackgroundTasks:
    """
    FastAPI-compatible background task handler.
    
    Example:
        from fastapi import FastAPI
        from ghostapi.tasks import BackgroundTasks, run_in_background
        
        app = FastAPI()
        background_tasks = BackgroundTasks()
        
        @app.post(\"/process\")
        async def process_data(data: dict):
            def long_task():
                # Do heavy processing
                return {\"status\": \"completed\"}
            
            background_tasks.add_task(long_task)
            return {\"message\": \"Task started\"}
    """
    
    def __init__(self, runner: Optional[AsyncRunner] = None):
        self.runner = runner or AsyncRunner()
        self._tasks: list = []
    
    def add_task(self, func: Callable, *args, **kwargs):
        """Add a task to run in background."""
        self._tasks.append((func, args, kwargs))
    
    def execute(self):
        """Execute all background tasks."""
        for func, args, kwargs in self._tasks:
            self.runner.enqueue(func, *args, **kwargs)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.execute()


# Helper to run functions in background
def run_in_background(func: Callable, *args, **kwargs) -> Any:
    """
    Run a function in the background.
    
    Example:
        # In FastAPI endpoint
        @app.post(\"/generate-report\")
        async def generate_report():
            job = run_in_background(generate_report, data)
            return {\"job_id\": job.id, \"status\": \"pending\"}
    """
    from ghostapi import get_app
    
    # Try to get app context
    try:
        app = get_app()
        if app and hasattr(app, "state"):
            # Store runner in app state
            if not hasattr(app.state, "task_runner"):
                app.state.task_runner = AsyncRunner()
            
            return app.state.task_runner.enqueue(func, *args, **kwargs)
    except:
        pass
    
    # Fallback to default runner
    runner = AsyncRunner()
    return runner.enqueue(func, *args, **kwargs)
