from queue import PriorityQueue
from Domain.State import State
from datetime import timedelta
from AI.Node import Node
import Instance

class Explorer:
    threshold = (5, 5)

    def __init__(self):
        timelines: list[tuple[int, ...]] = [()] * Instance.OPERATORS
        for i in range(len(Instance.JOBS)):
            timelines[i % Instance.OPERATORS] += (i,)

        self.state = State(tuple(timelines))
        self.moves = ()

    def explore(self, current_time: timedelta):
        fringe: PriorityQueue[Node] = PriorityQueue()

        best_node = Node(self.state,(0,0),None)

        fringe.put(best_node)

        counter = 0
        bad_iterations = 0
        visited: set[Node] = set()
        visited.add(best_node)

        print("="*30)
        print("Starting exploration from node with score:",best_node.score)

        while fringe.qsize() > 0:
            node = fringe.get()
            visited.remove(node)

            if node < best_node:
                best_node = node
                print("-"*30)
                print(f"New best score at iteration {counter}: {node.score}")

            if bad_iterations > 10000:
                break

            for new_node in node.get_next_nodes(current_time):
                if new_node not in visited:
                    visited.add(new_node)
                    fringe.put(new_node)

            counter += 1
            bad_iterations += 1

        self.state=best_node.state
        self.moves=list(best_node.get_moves())

    def show_state(self):
        self.state.show()

    def show_moves(self):
        for j,tl in self.moves:
            print(f"Job {j} was moved to Operator {tl}")