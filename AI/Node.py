from typing import Self, Optional
from Domain.State import State
from datetime import timedelta
import Instance
from random import choices

class Node:
    def __init__(self, state:State, move:tuple[int,int], parent:Optional[Self]) -> None:
        self.state = state
        self.move = move
        self.parent = parent
        self.score = self.state.evaluate()

    def __lt__(self, other:Self):
        return self.score < other.score
    
    def __hash__(self) -> int:
        return hash(self.state)


    def __eq__(self, value: object) -> bool:
        if not isinstance(value,Node):
            return False
        return self.state==value.state

    def get_moves_raw(self)->tuple[tuple[int,int],...]:
        if self.parent:
            return self.parent.get_moves_raw() + (self.move,)
        else:
            return ()

    def get_moves(self):
        job2tl:dict[int,int] = {}
        for j,tl in self.get_moves_raw():
            job2tl[j]=tl
        return ((j,tl) for j,tl in job2tl.items())
        

    def get_next_nodes(self, current_time: timedelta):
        candidates = self.state.coupled_jobs_timelines()
        weights = tuple(
            (d + t).total_seconds()
            for d, t in zip(
                self.state.calculate_all_delays_flattened(),
                self.state.calculate_all_travels_flattened(),
            )
        )

        candidates, weights = self.state.filter_started_jobs(
            current_time, candidates, weights
        )

        try:
            j, old_t = choices(
                candidates,
                weights,
            )[0]
        except ValueError:
            return ()

        candidates = range(Instance.OPERATORS)
        weights = tuple(
            (
                1
                / (
                    (
                        self.state.calculate_total_timeline_delay(i)
                        + self.state.calculate_total_timeline_travel(i)
                    ).total_seconds()
                    + 1
                )
                for i in range(Instance.OPERATORS)
            )
        )

        target_timeline = choices(
            candidates,
            weights,
        )[0]

        move = (j,target_timeline)

        return (Node(state,move,self) for state in self.state.get_copies_with_moved_job(old_t, target_timeline, j, current_time))
