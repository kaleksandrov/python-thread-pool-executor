#!/usr/bin/env python

from __future__ import with_statement

from random import random
from threading import RLock
from time import sleep

from threadpoolexecutor import ThreadPoolExecutor

lock = RLock()
result = {}


def task(value):
    sleep(random())
    with lock:
        result[value] = value ** 2


executor = ThreadPoolExecutor(10)

for i in range(100):
    executor.submit(task, i)

executor.start()
executor.shutdown(False)
print executor._state
print result
