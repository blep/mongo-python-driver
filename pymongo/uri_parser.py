# Copyright 2009-2011 10gen, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you
# may not use this file except in compliance with the License.  You
# may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.


"""Tools to parse and validate a MongoDB URI."""

import urllib.request, urllib.parse, urllib.error

from pymongo.common import VALIDATORS, UNSUPPORTED
from pymongo.errors import (ConfigurationError,
                            InvalidURI,
                            UnsupportedOption)

SCHEME = 'mongodb://'
SCHEME_LEN = len(SCHEME)
DEFAULT_PORT = 27017


def _partition(entity, sep):
    """Python2.4 doesn't have a partition method so we provide
    our own that mimics str.partition from later releases.

    Split the string at the first occurrence of sep, and return a
    3-tuple containing the part before the separator, the separator
    itself, and the part after the separator. If the separator is not
    found, return a 3-tuple containing the string itself, followed
    by two empty strings.
    """
    parts = entity.split(sep, 1)
    if len(parts) == 2:
        return parts[0], sep, parts[1]
    else:
        return entity, '', ''


def _rpartition(entity, sep):
    """Python2.4 doesn't have an rpartition method so we provide
    our own that mimics str.rpartition from later releases.

    Split the string at the last occurrence of sep, and return a
    3-tuple containing the part before the separator, the separator
    itself, and the part after the separator. If the separator is not
    found, return a 3-tuple containing two empty strings, followed
    by the string itself.
    """
    idx = entity.rfind(sep)
    if idx == -1:
        return '', '', entity
    return entity[:idx], sep, entity[idx + 1:]


def parse_userinfo(userinfo):
    """Validates the format of user information in a MongoDB URI.
    Reserved characters like ':', '/' and '@' must be escaped
    following RFC 2396.

    Returns a 2-tuple containing the unescaped username followed
    by the unescaped password.

    :Paramaters:
        - `userinfo`: A string of the form <username>:<password>
    """
    if '@' in userinfo or userinfo.count(':') > 1:
        raise InvalidURI("':' or '@' characters in a username or password "
                         "must be escaped according to RFC 2396.")
    user, _, passwd = _partition(userinfo, ":")
    if not user or not passwd:
        raise InvalidURI("An empty string is not a "
                         "valid username or password.")
    user = urllib.parse.unquote(user)
    passwd = urllib.parse.unquote(passwd)

    return user, passwd


def parse_ipv6_literal_host(entity, default_port):
    """Validates an IPv6 literal host:port string.

    Returns a 2-tuple of IPv6 literal followed by port where
    port is default_port if it wasn't specified in entity.

    :Parameters:
        - `entity`: A string that represents an IPv6 literal enclosed
                    in braces (e.g. '[::1]' or '[::1]:27017').
        - `default_port`: The port number to use when one wasn't
                          specified in entity.
    """
    if entity.find(']') == -1:
        raise ConfigurationError("an IPv6 address literal must be "
                                 "enclosed in '[' and ']' according "
                                 "to RFC 2732.")
    i = entity.find(']:')
    if i == -1:
        return entity[1:-1], default_port
    return entity[1: i], entity[i + 2:]


def parse_host(entity, default_port=DEFAULT_PORT):
    """Validates a host string

    Returns a 2-tuple of host followed by port where port is default_port
    if it wasn't specified in the string.

    :Parameters:
        - `entity`: A host or host:port string where host could be a
                    hostname or IP address.
        - `default_port`: The port number to use when one wasn't
                          specified in entity.
    """
    host = entity
    port = default_port
    if entity[0] == '[':
        host, port = parse_ipv6_literal_host(entity, default_port)
    elif entity.find(':') != -1:
        if entity.count(':') > 1:
            raise ConfigurationError("Reserved characters such as ':' must be "
                                     "escaped according RFC 2396. An IPv6 "
                                     "address literal must be enclosed in '[' "
                                     "and ']' according to RFC 2732.")
        host, port = host.split(':', 1)
    if isinstance(port, str):
        if not port.isdigit():
            raise ConfigurationError("Port number must be an integer.")
        port = int(port)
    return host, port

def validate_options(opts):
    """Validates and normalizes options passed in a MongoDB URI.

    Returns a new dictionary of validated and normalized options.

    :Parameters:
        - `opts`: A dict of MongoDB URI options.
    """
    normalized = {}
    for key, value in opts.items():
        opt = key.lower()
        validate = VALIDATORS.get(opt)
        if not validate:
            if opt in UNSUPPORTED:
                raise UnsupportedOption("%s is not currently "
                                        "supported by pymongo." % (key,))
            raise ConfigurationError("%s is not a "
                                     "recognized MongoDB URI option." % (key,))
        normalized[opt] = validate(key, value)
    return normalized


def split_options(opts):
    """Takes the options portion of a MongoDB URI, validates each option
    and returns the options in a dictionary. The option names will be returned
    lowercase even if camelCase options are used.

    :Parameters:
        - `opt`: A string representing MongoDB URI options.
    """
    and_idx = opts.find("&")
    semi_idx = opts.find(";")
    try:
        if and_idx >= 0 and semi_idx >= 0:
            raise InvalidURI("Can not mix '&' and ';' for option separators.")
        elif and_idx >= 0:
            options = dict([kv.split("=") for kv in opts.split("&")])
        elif semi_idx >= 0:
            options = dict([kv.split("=") for kv in opts.split(";")])
        elif opts.find("=") != -1:
            options = dict([opts.split("=")])
        else:
            raise ValueError
    except ValueError:
        raise InvalidURI("MongoDB URI options are key=value pairs.")

    return validate_options(options)


def split_hosts(hosts, default_port=DEFAULT_PORT):
    """Takes a string of the form host1[:port],host2[:port]... and
    splits it into (host, port) tuples. If [:port] isn't present the
    default_port is used.

    Returns a set of 2-tuples containing the host name (or IP) followed by
    port number.

    :Parameters:
        - `hosts`: A string of the form host1[:port],host2[:port],...
        - `default_port`: The port number to use when one wasn't specified
                          for a host.
    """
    nodes = []
    for entity in hosts.split(','):
        if not entity:
            raise ConfigurationError("Empty host "
                                     "(or extra comma in host list).")
        nodes.append(parse_host(entity, default_port))
    return nodes


def parse_uri(uri, default_port=DEFAULT_PORT):
    """Parse and validate a MongoDB URI.

    Returns a dict of the form::

        {
            'nodelist': <list of (host, port) tuples>,
            'username': <username> or None,
            'password': <password> or None,
            'database': <database name> or None,
            'collection': <collection name> or None,
            'options': <dict of MongoDB URI options>
        }

    :Parameters:
        - `uri`: The MongoDB URI to parse.
        - `default_port`: The port number to use when one wasn't specified
                          for a host in the URI.
    """
    if not uri.startswith(SCHEME):
        raise InvalidURI("Invalid URI scheme: URI "
                         "must begin with '%s'" % (SCHEME,))

    scheme_free = uri[SCHEME_LEN:]

    if not scheme_free:
        raise InvalidURI("Must provide at least one hostname or IP.")

    nodes = None
    user = None
    passwd = None
    dbase = None
    collection = None
    options = {}

    host_part, _, path_part = _partition(scheme_free, '/')
    if not path_part and '?' in host_part:
        raise InvalidURI("A '/' is required between "
                         "the host list and any options.")

    if '@' in host_part:
        userinfo, _, hosts = _rpartition(host_part, '@')
        user, passwd = parse_userinfo(userinfo)
    else:
        hosts = host_part

    nodes = split_hosts(hosts, default_port=default_port)

    if path_part:

        if path_part[0] == '?':
            opts = path_part[1:]
        else:
            dbase, _, opts = _partition(path_part, '?')
            if '.' in dbase:
                dbase, collection = dbase.split('.', 1)

        if opts:
            options = split_options(opts)

    return {
        'nodelist': nodes,
        'username': user,
        'password': passwd,
        'database': dbase,
        'collection': collection,
        'options': options
    }


if __name__ == '__main__':
    import pprint
    import sys
    try:
        pprint.pprint(parse_uri(sys.argv[1]))
    except (InvalidURI, UnsupportedOption) as e:
        print(e)
    sys.exit(0)
