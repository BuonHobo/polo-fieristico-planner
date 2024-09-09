from __future__ import annotations

from datetime import timedelta
from queue import PriorityQueue
from random import choices


class Location:
    travel_speed = 250  # meters per minute

    def __init__(self, x: float, y: float):
        self.__x = x
        self.__y = y

    def distance_to(self, location: Location) -> float:
        return ((self.__x - location.__x) ** 2 + (self.__y - location.__y) ** 2) ** 0.5

    def travel_time_to(self, location: Location) -> timedelta:
        return timedelta(minutes=self.distance_to(location) / self.travel_speed)

    def __hash__(self) -> int:
        return hash((self.__x, self.__y))

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Location):
            return self.__x == o.__x and self.__y == o.__y
        return False


class Job:
    def __init__(self, id: int, start: timedelta, end: timedelta, location: Location):
        self.__id = id
        self.__location = location
        self.__start = start
        self.__end = end

    def get_id(self):
        return self.__id

    def get_location(self):
        return self.__location

    def get_start(self):
        return self.__start

    def get_end(self):
        return self.__end

    def get_travel_time(self, source: Location):
        return source.travel_time_to(self.__location)

    def print(self):
        print("Job: ", self.__id, " Start: ", self.__start, " End: ", self.__end)

    def __hash__(self) -> int:
        return hash(self.get_id())

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Job):
            return self.get_id() == o.get_id()
        return False


class Timeline:
    def __init__(self, jobs: tuple[Job, ...]):
        self.jobs: tuple[Job, ...] = jobs

    def __hash__(self) -> int:
        return hash(self.jobs)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, type(self)):
            return self.jobs == o.jobs
        return False

    def get_total_transit_time(self):
        if self.size() == 0:
            return timedelta(0)
        time = timedelta(0)
        last_location = self.jobs[0].get_location()
        for j in self.jobs:
            time += j.get_travel_time(last_location)
            last_location = j.get_location()
        return time

    def size(self):
        return len(self.jobs)

    def copy_without_job(self, job: Job):
        return Timeline(tuple((j for j in self.jobs if j.get_id() != job.get_id())))

    def print(self):
        if self.size() == 0:
            return
        last_location = self.jobs[0].get_location()
        jobs, delays = self.get_jobs_delays()
        for job, delay in zip(jobs, delays):
            print(
                "Job:",
                str(job.get_id()).ljust(6),
                "| Travel start:",
                str(
                    delay + (job.get_start() - job.get_travel_time(last_location))
                ).ljust(16),
                "| Job start:",
                str(delay + job.get_start()).ljust(16),
                "| Job end:",
                str(delay + job.get_end()).ljust(16),
                "| Delay:",
                str(delay).ljust(16),
                "| Travel time:",
                str(job.get_travel_time(last_location)).ljust(16),
                "| Duration:",
                str(job.get_end() - job.get_start()).ljust(16),
                "| Target start:",
                str(job.get_start()).ljust(16),
                "| Target end:",
                str(job.get_end()).ljust(16),
            )
            last_location = job.get_location()

    def get_delays(self):
        if self.size() == 0:
            return ()
        time = timedelta(0)
        delays: tuple[timedelta, ...] = ()
        last_location = self.jobs[0].get_location()
        for j in self.jobs:
            time += j.get_travel_time(last_location)
            last_location = j.get_location()
            delays += (max(timedelta(0), time - j.get_start()),)
            time += j.get_end() - j.get_start()  # job duration
            time = max(time, j.get_end())  # wait until the end of the job
        return delays

    def get_jobs_delays(self):
        return self.jobs, self.get_delays()

    def get_delay_sum(self):
        total = timedelta(0)
        for delay in self.get_delays():
            total += delay
        return total

    def copy_with_appended_job(self, job: Job):
        return Timeline(self.jobs + (job,))

    def copy_with_inserted_job(self, job: Job, i: int):
        return Timeline(self.jobs[:i] + (job,) + self.jobs[i:])

    def get_next_states(self, job: Job):
        timeline = self.copy_without_job(job)

        res: tuple[Timeline, ...] = ()
        for i in range(timeline.size()):  # insert in the middle
            res += (timeline.copy_with_inserted_job(job, i),)

        res += (timeline.copy_with_appended_job(job),)  # append at the end

        return res


class State:
    def __init__(self, timelines: tuple[Timeline, ...]):
        self.timelines = timelines

    def __hash__(self) -> int:
        return hash(sum(hash(tl) for tl in self.get_timelines()))

    def __eq__(self, o: object) -> bool:
        if isinstance(o, type(self)):
            return set(self.get_timelines()) == set(o.get_timelines())
        return False

    def get_timelines(self):
        return self.timelines

    def get_jobs_delays(self):
        jobs: tuple[Job, ...] = ()
        delays: tuple[timedelta, ...] = ()

        for timeline in self.get_timelines():
            timeline_jobs, timeline_delays = timeline.get_jobs_delays()
            jobs += timeline_jobs
            delays += timeline_delays

        return jobs, delays

    def get_operator(self, timeline: Timeline):
        for i, tl in enumerate(self.get_timelines()):
            if tl == timeline:
                return i

    def get_delay_sum(self):
        total = timedelta(0)
        for timeline in self.get_timelines():
            total += timeline.get_delay_sum()
        return total

    def get_total_transit_time(self):
        time = timedelta(0)
        for timeline in self.get_timelines():
            time += timeline.get_total_transit_time()
        return time

    def get_sum_of_squared_delays(self):
        score = 0
        for timeline in self.get_timelines():
            score += sum(
                ((delay.total_seconds() / 60) ** 2 for delay in timeline.get_delays())
            )
        return score

    def evaluate(self) -> tuple[float, float]:
        return (
            self.get_sum_of_squared_delays(),
            self.get_total_transit_time().total_seconds() / 60,
        )

    def copy_without_job(self, job: Job):
        return State(
            tuple((timeline.copy_without_job(job) for timeline in self.get_timelines()))
        )

    def copy_with_edited_timeline(self, timeline: Timeline, operator: int):
        return State(
            tuple(
                (
                    tl if i != operator else timeline
                    for i, tl in enumerate(self.get_timelines())
                )
            )
        )

    def get_next_states(self):
        jobs, delays = self.get_jobs_delays()
        # Choose a job to move with a probability based on the delay
        if sum(delay.total_seconds() for delay in delays) == 0:
            target_jb = choices(jobs)[0]
        else:
            target_jb = choices(jobs, [delay.total_seconds() for delay in delays])[0]

        # Remove the job from the state
        new_state = self.copy_without_job(target_jb)

        probabilities = [
            1.0
            / (
                tl.get_delay_sum().total_seconds()
                + tl.get_total_transit_time().total_seconds()
                + 1
            )
            for tl in new_state.get_timelines()
        ]

        # Choose a timeline to move the job to with a probability based on the total delay and total transit time
        target_tl = choices(new_state.get_timelines(), probabilities)[0]

        target_op: int = new_state.get_operator(target_tl)  # type:ignore

        # Try to insert the job in all possible positions in the timeline
        changes = target_tl.get_next_states(target_jb)

        # Create a new state for each possible change
        states: tuple[State, ...] = ()
        for change in changes:
            states += (new_state.copy_with_edited_timeline(change, target_op),)

        return states

    def __lt__(self, other: State):
        return self.evaluate() < other.evaluate()

    def print(self):
        for op, tl in enumerate(self.get_timelines()):
            print(f"Operator: {str(op).ljust(2)}| Total Delay: {tl.get_delay_sum()}")
            tl.print()
        print(
            f"State with score: {self.evaluate()} | Total Delay: {self.get_delay_sum()}"
        )


class Explorer:
    threshold = (5, 5)

    def __init__(self, jobs: list[Job], operators: int) -> None:
        timelines: list[list[Job]] = [[]] * operators

        for idx, j in enumerate(sorted(jobs, key=lambda x: x.get_start())):
            timelines[idx % operators].append(j)

        timeline2operator = tuple(Timeline(tuple(js)) for js in timelines)

        self.fringe: PriorityQueue[tuple[tuple[float, float], State]] = PriorityQueue()

        first_state = State(timeline2operator)
        first_score = first_state.evaluate()
        self.fringe.put((first_score, first_state))
        self.best_state = first_state
        self.best_score = first_score

    def explore(self):
        counter = 0
        bad_iters = 0
        visited: set[State] = set()
        while self.fringe.qsize() > 0:
            score, state = self.fringe.get()

            if score < self.best_score:
                difference = self.best_score[0] - score[0]
                self.best_state = state
                self.best_score = score
                bad_iters = 0
                print(
                    "Iter.:",
                    str(counter).ljust(4),
                    "| Best Score:",
                    str(self.best_score).ljust(42),
                    "| Difference:",
                    difference,
                )

            if bad_iters > 10000:
                break

            for next_state in state.get_next_states():
                if next_state in visited:
                    continue
                visited.add(next_state)
                score = next_state.evaluate()
                self.fringe.put((score, next_state))

            counter += 1
            bad_iters += 1

        self.best_state.print()


l1 = Location(0, 0)
l2 = Location(1000, 1000)
l3 = Location(1500, 600)
l4 = Location(200, 2000)

jobs = [
    Job(1, timedelta(minutes=10), timedelta(minutes=30), l1),
    Job(2, timedelta(minutes=0), timedelta(minutes=110), l3),
    Job(3, timedelta(minutes=5), timedelta(minutes=45), l2),
    Job(4, timedelta(minutes=5), timedelta(minutes=54), l4),
    Job(5, timedelta(minutes=5), timedelta(minutes=77), l2),
    Job(6, timedelta(minutes=5), timedelta(minutes=54), l1),
    Job(7, timedelta(minutes=60), timedelta(minutes=90), l3),
    Job(8, timedelta(minutes=70), timedelta(minutes=90), l2),
    Job(9, timedelta(minutes=99), timedelta(minutes=122), l4),
    Job(10, timedelta(minutes=60), timedelta(minutes=75), l1),
    Job(11, timedelta(minutes=110), timedelta(minutes=130), l3),
]

operators = 5

Explorer(jobs, operators).explore()
