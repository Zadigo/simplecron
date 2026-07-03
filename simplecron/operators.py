from abc import ABC, abstractmethod
from typing import Sequence


class BaseOperator(ABC):
    def __init__(self, intervals: Sequence[int] = [], days: Sequence[str] = []):
        self.intervals = intervals
        self.days = days

    @abstractmethod
    def resolve(self, *args, **kwargs):
        pass


class And(BaseOperator):
    """Operator that the resolve the condition where the job should resolve
    on two ore more conditions. The job will only run if all conditions are met.

    For example, if you want to run a job every 10 minutes on Mondays and Wednesdays, 
    you can use the And operator to combine the two conditions::

        job = every(10).minutes.and_("monday", "wednesday").do(job_function)
    """

    def __init__(self, days: Sequence[str] = []):
        super().__init__(days=days)


class Between(BaseOperator):
    """Operator that resolves the condition where the job should run between two intervals or days.
    
    For example, if you want to run a job every minute between the 10th and 20th minute of the hour, 
    you can use the Between operator::

        job = every(1).minutes.between(10, 20).do(job_function)

    The same can be done with days, for example, if you want to run a job every 10 minutes between Monday and Wednesday::

        job = every(10).minutes.between("monday", "wednesday").do(job_function)
    """
    def __init__(self, interval_start: int = None, interval_end: int = None, day_start: str = None, day_end: str = None):
        _intervals = [interval_start, interval_end]
        _days = [day_start, day_end]
        super().__init__(intervals=_intervals, days=_days)
