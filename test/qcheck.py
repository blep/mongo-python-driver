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

import random
import traceback
import datetime
import re
import sys
from functools import reduce
sys.path[0:0] = [""]

from bson.binary import Binary
from bson.dbref import DBRef
from bson.objectid import ObjectId
from bson.son import SON

gen_target = 100
reduction_attempts = 10
examples = 5


def lift(value):
    return lambda: value


def choose_lifted(generator_list):
    return lambda: random.choice(generator_list)


def map(generator, function):
    return lambda: function(generator())


def choose(list):
    return lambda: random.choice(list)()


def gen_range(start, stop):
    return lambda: random.randint(start, stop)


def gen_int():
    max_int = 2147483647
    return lambda: random.randint(-max_int - 1, max_int)


def gen_float():
    return lambda: (random.random() - 0.5) * sys.maxsize


def gen_boolean():
    return lambda: random.choice([True, False])


def gen_printable_char():
    return lambda: chr(random.randint(32, 126))


def gen_printable_string(gen_length):
    return lambda: "".join(gen_list(gen_printable_char(), gen_length)())


def gen_char(set=None):
    return lambda: chr(random.randint(0, 255))


def gen_byte(set=None):
    return lambda: bytes([random.randint(0, 255)])


def gen_string(gen_length):
    return lambda: "".join(gen_list(gen_char(), gen_length)())


def gen_bytes(gen_length):
    return lambda: b"".join(gen_list(gen_byte(), gen_length)())


def gen_unichar():
    return lambda: chr(random.randint(1, 0xFFF))


def gen_unicode(gen_length):
    return lambda: "".join([x for x in
                             gen_list(gen_unichar(), gen_length)() if
                             x not in ".$"])


def gen_list(generator, gen_length):
    return lambda: [generator() for _ in range(gen_length())]


def gen_datetime():
    return lambda: datetime.datetime(random.randint(1970, 2037),
                                     random.randint(1, 12),
                                     random.randint(1, 28),
                                     random.randint(0, 23),
                                     random.randint(0, 59),
                                     random.randint(0, 59),
                                     random.randint(0, 999) * 1000)


def gen_dict(gen_key, gen_value, gen_length):

    def a_dict(gen_key, gen_value, length):
        result = {}
        for _ in range(length):
            result[gen_key()] = gen_value()
        return result
    return lambda: a_dict(gen_key, gen_value, gen_length())


def gen_regexp(gen_length):
    # TODO our patterns only consist of one letter.
    # this is because of a bug in CPython's regex equality testing,
    # which I haven't quite tracked down, so I'm just ignoring it...
    pattern = lambda: "".join(gen_list(choose_lifted("a"), gen_length)())

    def gen_flags():
        flags = 0
        if random.random() > 0.5:
            flags = flags | re.IGNORECASE
        if random.random() > 0.5:
            flags = flags | re.MULTILINE
        if random.random() > 0.5:
            flags = flags | re.VERBOSE

        return flags
    return lambda: re.compile(pattern(), gen_flags())


def gen_objectid():
    return lambda: ObjectId()


def gen_dbref():
    collection = gen_unicode(gen_range(0, 20))
    return lambda: DBRef(collection(), gen_mongo_value(1, True)())


def gen_mongo_value(depth, ref):
    choices = [gen_unicode(gen_range(0, 50)),
               gen_printable_string(gen_range(0, 50)),
               gen_bytes(gen_range(0, 1000)),
               gen_int(),
               gen_float(),
               gen_boolean(),
               gen_datetime(),
               gen_objectid(),
               lift(None)]
    if ref:
        choices.append(gen_dbref())
    if depth > 0:
        choices.append(gen_mongo_list(depth, ref))
        choices.append(gen_mongo_dict(depth, ref))
    return choose(choices)


def gen_mongo_list(depth, ref):
    return gen_list(gen_mongo_value(depth - 1, ref), gen_range(0, 10))


def gen_mongo_dict(depth, ref=True):
    return map(gen_dict(gen_unicode(gen_range(0, 20)),
                        gen_mongo_value(depth - 1, ref),
                        gen_range(0, 10)), SON)


def simplify(case):  # TODO this is a hack
    if isinstance(case, SON) and "$ref" not in case:
        simplified = SON(case)  # make a copy!
        if random.choice([True, False]):
            # delete
            if not len(list(simplified.keys())):
                return (False, case)
            del simplified[random.choice(list(simplified.keys()))]
            return (True, simplified)
        else:
            # simplify a value
            if not len(list(simplified.items())):
                return (False, case)
            (key, value) = random.choice(list(simplified.items()))
            (success, value) = simplify(value)
            simplified[key] = value
            return (success, success and simplified or case)
    if isinstance(case, list):
        simplified = list(case)
        if random.choice([True, False]):
            # delete
            if not len(simplified):
                return (False, case)
            simplified.pop(random.randrange(len(simplified)))
            return (True, simplified)
        else:
            # simplify an item
            if not len(simplified):
                return (False, case)
            index = random.randrange(len(simplified))
            (success, value) = simplify(simplified[index])
            simplified[index] = value
            return (success, success and simplified or case)
    return (False, case)


def reduce(case, predicate, reductions=0):
    for _ in range(reduction_attempts):
        (reduced, simplified) = simplify(case)
        if reduced and not predicate(simplified):
            return reduce(simplified, predicate, reductions + 1)
    return (reductions, case)


def isnt(predicate):
    return lambda x: not predicate(x)


def check(predicate, generator):
    counter_examples = []
    for _ in range(gen_target):
        case = generator()
        try:
            if not predicate(case):
                reduction = reduce(case, predicate)
                counter_examples.append("after %s reductions: %r" % reduction)
        except:
            counter_examples.append("%r : %s" % (case, traceback.format_exc()))
    return counter_examples


def check_unittest(test, predicate, generator):
    counter_examples = check(predicate, generator)
    if counter_examples:
        failures = len(counter_examples)
        message = "\n".join(["    -> %s" % f for f in
                             counter_examples[:examples]])
        message = ("found %d counter examples, displaying first %d:\n%s" %
                   (failures, min(failures, examples), message))
        test.fail(message)
