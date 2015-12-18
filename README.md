# Python Thread Pool Executor
## What is this?
This is an implementation of the **Thread Pool Executor** pattern written in **Python** langugage. I find it quite useful when writing multithreaded programs as the responsibility for managing the threads lies on the executor. This logic was officially added in version *3.2* of the languge but there are still tons of projects that are running on version *2.\** (like mine).

## How to use
Just copy this file somewhere in your project and import it. Here is a sample example of how to use the executor class:
```python
   from threadpoolexecutor import ThreadPoolExecutor
   ...

   def task1(value):
      """
      Operation that has to be executed in parallel.
      """
      ...

   def task2(value):
      """
      Another operation that has to be executed in parallel.
      """
      ...

   # Instantiate the executor with the desired number of threads.
   executor = ThreadPoolExecutor(16)

   # Launch the threads. At this point they are up and waiting for a task to be submitted for an execution.
   executor.start()

   # Submit any number of tasks. When a task is submited if there is a waiting thread, it starts executing it, otherwise - the tasks remains in a queue. Once a thread becomes available it checks in the queue for pending tasks.
   executor.submit(task1, value1)
   executor.submit(task1, value2)
   executor.submit(task2, value3)
   executor.submit(task2, value4)
   ...

   # When you are ready you can request a shutdown on the executor. This does not happen immediately. The executor will stop when there is no pending task in the queue. However after the shutdown is initiated no new task can be submitted. You can pass an optional argument to the method that indicates if you want to block the current thread and wait for the executor to be completely stopped or you want this process to happen in the background while the current thread continues its execution.
   executor.shutdown(True)
```

## How to contribute
1. Fork the repo.
1. Add some cool stuff.
1. Send a pull request.
