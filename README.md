# Simple Cron

Simplecron is a simple and lightweight Python library for scheduling tasks using cron-like syntax. It allows you to define jobs that run at specific intervals or times, making it easy to automate repetitive tasks in your applications. This project was inspired by [**schedule.**](https://github.com/dbader/schedule)

## Creating a schedule

### Default scheduler

Simplecron uses a default scheduler that is created when the library is imported. You can create jobs using the `every` function, which creates a new job instance and attaches it to the default scheduler.

```Python
from simplecron import base


def callback(job: base.Job, *args, **kwargs):
    print("Hello, World!", job)


base.every(1).second.do(callback)


while True:
    base.run_pending()
    time.sleep(1)
```

By calling `every`, a new job is created. `schedule` attaches the unit of time to the job and finally `do` attaches the callback function.

> [!NOTE]
> This is a blocking function, in other words, it will block the main thread and will not allow other code to run while it is executing.

### Custom scheduler

You can also create your own scheduler by instantiating the `BaseScheduler` class. This can allow you to have multiple schedulers running concurrently, each with its own set of jobs.

```python
from simplecron.base import BaseScheduler

s1 = BaseScheduler()
s2 = BaseScheduler()

# Adds a job to the first scheduler that runs every second
s1.every(1).second.do(lambda job: print("Scheduler 1:", job))

# Adds a job to the second scheduler that runs every 2 seconds
s2.every(2).seconds.do(lambda job: print("Scheduler 2:", job))

def main():
	while True:
		s1.run_pending_jobs()
		s2.run_pending_jobs()
		time.sleep(1)

if __name__ == "__main__":
	main()
```

<!-- 
The same code can be achieved using the `Schedulers` class with the `start_blocking` method, which allows you to run multiple schedulers consecutively in a blocking manner.

```Python
import asyncio
from simplecron.base import BaseScheduler, Job
from simplecron.runners import Schedulers

synchronizer = Schedulers()

def callback(job: Job, *args, **kwargs):
	print("Hello, World!", job)

def main():
	s1 = BaseScheduler()
	s2 = BaseScheduler()

	synchronizer.add_scheduler(s1, "seconds", 1, callback)
	synchronizer.add_scheduler(s2, "seconds", 2, callback)

	synchronizer.start_blocking()

if __name__ == "__main__":
	main()
```

### Concurrent schedulers

To run multiple schedulers concurrently, you can use the `asyncio` library. This allows you to run multiple schedulers in an asynchronous manner, enabling better performance and responsiveness.

```Python
import asyncio
from simplecron.base import BaseScheduler, Job
from simplecron.runners import Schedulers

synchronizer = Schedulers()

def callback(job: Job, *args, **kwargs):
	print("Hello, World!", job)

async def main():
	s1 = BaseScheduler()
	s2 = BaseScheduler()

	synchronizer.add_scheduler(s1, "seconds", 1, callback)
	synchronizer.add_scheduler(s2, "seconds", 2, callback)

	await synchronizer.async_blocking()

if __name__ == "__main__":
	asyncio.run(main())
``` -->

## Event Listeners

You can attach event listeners to a scheduler to listen for specific events. There are three main listeners:

* `before` - Triggered before a job is executed.
* `after` - Triggered after a job is executed.
* `before_all` - Triggered before all jobs are executed.

```python
from simplecron.base import default_scheduler
from simplecron.utils import EventListenerEnum

default_scheduler.event_listener(EventListenerEnum.BEFORE_ALL, lambda scheduler: print("Before all jobs"))
```

The same can be achieved using the shortcut method `before_all_events`, `after_events`, and `before_events`:

```python
from simplecron.base import default_scheduler

default_scheduler.before_all_events(lambda scheduler: print("Before all jobs"))
default_scheduler.before_events(lambda job: print("Before job:", job))
default_scheduler.after_events(lambda job: print("After job:", job))
```

<!-- You can also attach event listeners to a specific jobs matching a certain set of tags or criteria. This allows you to have more granular control over which jobs trigger the event listeners.:

```python
from simplecron.base import default_scheduler
from simplecron.utils import EventListenerEnum

def before_all_jobs(jobs):
	print("Before all jobs:", jobs)
``` -->

## Jobs

### Cancelling

To cancel a job, it simple needs to return an instance of `Cancel`.

```python
def callback(job: Job, *args, **kwargs):
	print("Hello, World!", job)
	return Cancel(job, reason="Some reason")  # This will cancel the job after it runs once
```

### Types of jobs

**Every second**

```python
default_scheduler.every(1).second.do(callback)
```

**Every X second**

```python
default_scheduler.every(15).seconds.do(callback)
```

**Every minute**

```python
default_scheduler.every(1).minute.do(callback)
```

**Every X minutes**

```python
default_scheduler.every(15).minutes.do(callback)
```

**Every hour**

```python
default_scheduler.every(1).hour.do(callback)
```

**Every hours**

```python
default_scheduler.every(1).hours.do(callback)
```

**Every day**

When no specific time is provided, the job will run automatically at the start of the day (00:00). If you need to run the job at a specific time, you must use the `at` method to specify the time in 24-hour format (HH:MM).

```python
default_scheduler.every(1).day.do(callback)
```

```python
default_scheduler.every(1).day.at(datetime.time(12, 00)).do(callback)
```

**Every days**

```python
default_scheduler.every(1).days.do(callback)
```

**Every week**

If not specific day and time is povided, the job will run automatically at the start of the week (Monday at 00:00). If you need to run the job at a specific day, you must use one of the properties `monday`, `tuesday`, `wednesday`, `thursday`, `friday`, `saturday` or `sunday`.

You can also use the `at` method to specify the time in 24-hour format (HH:MM).

```python
default_scheduler.every(1).week.do(callback)
```

```python
default_scheduler.every(1).week.at(datetime.time(12, 00)).do(callback)
```

**Every X day**

```python
default_scheduler.every(1).monday.do(callback)
default_scheduler.every(1).tuesday.do(callback)
default_scheduler.every(1).wednesday.do(callback)
default_scheduler.every(1).thursday.do(callback)
default_scheduler.every(1).friday.do(callback)
default_scheduler.every(1).saturday.do(callback)
default_scheduler.every(1).sunday.do(callback)
```
