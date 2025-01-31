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

"""Tools for creating and manipulating SON, the Serialized Ocument Notation.

Regular dictionaries can be used instead of SON objects, but not when the order
of keys is important. A SON object can be used just like a normal Python
dictionary."""

import copy


class SON(dict):
    """SON data.

    A subclass of dict that maintains ordering of keys and provides a
    few extra niceties for dealing with SON. SON objects can be
    converted to and from BSON.

    The mapping from Python types to BSON types is as follows:

    ===================================  =============  ===================
    Python Type                          BSON Type      Supported Direction
    ===================================  =============  ===================
    None                                 null           both
    bool                                 boolean        both
    int [#int]_                          int32 / int64  py -> bson
    long                                 int64          both
    float                                number (real)  both
    string                               string         py -> bson
    unicode                              string         both
    list                                 array          both
    dict / `SON`                         object         both
    datetime.datetime [#dt]_ [#dt2]_     date           both
    compiled re                          regex          both
    `bson.binary.Binary`                 binary         both
    `bson.objectid.ObjectId`             oid            both
    `bson.dbref.DBRef`                   dbref          both
    None                                 undefined      bson -> py
    unicode                              code           bson -> py
    `bson.code.Code`                     code           py -> bson
    unicode                              symbol         bson -> py
    ===================================  =============  ===================

    Note that to save binary data it must be wrapped as an instance of
    `bson.binary.Binary`. Otherwise it will be saved as a BSON string
    and retrieved as unicode.

    .. [#int] A Python int will be saved as a BSON int32 or BSON int64 depending
       on its size. A BSON int32 will always decode to a Python int. A BSON int64
       will always decode to a Python long.
    .. [#dt] datetime.datetime instances will be rounded to the nearest
       millisecond when saved
    .. [#dt2] all datetime.datetime instances are treated as *naive*. clients
       should always use UTC.
    """

    def __init__(self, data=None, **kwargs):
        self.__keys = []
        dict.__init__(self)
        self.update(data)
        self.update(kwargs)

    def __repr__(self):
        result = []
        for key in self.__keys:
            result.append("(%r, %r)" % (key, self[key]))
        return "SON([%s])" % ", ".join(result)

    def __setitem__(self, key, value):
        if key not in self.__keys:
            self.__keys.append(key)
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        self.__keys.remove(key)
        dict.__delitem__(self, key)

    def keys(self):
        for k in self.__keys:
            yield k

    def copy(self):
        return SON(self)

    def __iter__(self):
        return self.keys()

    def __contains__(self, key):
        return key in self.__keys

    def items(self):
        for k in self.__keys:
            yield (k, self[k])

    def values(self):
        for k in self.__keys:
            yield self[k]

    def clear(self):
        dict.clear(self)
        self.__keys = list()

    def setdefault(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            self[key] = default
        return default

    def pop(self, key, *args):
        if len(args) > 1:
            raise TypeError("pop expected at most 2 arguments, got "\
                                + repr(1 + len(args)))
        try:
            value = self[key]
        except KeyError:
            if args:
                return args[0]
            raise
        del self[key]
        return value

    def popitem(self):
        try:
            k, v = self.items().next()
        except StopIteration:
            raise KeyError('container is empty')
        del self[k]
        return (k, v)

    def update(self, other=None, **kwargs):
        # Make progressively weaker assumptions about "other"
        if other is None:
            pass
        elif hasattr(other, 'items'):
            for k, v in other.items():
                self[k] = v
        elif hasattr(other, 'keys'):
            for k in other.keys():
                self[k] = other[k]
        else:
            for k, v in other:
                self[k] = v
        if kwargs:
            self.update(kwargs)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __len__(self):
        return len(self.__keys)

    def to_dict(self):
        """Convert a SON document to a normal Python dictionary instance.

        This is trickier than just *dict(...)* because it needs to be
        recursive.
        """

        def transform_value(value):
            if isinstance(value, list):
                return [transform_value(v) for v in value]
            if isinstance(value, SON):
                value = dict(value)
            if isinstance(value, dict):
                for k, v in value.items():
                    value[k] = transform_value(v)
            return value

        return transform_value(dict(self))

    def __deepcopy__(self, memo):
        out = SON()
        for k, v in self.items():
            out[k] = copy.deepcopy(v, memo)
        return out
