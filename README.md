# Simple Cron

Simplecron is a Python module that creates a cron scheduler in Pyrhon

## Create a schedule

### Using the default scheduler

In simple situations, you can use the default scheduler to run a simple cron over a period of time:

```Python
from simplecron import base

def simple_function(job: base.Job, *args, **kwargs):
    print("Hello, World!", job)


base.every(1).second.do(some_func)


while True:
    base.run_pending_jobs()
    time.sleep(1)
```

> This is a blocking function, in other words it blocks the

## Using multiple schedulers

```Python
from simplecron import base

async def main():
	s1 = base.BaseScheduler()
	s2 = base.BaseScheduler()

	synchronizer = base.synchronize(s1, s2)

  	await synchronizer


if __name__ == "__main__":
	aysncio.run(main())
```

## Using  memory

The ressults of the jobs can be memorized in a local file, a database (sqlite) or in Redis.
