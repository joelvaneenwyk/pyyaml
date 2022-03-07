# PyYAML

A full-featured YAML processing framework for Python.

This is a modified version of [PyYAML](https://github.com/yaml/pyyaml) locked to v5.4.1.1 that combines Python 2 and Python 3 versions together. Whenever possible, the [six](https://github.com/benjaminp/six) package is used to avoid branching but this is not possible in some cases. This does mean, however, that it is expected that performance of this version is going to not be as performant as the standard `PyYAML`.

## Installation

To install, type `python setup.py install`.

By default, the `setup.py` script checks whether LibYAML is installed and if
so, builds and installs LibYAML bindings.
To skip the check and force installation of LibYAML bindings, use the option
`--with-libyaml`: `python setup.py --with-libyaml install`.
To disable the check and skip building and installing LibYAML bindings, use
`--without-libyaml`: `python setup.py --without-libyaml install`.

When LibYAML bindings are installed, you may use fast LibYAML-based parser and
emitter as follows:

    >>> yaml.load(stream, Loader=yaml.CLoader)
    >>> yaml.dump(data, Dumper=yaml.CDumper)

If you don't trust the input YAML stream, you should use:

    >>> yaml.safe_load(stream)

## Testing

PyYAML includes a comprehensive test suite.

To run the tests, type `python setup.py test`.

## Further Information

* For more information, check the
  [PyYAML homepage](https://github.com/yaml/pyyaml).

* [PyYAML tutorial and reference](http://pyyaml.org/wiki/PyYAMLDocumentation).

* Discuss PyYAML with the maintainers on
  Matrix at [matrix.to/pyyaml](https://matrix.to/#/#pyyaml:yaml.io) or
  IRC #pyyaml irc.libera.chat

* Submit bug reports and feature requests to the
  [PyYAML bug tracker](https://github.com/yaml/pyyaml/issues).

## License

The PyYAML module was written by Kirill Simonov <xi@resolvent.net>.
It is currently maintained by the YAML and Python communities.

PyYAML is released under the MIT license.

See the file LICENSE for more details.
