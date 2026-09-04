"""Small concurrency boundary for independent event sources.

The goal is failure isolation, not a background job system: independent source
imports may run together so one slow source does not serially delay all others.
Each source adapter remains responsible for its own HTTP timeout.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable, Iterable

from source_health import safe_import_error


@dataclass(frozen=True)
class SourceTask:
    key: str
    failure_name: str
    fetch: Callable[[], tuple[list, list[tuple]]]


@dataclass(frozen=True)
class SourceTaskResult:
    key: str
    events: list
    health: list[tuple]


def run_source_tasks(tasks: Iterable[SourceTask], max_workers: int = 6) -> list[SourceTaskResult]:
    """Run independent imports concurrently and return results in task order.

    A failed source is converted into its own health row. Other completed
    sources are retained. This intentionally does not add retries: automatic
    retries can amplify load and make a degraded upstream slower.
    """
    task_list = list(tasks)
    if not task_list:
        return []
    workers = max(1, min(int(max_workers), len(task_list)))
    completed = {}
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="upplevio-source") as pool:
        future_to_task = {pool.submit(task.fetch): task for task in task_list}
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            try:
                events, health = future.result()
                completed[task.key] = SourceTaskResult(task.key, list(events), list(health))
            except Exception as exc:
                completed[task.key] = SourceTaskResult(
                    task.key, [], [(task.failure_name, "Fel", 0, safe_import_error(exc))]
                )
    return [completed[task.key] for task in task_list]
