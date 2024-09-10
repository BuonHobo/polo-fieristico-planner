from __future__ import annotations

from datetime import timedelta
from queue import PriorityQueue
from random import choices
from typing import Optional


class Location:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def distance(self, other: Location) -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5


class Job:
    ident: int = 0

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
        Job.ident += 1

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

    def get_copies_with_job(self, timeline: int, job: int, current_time: timedelta):
        delays = self.calculate_timeline_delays(timeline)
        for i in range(len(self.allocation[timeline])):
            if JOBS[i].start + delays[i] < current_time:
                continue
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

    def get_copies_with_moved_job(
        self, old_tl: int, new_tl: int, job: int, current_time: timedelta
    ):
        return self.copy_without_job(old_tl, job).get_copies_with_job(
            new_tl, job, current_time
        )

    def show(self):
        print("=" * 30)
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
                print(
                    f"Job: {job.id}".ljust(4)
                    + f" | Travel start: {(job.start - travel) + delay}".ljust(31)
                    + f" | Start: {job.start + delay}".ljust(24)
                    + f" | End: {job.end + delay}".ljust(22)
                    + f" | Delay: {delay}".ljust(24)
                    + f" | Travel time: {travel}".ljust(30)
                    + f" | Expected start: {job.expected_start}".ljust(33)
                    + f" | Expected end: {job.expected_end}".ljust(31)
                    + f" | Duration: {job.end-job.start}".ljust(27)
                    + f" | Location: ({job.location.x}, {job.location.y})".ljust(27)
                )
            print("-" * 30)
        print(
            f"Total delay: {self.calculate_total_delay()}, Total travel: {self.calculate_total_travel()}, Total delay squared: {self.calculate_sum_of_squared_delay_minutes()}"
        )
        print("--------------------------------------------------------")

    def filter_started_jobs(
        self,
        current_time: timedelta,
        candidates: tuple[tuple[int, int], ...],
        weights: tuple[float, ...],
    ):
        delays = self.calculate_all_delays_flattened()
        res_candidates = ()
        res_weights = ()
        for (j, t), w, d in zip(candidates, weights, delays):
            if JOBS[j].start + d >= current_time:
                res_candidates += ((j, t),)
                res_weights += (w,)
        return res_candidates, res_weights

    def get_next_states(self, current_time: timedelta):
        candidates = self.coupled_jobs_timelines()
        weights = tuple(
            (d + t).total_seconds()
            for d, t in zip(
                self.calculate_all_delays_flattened(),
                self.calculate_all_travels_flattened(),
            )
        )

        candidates, weights = self.filter_started_jobs(
            current_time, candidates, weights
        )
        try:
            j, old_t = choices(
                candidates,
                weights,
            )[0]
        except ValueError:
            return ()

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

        return self.get_copies_with_moved_job(old_t, target_timeline, j, current_time)


class Explorer:
    threshold = (5, 5)

    def __init__(self):
        timelines: list[tuple[int, ...]] = [()] * OPERATORS
        for i in range(len(JOBS)):
            timelines[i % OPERATORS] += (i,)

        self.best_state = State(tuple(timelines))

    def explore(self, current_time: timedelta):
        fringe: PriorityQueue[tuple[tuple[float, float], State]] = PriorityQueue()

        best_score = self.best_state.evaluate()
        fringe.put((best_score, self.best_state))

        counter = 0
        bad_iterations = 0
        visited: set[State] = set()
        visited.add(self.best_state)

        while fringe.qsize() > 0:
            score, state = fringe.get()
            visited.remove(state)

            if score < best_score:
                best_score = score
                self.best_state = state
                bad_iterations = 0
                print(f"New best score at {counter}: {score}")

            if bad_iterations > 10000:
                break

            for new_state in state.get_next_states(current_time):
                if new_state not in visited:
                    visited.add(new_state)
                    new_score = new_state.evaluate()
                    fringe.put((new_score, new_state))

            counter += 1
            bad_iterations += 1

        self.best_state.show()


TRAVEL_SPEED = 250  # meters per minute

l1 = Location(0, 0)
l2 = Location(1000, 1000)
l3 = Location(1500, 600)
l4 = Location(200, 2000)


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

explorer = Explorer()
Explorer().explore(timedelta(minutes=0))
jobs = list(JOBS)
jobs[3].end += timedelta(minutes=25)
jobs[7].start += timedelta(minutes=5)
JOBS = tuple(jobs)
explorer.explore(timedelta(minutes=25))
