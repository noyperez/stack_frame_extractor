import os
import unittest

from stack_frame_extractor import extract_stack_frames, StackFrame


def _outermost_helper():
    # Add a known extra frame so tests can assert on relative depth without
    # depending on the interpreter's own startup frames, which vary by
    # platform and invocation.
    return _innermost_helper()


def _innermost_helper():
    return extract_stack_frames()


class ExtractStackFramesTests(unittest.TestCase):
    def test_returns_list_of_stackframe(self):
        frames = extract_stack_frames()
        self.assertIsInstance(frames, list)
        self.assertTrue(all(isinstance(f, StackFrame) for f in frames))

    def test_first_frame_is_caller(self):
        # When called directly from this test method, the first frame should
        # describe this very method.
        frames = extract_stack_frames()
        self.assertGreater(len(frames), 0)
        first = frames[0]
        self.assertEqual(first.function_name, "test_first_frame_is_caller")
        self.assertEqual(first.file_path, __file__)
        self.assertGreater(first.line_number, 0)

    def test_stack_order_is_caller_to_outermost(self):
        frames = _outermost_helper()
        # _outermost_helper called _innermost_helper, which called
        # extract_stack_frames. With the default start_frame=1 the extractor
        # itself is skipped, so the first recorded frame is
        # _innermost_helper.
        self.assertEqual(frames[0].function_name, "_innermost_helper")
        self.assertEqual(frames[1].function_name, "_outermost_helper")
        # The test method should appear further out.
        names = [f.function_name for f in frames]
        self.assertIn("test_stack_order_is_caller_to_outermost", names)
        self.assertLess(names.index("_innermost_helper"),
                        names.index("_outermost_helper"))

    def test_start_frame_zero_includes_extractor(self):
        frames = extract_stack_frames(start_frame=0)
        self.assertGreater(len(frames), 0)
        self.assertEqual(frames[0].function_name, "extract_stack_frames")

    def test_start_frame_two_skips_caller(self):
        frames = extract_stack_frames(start_frame=2)
        self.assertGreater(len(frames), 0)
        # Skipping the extractor and this test method means the first frame
        # is something further out, never this method.
        self.assertNotEqual(frames[0].function_name,
                            "test_start_frame_two_skips_caller")

    def test_negative_start_frame_raises(self):
        with self.assertRaises(ValueError):
            extract_stack_frames(start_frame=-1)

    def test_line_number_is_int(self):
        frames = extract_stack_frames()
        self.assertGreater(len(frames), 0)
        self.assertIsInstance(frames[0].line_number, int)

    def test_file_path_is_string(self):
        frames = extract_stack_frames()
        self.assertGreater(len(frames), 0)
        self.assertIsInstance(frames[0].file_path, str)

    def test_function_name_is_string(self):
        frames = extract_stack_frames()
        self.assertGreater(len(frames), 0)
        self.assertIsInstance(frames[0].function_name, str)

    def test_namedtuple_field_access(self):
        frames = extract_stack_frames()
        first = frames[0]
        # Confirm the namedtuple exposes the documented field names by
        # attribute access, not just by index.
        self.assertTrue(hasattr(first, "function_name"))
        self.assertTrue(hasattr(first, "file_path"))
        self.assertTrue(hasattr(first, "line_number"))

    def test_frames_share_real_file_path(self):
        frames = extract_stack_frames()
        first = frames[0]
        # The caller's file path should resolve to this test file on disk.
        self.assertTrue(os.path.samefile(first.file_path, __file__) or
                        first.file_path == __file__)

    def test_empty_stack_when_start_frame_exceeds_depth(self):
        # Requesting more frames than exist yields an empty list rather than
        # an error, matching slicing semantics on the underlying stack.
        frames = extract_stack_frames(start_frame=10000)
        self.assertEqual(frames, [])


if __name__ == "__main__":
    unittest.main()
