import pytest
from IntelliFiller.execution_manager import ExecutionManager

@pytest.fixture(autouse=True)
def reset_execution_manager():
    ExecutionManager._instance = None
    yield
    ExecutionManager._instance = None

def test_execution_manager_singleton():
    em1 = ExecutionManager.instance()
    em2 = ExecutionManager.instance()
    assert em1 is em2

def test_enqueue_first_task(mocker):
    em = ExecutionManager.instance()
    
    mock_task = mocker.Mock()
    mock_task.start_processing = mocker.Mock()
    
    em.enqueue(mock_task)
    
    assert em.current_task is mock_task
    mock_task.start_processing.assert_called_once()
    assert len(em.queue) == 0

def test_enqueue_multiple_tasks(mocker):
    em = ExecutionManager.instance()
    
    task1 = mocker.Mock()
    task2 = mocker.Mock()
    task3 = mocker.Mock()
    
    # Track position calls
    task2.set_queue_position = mocker.Mock()
    task3.set_queue_position = mocker.Mock()
    
    em.enqueue(task1)
    em.enqueue(task2)
    em.enqueue(task3)
    
    assert em.current_task is task1
    assert list(em.queue) == [task2, task3]
    
    task2.set_queue_position.assert_called_with(1)
    task3.set_queue_position.assert_called_with(2)

def test_yield_execution(mocker):
    em = ExecutionManager.instance()
    
    task1 = mocker.Mock()
    task2 = mocker.Mock()
    
    em.enqueue(task1)
    em.enqueue(task2)
    
    assert em.current_task is task1
    
    # task1 yields execution
    em.yield_execution(task1)
    
    assert em.current_task is task2
    task2.start_processing.assert_called_once()
    assert len(em.queue) == 0

def test_notify_finished_current(mocker):
    em = ExecutionManager.instance()
    
    task1 = mocker.Mock()
    task2 = mocker.Mock()
    
    em.enqueue(task1)
    em.enqueue(task2)
    
    # task1 finishes
    em.notify_finished(task1)
    
    assert em.current_task is task2
    task2.start_processing.assert_called_once()
    assert len(em.queue) == 0

def test_notify_finished_queued(mocker):
    em = ExecutionManager.instance()
    
    task1 = mocker.Mock()
    task2 = mocker.Mock()
    task3 = mocker.Mock()
    
    task3.set_queue_position = mocker.Mock()
    
    em.enqueue(task1)
    em.enqueue(task2)
    em.enqueue(task3)
    
    # task2 is cancelled / finishes before starting
    em.notify_finished(task2)
    
    assert em.current_task is task1
    assert list(em.queue) == [task3]
    # task3 queue position should update to 1
    task3.set_queue_position.assert_called_with(1)

def test_enqueue_duplicate_is_ignored(mocker):
    em = ExecutionManager.instance()

    task1 = mocker.Mock()
    task1.start_processing = mocker.Mock()

    em.enqueue(task1)
    em.enqueue(task1)

    assert em.current_task is task1
    assert len(em.queue) == 0
    task1.start_processing.assert_called_once()
