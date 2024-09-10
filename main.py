from AI.Explorer import Explorer
from datetime import timedelta
import Instance

explorer = Explorer()
explorer.explore(timedelta(minutes=0))
explorer.show_state()
print("=" * 30)
input("Press enter to add 25 minute delay to job 3 ")
jobs = Instance.JOBS
jobs[3].end+= timedelta(minutes=25)
Instance.JOBS = tuple(jobs)
explorer.explore(timedelta(minutes=25))
explorer.show_state()
print("-" * 30)
explorer.show_moves()
print("-" * 30)
