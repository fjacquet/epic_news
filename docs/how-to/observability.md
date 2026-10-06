# Observability

Epic News records a trace event for every `ReceptionFlow` step and for the steps of the
company news crew. Crew timing and token usage go to the logs (`logs/`).

## Trace events

`src/epic_news/utils/observability.py` provides three things:

- `TraceEvent`: one event (type, source, details, timestamp).
- `Tracer`: appends events to `traces/<trace_id>.json`, one JSON object per line.
- `trace_task(tracer)`: a decorator that records `task_start`, then `task_end` (and
  `task_error` when the step raises) around a function. It works for plain and
  `async def` steps; an async step is recorded when it finishes.

The flow builds one tracer per process and decorates every step:

```python
from epic_news.utils.observability import Tracer, trace_task

tracer = Tracer(f"reception_flow_{int(time.time())}")


class ReceptionFlow(Flow[ContentState]):
    @listen("go_generate_poem")
    @trace_task(tracer)
    def generate_poem(self):
        ...
```

`task_start` carries only `task_name`; `task_end` carries `task_name`, `duration`, `success` and `result_type` (`None` when the
step failed); `task_error` carries `task_name` and `error`.

## Trace file format

A trace file holds one JSON object per line, one line per event:

```json
{"event_id": "6596c8be…", "event_type": "task_start", "source": "task:generate_saint_daily", "details": {"task_name": "generate_saint_daily"}, "timestamp": 1791220005.1}
{"event_id": "…", "event_type": "task_end", "source": "task:generate_saint_daily", "details": {"task_name": "generate_saint_daily", "duration": 142.3, "success": true, "result_type": "NoneType"}, "timestamp": 1791220147.4}
```

Read a trace back with `Tracer.load_trace(trace_id)` and filter it with
`tracer.get_events(event_type=..., source=...)`.

## Crew run usage

`kickoff_flow` / `akickoff_flow` (`utils/flow_enforcement.py`) log the wall-clock time and
CrewAI token usage of every crew run (`📊 Crew ... took ...`). For whole-run LiteLLM totals
(every call, including structured-output calls CrewAI does not count), use
`scripts/bench_flow.py`.

## Related Documentation

- [Architecture](../explanations/architecture.md)
- [Tools Reference](../reference/tools.md)
