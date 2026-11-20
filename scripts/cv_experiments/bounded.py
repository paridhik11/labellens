"""Resumable, process-isolated evaluation deadlines for native decoder stalls."""
from __future__ import annotations

import json
import math
import multiprocessing as mp
import os
import queue
import sys
import time
from collections import deque
from collections.abc import Callable
from pathlib import Path
from typing import Any


def _worker(slot: int, incoming: Any, outgoing: Any, predict: Callable[..., dict[str, Any]]) -> None:
    """Keep models warm between images and announce each call before entering native code."""
    while True:
        message = incoming.get()
        if message is None:
            return
        index, task = message
        outgoing.put(('started', slot, index, None))
        try:
            result = predict(task)
        except Exception as error:
            result = {'fields': {}, 'error': f'{type(error).__name__}: {error}'}
        outgoing.put(('result', slot, index, result))


def run_bounded(
    tasks: list[tuple[str, str, str]], *, workers: int, timeout: float,
    journal: Path, fingerprint: str, predict: Callable[..., dict[str, Any]],
) -> list[dict[str, Any]]:
    """Persist each prediction and restart only stalled workers; every timeout is a miss.

    The same fixed deadline applies to both systems. The journal prevents completed
    images being rescored following infrastructure interruption, including timeouts.
    It never contains reference annotations or makes any recognition decisions.
    """
    if not math.isfinite(timeout) or timeout <= 0 or workers < 1:
        raise ValueError('Positive timeout and worker count required')
    completed: dict[int, dict[str, Any]] = {}
    if journal.exists():
        rows = [json.loads(line) for line in journal.read_text().splitlines()]
        if rows[0] != {'fingerprint': fingerprint, 'tasks': len(tasks), 'timeout': timeout}:
            raise ValueError('Journal protocol differs')
        for row in rows[1:]:
            index = row['index']
            if index in completed or not 0 <= index < len(tasks):
                raise ValueError('Invalid journal index')
            completed[index] = row['result']
    else:
        with journal.open('x') as handle:
            handle.write(json.dumps({'fingerprint': fingerprint, 'tasks': len(tasks), 'timeout': timeout})+'\n')
    pending = deque(i for i in range(len(tasks)) if i not in completed)
    context = mp.get_context('spawn')
    outgoing = context.Queue()
    states: dict[int, dict[str, Any]] = {}

    def launch(slot: int) -> None:
        """Create one replaceable model process and assign its next immutable image."""
        incoming = context.Queue()
        process = context.Process(target=_worker, args=(slot, incoming, outgoing, predict))
        process.start()
        states[slot] = {'process': process, 'queue': incoming, 'index': None}
        dispatch(slot)

    def dispatch(slot: int) -> None:
        """Keep one outstanding image per worker so a deadline cannot discard other results."""
        state = states[slot]
        if not pending:
            state['index'] = None
            return
        index = pending.popleft()
        state.update(index=index, started=time.monotonic(), active=False)
        state['queue'].put((index, tasks[index]))

    def stop(slot: int) -> None:
        """Terminate a native stall without relying on Python signal handlers."""
        state = states[slot]
        process = state['process']
        if process.is_alive():
            process.terminate()
        process.join(1)
        if process.is_alive():
            process.kill()
            process.join(1)
        state['queue'].cancel_join_thread()
        state['queue'].close()

    with journal.open('a') as handle:
        def store(index: int, result: dict[str, Any]) -> None:
            """Flush observations immediately, before another image starts or any scoring happens."""
            completed[index] = result
            handle.write(json.dumps({'index': index, 'result': result})+'\n')
            handle.flush()
            os.fsync(handle.fileno())
            if len(completed) % 10 == 0 or len(completed) == len(tasks):
                print(f'Prediction progress: {len(completed)}/{len(tasks)} unique images', file=sys.stderr, flush=True)

        try:
            for slot in range(min(workers, len(pending))):
                launch(slot)
            while len(completed) < len(tasks):
                try:
                    kind, slot, index, result = outgoing.get(timeout=0.02)
                    state = states[slot]
                    if state['index'] == index:
                        if kind == 'started':
                            state.update(started=time.monotonic(), active=True)
                        else:
                            store(index, result)
                            dispatch(slot)
                except queue.Empty:
                    pass
                for slot, state in list(states.items()):
                    index = state['index']
                    if index is None:
                        continue
                    elapsed = time.monotonic()-state['started']
                    limit = timeout if state['active'] else 60.0
                    if elapsed > limit or not state['process'].is_alive():
                        error = (f'EvaluationTimeout: {timeout}s; counted as miss' if elapsed > limit
                                 else f'EvaluationWorkerExit: {state["process"].exitcode}; counted as miss')
                        stop(slot)
                        store(index, {'fields': {}, 'error': error})
                        if pending:
                            launch(slot)
                        else:
                            state['index'] = None
        finally:
            for slot in states:
                stop(slot)
            outgoing.cancel_join_thread()
            outgoing.close()
    return [completed[i] for i in range(len(tasks))]
