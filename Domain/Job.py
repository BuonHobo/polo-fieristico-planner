from datetime import timedelta
from typing import Optional
from Domain.Location import Location
import Instance

class Job:
    ident: int = 0

    def __init__(
        self,
        expected_start: timedelta,
        expected_end: timedelta,
        location: Location,
    ):
        self.id:int = Job.ident
        self.expected_start = expected_start
        self.expected_end = expected_end
        self.location = location
        self.start = expected_start
        self.end = expected_end
        Job.ident += 1

    def travel_time_from(self, location: Optional[Location]) -> timedelta:
        if location is None:
            return timedelta(0)
        return timedelta(minutes=self.location.distance(location) / Instance.TRAVEL_SPEED)

    def duration(self) -> timedelta:
        return self.end - self.start