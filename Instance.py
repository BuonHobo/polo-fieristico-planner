from datetime import timedelta

from Domain.Location import Location
from Domain.Job import Job

TRAVEL_SPEED = 250  # meters per minute

l1 = Location(0, 0)
l3 = Location(0, 1000)
l4 = Location(1000, 0)
l2 = Location(1000, 1000)


JOBS: tuple[Job, ...] = (
    Job(timedelta(minutes=0), timedelta(minutes=30), l1),
    Job(timedelta(minutes=0), timedelta(minutes=30), l1),
    Job(timedelta(minutes=0), timedelta(minutes=30), l1),
    Job(timedelta(minutes=0), timedelta(minutes=30), l2),
    Job(timedelta(minutes=0), timedelta(minutes=30), l2),
    Job(timedelta(minutes=30), timedelta(minutes=60), l1),
    Job(timedelta(minutes=30), timedelta(minutes=60), l1),
    Job(timedelta(minutes=30), timedelta(minutes=60), l2),
    Job(timedelta(minutes=30), timedelta(minutes=60), l2),
)

OPERATORS = 5