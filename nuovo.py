from __future__ import annotations

from datetime import timedelta
from queue import PriorityQueue
from random import choice, choices
from typing import Optional


class Location:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def distance(self, other: Location) -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5


def find_next_prime(n: int):
    return find_prime_in_range(n, 2 * n)


def find_prime_in_range(a: int, b: int):
    for c in range(a, b):
        for i in range(2, c):
            if c % i == 0:
                break
        else:
            return c
    return -1


class Job:
    ident: int = 2

    def __init__(
        self,
        expected_start: timedelta,
        expected_end: timedelta,
        location: Location,
    ):
        self.id = Job.ident
        self.expected_start = expected_start
        self.expected_end = expected_end
        self.location = location
        self.start = expected_start
        self.end = expected_end
        Job.ident = find_next_prime(Job.ident)

    def travel_time_from(self, location: Optional[Location]) -> timedelta:
        if location is None:
            return timedelta(0)
        return timedelta(minutes=self.location.distance(location) / TRAVEL_SPEED)

    def duration(self) -> timedelta:
        return self.end - self.start


class State:
    def __init__(self, allocation: tuple[tuple[int, ...], ...]):
        self.allocation = allocation

    def __hash__(self) -> int:
        return sum((hash(tl) for tl in self.allocation))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return False
        return all(a in other.allocation for a in self.allocation)

    def __lt__(self, other: State) -> bool:
        return self.evaluate() < other.evaluate()

    def calculate_total_timeline_delay(self, timeline: int):
        return sum(self.calculate_timeline_delays(timeline), timedelta(0))

    def calculate_all_delays(self):
        return tuple(self.calculate_timeline_delays(i) for i in range(OPERATORS))

    def calculate_all_delays_flattened(self):
        return tuple(d for delays in self.calculate_all_delays() for d in delays)

    def calculate_total_delay(self):
        return sum(
            self.calculate_all_delays_flattened(),
            timedelta(0),
        )

    def calculate_total_timeline_travel(self, timeline: int):
        return sum(self.calculate_timeline_travels(timeline), timedelta(0))

    def calculate_all_travels(self):
        return tuple(self.calculate_timeline_travels(i) for i in range(OPERATORS))

    def calculate_all_travels_flattened(self):
        return tuple(d for travels in self.calculate_all_travels() for d in travels)

    def calculate_total_travel(self):
        return sum(
            self.calculate_all_travels_flattened(),
            timedelta(0),
        )

    def calculate_sum_of_squared_delay_minutes(self):
        return sum(
            (
                (d.total_seconds() / 60) ** 2
                for d in self.calculate_all_delays_flattened()
            )
        )

    def evaluate(self):
        return (
            self.calculate_sum_of_squared_delay_minutes(),
            self.calculate_total_travel().total_seconds() / 60,
        )

    def calculate_timeline_delays(self, timeline: int):
        time = timedelta(0)
        location = None
        res = ()
        for i in self.allocation[timeline]:
            job = JOBS[i]
            time += job.travel_time_from(location)
            location = job.location
            res += (max(timedelta(0), time - job.start),)
            time += job.duration()
            time = max(time, job.end)
        return res

    def calculate_timeline_travels(self, timeline: int):
        res = ()
        location = None
        for i in self.allocation[timeline]:
            job = JOBS[i]
            res += (job.travel_time_from(location),)
            location = job.location
        return res

    def coupled_jobs_timelines(self):
        res = ()
        for i, timeline in enumerate(self.allocation):
            res += tuple((j, i) for j in timeline)
        return res

    def copy_without_job(self, timeline: int, job: int):
        new_allocation = list(self.allocation)
        new_allocation[timeline] = tuple(
            j for j in new_allocation[timeline] if j != job
        )
        return State(tuple(new_allocation))

    def get_copies_with_job(self, timeline: int, job: int):
        for i in range(len(self.allocation[timeline])):
            t = self.allocation[timeline]
            changed_timeline = t[:i] + (job,) + t[i:]
            new_allocation = tuple(
                (changed_timeline if j == timeline else t)
                for j, t in enumerate(self.allocation)
            )
            yield State(new_allocation)

        t = self.allocation[timeline]
        changed_timeline = t + (job,)
        new_allocation = tuple(
            (changed_timeline if j == timeline else t)
            for j, t in enumerate(self.allocation)
        )
        yield State(new_allocation)

    def get_copies_with_moved_job(self, old_tl: int, new_tl: int, job: int):
        return self.copy_without_job(old_tl, job).get_copies_with_job(new_tl, job)

    def show(self):
        for i, timeline in enumerate(self.allocation):
            print(
                f"Operator {i}, Total delay: {self.calculate_total_timeline_delay(i)}, Total travel: {self.calculate_total_timeline_travel(i)}"
            )
            delays = self.calculate_timeline_delays(i)
            travels = self.calculate_timeline_travels(i)
            for j in range(len(timeline)):
                job = JOBS[timeline[j]]
                delay = delays[j]
                travel = travels[j]
                print(f"Job {timeline[j]}:")
                print(f"Travel start: {(job.start - travel) + delay}")
                print(f"Start: {job.start + delay}")
                print(f"End: {job.end + delay}")
                print(f"Delay: {delay}")
                print(f"Travel time: {travel}")
                print(f"Expected start: {job.start}")
                print(f"Expected end: {job.end}")
                print(f"Duration: {job.end-job.start}")
                print(f"Location: ({job.location.x}, {job.location.y})")
                print()
            print()
        print(
            f"Total delay: {self.calculate_total_delay()}, Total travel: {self.calculate_total_travel()}, Total delay squared: {self.calculate_sum_of_squared_delay_minutes()}"
        )

    def get_next_states(self):
        candidates = self.coupled_jobs_timelines()
        weights = tuple(
            (d + t).total_seconds()
            for d, t in zip(
                self.calculate_all_delays_flattened(),
                self.calculate_all_travels_flattened(),
            )
        )
        try:
            j, old_t = choices(
                candidates,
                weights,
            )[0]
        except ValueError:
            j, old_t = choice(candidates)

        candidates = range(OPERATORS)
        weights = tuple(
            (
                1
                / (
                    (
                        self.calculate_total_timeline_delay(i)
                        + self.calculate_total_timeline_travel(i)
                    ).total_seconds()
                    + 1
                )
                for i in range(OPERATORS)
            )
        )

        target_timeline = choices(
            candidates,
            weights,
        )[0]

        return self.get_copies_with_moved_job(old_t, target_timeline, j)


class Explorer:
    threshold = (5, 5)

    def __init__(self):
        self.fringe: PriorityQueue[tuple[tuple[float, float], State]] = PriorityQueue()

        timelines: list[tuple[int, ...]] = [()] * OPERATORS
        for i in range(len(JOBS)):
            timelines[i % OPERATORS] += (i,)

        self.best_state = State(tuple(timelines))
        self.best_score = self.best_state.evaluate()

        self.fringe.put((self.best_score, self.best_state))

    def explore(self):
        counter = 0
        bad_iterations = 0
        visited: set[State] = set()
        visited.add(self.best_state)

        while self.fringe.qsize() > 0:
            score, state = self.fringe.get()

            if score < self.best_score:
                visited.remove(state)
                self.best_score = score
                self.best_state = state
                bad_iterations = 0
                print(f"New best score at {counter}: {score}")

            if bad_iterations > 10000:
                break

            for new_state in state.get_next_states():
                if new_state not in visited:
                    visited.add(new_state)
                    new_score = new_state.evaluate()
                    self.fringe.put((new_score, new_state))

            counter += 1
            bad_iterations += 1

        self.best_state.show()


TRAVEL_SPEED = 250  # meters per minute

l1 = Location(0, 0)
l2 = Location(1000, 1000)
l3 = Location(1500, 600)
l4 = Location(200, 2000)


JOBS: tuple[Job, ...] = (
    Job(timedelta(minutes=10), timedelta(minutes=30), l1),
    Job(timedelta(minutes=0), timedelta(minutes=110), l3),
    Job(timedelta(minutes=5), timedelta(minutes=45), l2),
    Job(timedelta(minutes=5), timedelta(minutes=54), l4),
    Job(timedelta(minutes=5), timedelta(minutes=77), l2),
    Job(timedelta(minutes=5), timedelta(minutes=54), l1),
    Job(timedelta(minutes=60), timedelta(minutes=90), l3),
    Job(timedelta(minutes=70), timedelta(minutes=90), l2),
    Job(timedelta(minutes=99), timedelta(minutes=122), l4),
    Job(timedelta(minutes=60), timedelta(minutes=75), l1),
    Job(timedelta(minutes=110), timedelta(minutes=130), l3),
)

OPERATORS = 4

Explorer().explore()
