# golem-tasks - run tasks on the Golem Network

## Start

### Prerequisites

1.  A running requestor [`yagna`](https://handbook.golem.network/requestor-tutorials/flash-tutorial-of-requestor-development).
2.  Access to a [PostgreSQL](https://www.postgresql.org/download/) database.

    `Golem-tasks` interface requires specifying a `dsn` for the database you want to work in.
    Example `dsn`: `dbname=golem user=golem password=1234 host=localhost port=5432`
    
    To test if you have a correct `dsn` run `psql -d $DSN -c "SELECT 1"`.
    You can also use [environment variables](https://www.postgresql.org/docs/current/libpq-envars.html) instead, eg. `$PGPASSWORD`.

3.  [Poetry](https://python-poetry.org/docs/)
4.  This was developed & tested on `Ubuntu 20.04` and `python3.8.10`, but I don't know any reason why other environments should not work.

### Installation

```
#   Copy the code
git clone https://github.com/golemfactory/golem-tasks-python.git
cd golem-tasks-python

#   Install. Virtual environment is recommended.
poetry install

#   Initialize the database. This will create a "tasks" schema and few tables in it.
python3 -m golem_tasks install --dsn $DSN
```

### Check if everything works
```
python3 -m golem_tasks run examples.hello_world --workers 3
```

If this keeps running, everything should be fine. Stop with Ctrl + C.
Run commands from the [Monitoring](#Monitoring) section to check the execution details.


## Execution

### `run` command

```
python3 -m tasks run my_module [--dsn, --run-id, --workers, --max-price, --budget]
```

* `--dsn` - Database location, e.g. `dbname=golem user=golem password=1234 host=localhost port=5432`
* `--run-id` - String, identifier of a run. 

  Defaults to a random string. Executions with different `run_id` are totally separate.
  Subsequent `run` with the same `run-id` will try to recover as much as possible from the previous execution
  (i.e. reuse activities and agreements).

* `--workers` - Integer, expected number of activities working at the same time. Defaults to 1.
* `--max-price` - Float, maximal cost per a single result, optional.

   E.g. `--max-price=0.001` means "we don't want to work on activities where average price per result is greater than `0.001`".
   More details in the [Cost management](#Cost-management) section.
  
* `--budget` - String, how much we are willing to pay at most. Currently the only accepted format is hourly budget, e.g. `3/h`. Defaults to `1/h`.

### Monitoring

```
#   Print a single-row summary table
python3 -m golem_tasks summary [--dsn, --run-id]

#   Print a summary table with rows corresponding to activities
python3 -m golem_tasks show [--dsn, --run-id]
```

In both commands the default `--run-id` is the most recent new `run_id`.

These two commands can be combined into a single non-stop monitoring tool:
```
while true; do sleep 1; DATA=$(python3 -m golem_tasks show); SUMMARY=$(python3 -m golem_tasks summary); clear -x; echo "$DATA"; echo "$SUMMARY"; done
```

## Build a new app

The easiest way to build your own application is to copy `examples/hello_world.py` and modify it while preserving the same interface.

For an example of a more complex app, check `examples/yacat.py`. NOTE: to run this you must also install `aiofiles`.

## Additional details

### Restarting

```
#   Start
python3 -m tasks my_module run --workers 10 --run-id my_run

#   After a while kill the process in a non-graceful way (e.g. kill -9)
#   and start again
python3 -m tasks my_module run --workers 10 --run-id my_run
```
Second run will try to:

* reuse running activities, if it decides they are reusable
* reuse all agreements for non-reusable activities (i.e. will create new activities for the same agreements)

This will not work after Ctrl+C stop, because Ctrl+C terminates all agreements.
This should be useful if starting activity is expensive, or if we have a very restrictive provider selection so we really care about
preserving the "good" agreements.

### Budget

Whenever we receive a debit note, total amount for already accepted debit notes in the last hour is calculated.
We have a defined budget in a form `X/h`. If `calculated_amount + new_debit_note_amount > X`, program stops.

We create a new allocation for X each hour. This doesn't really matter now, but once
https://github.com/golemfactory/yagna/issues/2391 is done these two parts of logic will be cleanly merged into one 
(i.e. we won't be calculating any total budget, just trying to accept the invoice and stopping when this fails).

### Cost management

`--max-price=X` means that after some initial period (300s now) on every debit note we'll evaluate average cost of a single
result calculated by the activity and stop it if the cost exceedes X.

Note that now all debit notes/invoices are accepted, so our final price might be nowhere near the `--max-price` 
(e.g. we might get an invoice for 10 GLM after a second and we'll accept it if we have high enough budget).

### FAQ

**Q**: How do I change the payment network? or the subnet?  
**A**: Use `YAGNA_PAYMENT_NETWORK` and `YAGNA_SUBNET` variables. E.g. 
```
YAGNA_PAYMENT_NETWORK=mainnet YAGNA_SUBNET=public-beta python3 -m golem_tasks run examples.hello_world
```

**Q**: I see some traceback on the screen. Why? Is my program still working?  
**A**: Currently many not-really-important tracebacks are printed to the screen for debugging purposes.
If the script didn't exit, it should still be working correctly.

**Q**: Is there any API for `golem_tasks`, in case I didn't want to use CLI?  
**A**: Instead of executing the `run` command you can do:

```
runner = Runner(
    #   Arguments defined in a source file (e.g. in examples/hello_world.py)
    payload=payload,
    get_tasks=get_tasks,
    results_cnt=results_cnt,

    #   Arguments passed from the command line
    dsn=dsn,
    run_id=run_id,
    workers=workers,
    result_max_price=result_max_price,
    budget_str=budget_str,
)
await runner.main()
```

Check `golem_tasks/run.py` for more details.

## Current state

This is a MVP. There are real-life usecases where `golem-tasks` is really good, but many things are still missing.

There is already [task API in `yapapi`](https://yapapi.readthedocs.io/en/stable/api.html#yapapi.Golem.execute_tasks).
Main new features in `golem-tasks`:

*   Convenient tool for execution monitoring
*   Recovery in case of aburpt stop
*   Cost management
*   Hourly budget
*   All relevant execution-related data is saved to a Postgresql database
*   Built on top of [`golem-core`](https://github.com/golemfactory/golem-core-python)

Known missing features:

*   Parts of the interface mentioned in "missing features" section in https://github.com/golemfactory/golem-tasks-python/issues/2
*   Mid-agreement payments
