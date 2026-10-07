# Stack Frame Extractor

Captures the current call stack and returns a list of `(function_name, file_path, line_number)` tuples for attaching error context to log records or exception reports.

## Usage

```python
from stack_frame_extractor import extract_stack_frames

frames = extract_stack_frames()
for frame in frames:
    print(frame.function_name, frame.file_path, frame.line_number)
```

`extract_stack_frames(start_frame=1)` returns a list of `StackFrame` namedtuples with fields `function_name`, `file_path`, and `line_number`. The default `start_frame=1` skips the extractor itself, so the first element describes the caller. Pass `0` to include the extractor, or a higher integer to skip additional frames.

## Why this exists

Error handlers and structured loggers frequently want a compact, serialisable description of where an error was observed, without pulling in the full `traceback` machinery or a third-party logging framework. The standard library's `traceback.extract_stack` returns `FrameSummary` objects, but those carry extra fields and a repr aimed at formatting rather than at structured attachment. This library narrows the output to exactly the three fields most error-context pipelines want, as plain namedtuples.

The trade-off: the extractor's own frames are included in the output by default only when `start_frame=0`. With the default `start_frame=1`, the extractor is skipped but any helper the caller wraps around it is not. Keeping the trimming explicit and single-axis avoids the ambiguity of trying to guess which frames are "internal".

## Edge cases

Frames whose code object is `None` (which can appear for certain C-level callers) are skipped rather than emitted with placeholder values, so the returned list may be shorter than the raw stack depth. Requesting a `start_frame` larger than the stack depth returns an empty list, matching Python's slice semantics. Negative `start_frame` raises `ValueError`.
