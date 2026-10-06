"""Core implementation for extracting call-stack frames.

The module exposes a single function, :func:`extract_stack_frames`, that walks
the current call stack and returns a lightweight, serialisable description of
each frame. The description is a :class:`StackFrame` namedtuple containing the
function name, source file path, and line number.

Design notes
------------
* We use :mod:`inspect` rather than :func:`sys._getframe` because ``inspect``
  is the documented, stable public API and behaves consistently across CPython
  implementations. ``sys._getframe`` is a CPython implementation detail.
* We deliberately stop at the outermost frame rather than trying to trim the
  extractor's own frames from the top of the stack. Callers almost always want
  the full stack so they can see where the error context was captured. The
  extractor's own frames are included; if a caller wants to drop them they can
  slice the returned list. Keeping the extractor's frames in the output makes
  the function pure and deterministic: the same call site always yields the
  same number of frames regardless of how deep the extractor itself is.
* We skip frames whose code object is missing (``frame.f_code is None``). This
  can happen for frames created by some C-level callers; including them would
  force callers to handle ``None`` fields, which defeats the purpose of a
  simple error-context helper.
"""

from __future__ import annotations

import inspect
from collections import namedtuple
from typing import List

__all__ = ["extract_stack_frames", "StackFrame"]

StackFrame = namedtuple("StackFrame", ["function_name", "file_path", "line_number"])
"""A single frame on the call stack.

Attributes
----------
function_name : str
    The qualified name of the function executing in the frame, as reported by
    ``inspect.FrameInfo.function``. For methods this includes the class via
    ``qualname`` semantics where the runtime provides them.
file_path : str
    The filesystem path of the source file for the frame, or the empty string
    when the frame has no associated code object.
line_number : int
    The 1-based line number currently executing, or ``0`` when the frame has no
    associated code object.
"""


def extract_stack_frames(start_frame: int = 1) -> List[StackFrame]:
    """Return the current call stack as a list of :class:`StackFrame` tuples.

    Parameters
    ----------
    start_frame : int, optional
        The number of frames to skip from the top of the stack before
        collecting. ``1`` (the default) skips this function itself, so the
        first element describes the caller. ``0`` includes this function as
        the first element. Negative values raise :class:`ValueError`.

    Returns
    -------
    list of StackFrame
        One entry per frame, ordered from the caller outward to the outermost
        frame (typically the interpreter startup). Frames whose code object is
        ``None`` are skipped rather than emitted with placeholder values, so
        the returned list may be shorter than the raw stack depth.

    Raises
    ------
    ValueError
        If ``start_frame`` is negative.
    """
    if start_frame < 0:
        raise ValueError("start_frame must be non-negative")

    frames: List[StackFrame] = []
    # ``inspect.stack`` performs its own walk and returns FrameInfo records
    # ordered from the current frame outward. We slice off the requested
    # number of leading frames to give callers control over where the
    # captured context begins.
    for record in inspect.stack()[start_frame:]:
        frame = record.frame
        code = frame.f_code
        if code is None:
            # A frame with no code object carries no useful source-location
            # information. Skip it rather than emitting empty fields, so the
            # returned list only contains frames a caller can actually reason
            # about.
            continue
        frames.append(
            StackFrame(
                function_name=record.function,
                file_path=code.co_filename,
                line_number=frame.f_lineno,
            )
        )
    return frames
