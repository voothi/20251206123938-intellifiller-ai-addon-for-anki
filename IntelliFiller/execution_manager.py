from collections import deque
import threading

class ExecutionManager:
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.queue = deque()
        self.current_task = None
        self.queue_lock = threading.Lock()

    def enqueue(self, task):
        """
        Add a task (ProgressDialog) to the queue.
        If no task is running, start this one immediately.
        """
        with self.queue_lock:
            # Avoid duplicate queuing if possible, though logic in UI usually prevents this
            if task not in self.queue and task != self.current_task:
                self.queue.append(task)
                # task.update_status(f"Queued... Position: {len(self.queue)}") # Handled by broadcast now
        
        self._update_queue_positions()
        self._try_start_next()

    def _try_start_next(self):
        """
        Internal method to check if we can start the next task.
        """
        with self.queue_lock:
            if self.current_task is None and self.queue:
                self.current_task = self.queue.popleft()
                # Notify the task to start
                self.current_task.start_processing()
        
        # Update positions for remaining items
        self._update_queue_positions()

    def yield_execution(self, task):
        """
        Called when a running task wants to pause and let others run.
        The yielding task is NOT automatically re-queued here; 
        it is the caller's responsibility to decide if/when to re-enqueue (e.g. on Resume).
        """
        with self.queue_lock:
            if self.current_task == task:
                self.current_task = None
        
        # Immediately try to run the next one
        self._try_start_next()

    def notify_finished(self, task):
        """
        Called when a task completes naturally or is cancelled.
        """
        with self.queue_lock:
            if self.current_task == task:
                self.current_task = None
            
            # If the task was in the queue (e.g. cancelled while waiting), remove it
            if task in self.queue:
                self.queue.remove(task)

        self._update_queue_positions()
        self._try_start_next()

    def _update_queue_positions(self):
        """
        Updates the titles of all queued tasks to reflect their current position.
        """
        with self.queue_lock:
            for i, task in enumerate(self.queue):
                # We assume task has a method set_queue_position
                # Position is i+1
                try:
                    task.set_queue_position(i + 1)
                except:
                    pass
