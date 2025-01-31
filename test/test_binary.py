# Copyright 2009-2010 10gen, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the Binary wrapper."""

import unittest
import sys
sys.path[0:0] = [""]

from bson.binary import Binary


class TestBinary(unittest.TestCase):

    def setUp(self):
        pass

    def test_binary(self):
        a_string = b"hello world"
        a_binary = Binary(b"hello world")
        self.assert_(a_binary.startswith(b"hello"))
        self.assert_(a_binary.endswith(b"world"))
        self.assert_(isinstance(a_binary, Binary))
        self.assertFalse(isinstance(a_string, Binary))

    def test_exceptions(self):
        self.assertRaises(TypeError, Binary, None)
        self.assertRaises(TypeError, Binary, "hello")
        self.assertRaises(TypeError, Binary, 5)
        self.assertRaises(TypeError, Binary, 10.2)
        self.assertRaises(TypeError, Binary, b"hello", None)
        self.assertRaises(TypeError, Binary, b"hello", "100")
        self.assertRaises(ValueError, Binary, b"hello", -1)
        self.assertRaises(ValueError, Binary, b"hello", 256)
        self.assert_(Binary(b"hello", 0))
        self.assert_(Binary(b"hello", 255))

    def test_subtype(self):
        a = Binary(b"hello")
        self.assertEqual(a.subtype, 0)
        b = Binary(b"hello", 2)
        self.assertEqual(b.subtype, 2)
        c = Binary(b"hello", 100)
        self.assertEqual(c.subtype, 100)

    def test_equality(self):
        b = Binary(b"hello")
        c = Binary(b"hello", 100)
        self.assertNotEqual(b, c)
        self.assertEqual(c, Binary(b"hello", 100))
        self.assertEqual(b, Binary(b"hello"))
        self.assertNotEqual(b, Binary(b"hello "))
        self.assertNotEqual(b"hello", Binary(b"hello"))

    def test_repr(self):
        a = Binary(b"hello world")
        self.assertEqual(repr(a), "Binary(b'hello world', 0)")
        b = Binary(b"hello world", 2)
        self.assertEqual(repr(b), "Binary(b'hello world', 2)")
        c = Binary(b"\x08\xFF")
        self.assertEqual(repr(c), "Binary(b'\\x08\\xff', 0)")
        d = Binary(b"\x08\xFF", 2)
        self.assertEqual(repr(d), "Binary(b'\\x08\\xff', 2)")
        e = Binary(b"test", 100)
        self.assertEqual(repr(e), "Binary(b'test', 100)")

if __name__ == "__main__":
    unittest.main()
