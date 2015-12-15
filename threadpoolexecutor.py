#!/usr/bin/env python

import logging
import os
from Queue import Queue
from threading import Thread, Condition

DEFAULT_NUMBER_OF_THREADS = 8


def get_number_of_cpus():
    """
    Retrieves the number ot the available processors/cores/threads that can be used.
    Uses the API from the os package. If this information cannot be retrieved,
    returns the default value stored in DEFAULT_NUMBER_OF_THREADS constant.
    :return: The number of available processors/cores/threads.
    """
    try:
        return os.sysconf("SC_NPROCESSORS_ONLN")
    except Exception:
        return DEFAULT_NUMBER_OF_THREADS


class ThreadPoolExecutorState(object):
    """
    Represents the different states of the ThreadPoolExecutor class.
    """

    NOT_STARTED = 1
    RUNNING = 2
    STOPPING = 3
    STOPPED = 4


class ThreadPoolExecutor(object):
    """
    Creates a pool of thread that can be reused for multiple tasks. The tasks are submitted to the executor
    and it is responsible to deliver them to the working threads. The API allows its client to block until
    the task execution completes or to continue its work while the threads are doing their job in the background.

    A simple example of usage is as follows:

        def task1(value):
            ...

        def task2(value):
            ...

        executor = ThreadPoolExecutor(16)
        executor.start()
        ...
        executor.submit(task1, value1)
        executor.submit(task1, value2)
        executor.submit(task2, value3)
        executor.submit(task2, value4)
        ...
        executor.shutdown(True)
    """

    def __init__(self, size=get_number_of_cpus()):
        self._queue = Queue()
        self._size = size
        self._pool = []
        self._lock = Condition()
        self._state = ThreadPoolExecutorState.NOT_STARTED

        def execute_task():
            while True:
                with self._lock:
                    if self._state == ThreadPoolExecutorState.RUNNING:
                        if not self._queue.empty():
                            task, args = self._queue.get(False)
                        else:
                            logging.debug('Start waiting...')
                            self._lock.wait()
                            continue
                    elif self._state == ThreadPoolExecutorState.STOPPING:
                        if not self._queue.empty():
                            task, args = self._queue.get(False)
                        else:
                            break
                    elif self._state == ThreadPoolExecutorState.STOPPED:
                        break
                    else:
                        raise ValueError('Unknown state: %s', self._state)

                if task:
                    try:
                        task(*args)
                    except Exception, ex:
                        logging.error('Error while executing task in the thread pool.')
                        logging.exception(ex)

            logging.debug('Finished!')

        for _ in range(size):
            thread = Thread(target=execute_task)
            thread.daemon = True
            self._pool.append(thread)

    def start(self):
        """
        Starts the executor by spawning the needed threads.
        """
        with self._lock:
            self._validate_state(ThreadPoolExecutorState.NOT_STARTED)
            self._state = ThreadPoolExecutorState.RUNNING

        logging.debug('Spawning %s thread...', self._size)
        for thread in self._pool:
            thread.start()

    def shutdown(self, blocking=True):
        """
        Stops the executor. Stopping does not happen immediately, the worker threads will execute all the tasks
        from the queue before stopping. The client can choose if to wait the stopping process to finish or
        to allow this to happen in the background.
        :param blocking: If should wait for the stopping process to finish by blocking the current thread.
        """
        with self._lock:
            self._validate_state(ThreadPoolExecutorState.RUNNING)
            self._state = ThreadPoolExecutorState.STOPPING

            logging.debug('Notify waiting threads')
            self._lock.notifyAll()
            logging.debug('Threads notified')

        if blocking:
            self._wait_threads_to_finish()
        else:
            wait_thread = Thread(target=self._wait_threads_to_finish())
            wait_thread.start()

    def _wait_threads_to_finish(self):
        """
        Joins the worker threads to the current one and afther they finish changes the state
        of the executor.
        """
        for thread in self._pool:
            logging.debug('Joining thread %s', thread)
            thread.join()

        with self._lock:
            self._state = ThreadPoolExecutorState.STOPPED

    def submit(self, task, *args):
        """
        Submits a new task to the executor. The task should be callable and may take unnamed arguments
        :param task: The task to be executed.
        :param args: The parameters to be passed to the task in the moment of execution.
        """
        with self._lock:
            self._validate_state(ThreadPoolExecutorState.NOT_STARTED, ThreadPoolExecutorState.RUNNING)
            self._queue.put((task, args), False)
            self._lock.notify()

    def _validate_state(self, *states):
        """
        Validates if the current executor's state is in the given ones. If not, raise a ValueError.
        :param states: The set of state to check for.
        """
        if self._state not in states:
            raise ValueError('Invalid state: %s' % self._state)
