from __future__ import annotations

from datetime import timedelta
import Instance
from typing import Self

class State:
    def __init__(self, allocation: tuple[tuple[int, ...], ...]):
        self.allocation = allocation

    def __hash__(self) -> int:
        return sum((hash(tl) for tl in self.allocation))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return False
        return all(a in other.allocation for a in self.allocation)

    def __lt__(self, other: Self) -> bool:
        return self.evaluate() < other.evaluate()

    def calculate_total_timeline_delay(self, timeline: int):
        return sum(self.calculate_timeline_delays(timeline), timedelta(0))

    def calculate_all_delays(self):
        return tuple(self.calculate_timeline_delays(i) for i in range(Instance.OPERATORS))

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
        return tuple(self.calculate_timeline_travels(i) for i in range(Instance.OPERATORS))

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
            job = Instance.JOBS[i]
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
            job = Instance.JOBS[i]
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
            if Instance.JOBS[i].start + delays[i] < current_time:
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
        print(
            f"Total delay: {self.calculate_total_delay()}, Total travel: {self.calculate_total_travel()}, Total delay squared: {self.calculate_sum_of_squared_delay_minutes()}"
        )

        for i, timeline in enumerate(self.allocation):
            print("-" * 30)
            print(
                f"Op.: {i}".ljust(4)
                + f" | Total delay: {self.calculate_total_timeline_delay(i)}".ljust(31)
                + f" | Total travel: {self.calculate_total_timeline_travel(i)}".ljust(32)
            )
            delays = self.calculate_timeline_delays(i)
            travels = self.calculate_timeline_travels(i)
            for j in range(len(timeline)):
                job = Instance.JOBS[timeline[j]]
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
            if Instance.JOBS[j].start + d >= current_time:
                res_candidates += ((j, t),)
                res_weights += (w,)
        return res_candidates, res_weights