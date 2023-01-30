from itertools import count

from golem_core import Payload, commands

#   INTERFACE
#   3 things included here (PAYLOAD, get_tasks, results_cnt) are necessary parts
#   of a module that can be executed with golem-tasks.

#   This is the same thing as returned by e.g. 'yapapi.vm.repo`
PAYLOAD = Payload.from_image_hash("9a3b5d67b0b27746283cb5f287c13eab1beaa12d92a9f536b747c7ae")

#   Iterator yielding callables that receive golem_core.low.Activity as the only argument.
#   Execution ends when the iterator is exhausted (in this case - never).
def get_tasks(run_id):
    for i in count(0):
        task_callable = _get_task(i)
        yield task_callable

#   Function returning number of already calculated results. Caveats:
#   *   This should be optional (TODO -> https://github.com/golemfactory/golem-tasks-python/issues/2),
#       but now is required
#   *   Necessary only for cost management
#   *   Returned number must never decrease for a single run_id.
#       (--> following implementation will not work after a restart, because we'll be back to 0).
async def results_cnt(run_id):
    return len(results)


#   INTERNALS
#   This part can be implemented however you want.
results = {}
def _get_task(task_data):
    async def execute_task(activity):
        batch = await activity.execute_commands(
            commands.Run("sleep 1"),
            commands.Run(f"echo -n $(({task_data} * 7))"),
        )
        await batch.wait(5)

        result = batch.events[-1].stdout
        assert result is not None

        results[task_data] = result

        print(f"{task_data} -> {result}")

    return execute_task
