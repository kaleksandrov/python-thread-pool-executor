#!/usr/bin/env python

from Queue import Queue
from threading import Thread, Condition
import logging
import os


class ThreadPoolExecutorState(object):
   NOT_STARTED = 1
   RUNNING = 2
   STOPPING = 3
   STOPPED = 4


def get_number_of_cpus():
   try:
      return os.sysconf("SC_NPROCESSORS_ONLN")
   except Exception:
      return 8


class ThreadPoolExecutor(object):
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
      with self._lock:
         if self._state != ThreadPoolExecutorState.NOT_STARTED:
            raise ValueError('The %s has already been started!' % self.__class__.__name__)
         else:
            self._state = ThreadPoolExecutorState.RUNNING

      logging.debug('Spawning %s thread...', self._size)
      for thread in self._pool:
         thread.start()

   def shutdown(self, blocking=True):
      with self._lock:
         if self._state != ThreadPoolExecutorState.RUNNING:
            raise ValueError('The %s is not running!' % self.__class__.__name__)
         else:
            self._state = ThreadPoolExecutorState.STOPPING

         logging.debug('Notify waiting threads')
         self._lock.notifyAll()
         logging.debug('Threads notified')

      if blocking:
         for t in self._pool:
            logging.debug('Joining thread %s', t)
            t.join()

   def submit(self, task, *args):
      with self._lock:
         if self._state == ThreadPoolExecutorState.STOPPED or self._state == ThreadPoolExecutorState.STOPPING:
            raise ValueError('The %s has already been stopped!' % self.__class__.__name__)

         self._queue.put((task, args), False)
         self._lock.notify()
