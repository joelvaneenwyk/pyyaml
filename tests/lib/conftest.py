"""
Setup environment for 'pytest' to work.
"""
# cspell:ignore metafunc,maxunicode

import inspect
import os
import sys
import types
import traceback

from pytest import fixture, Metafunc

try:
    from typing import List, Optional, Tuple
except ImportError:
    pass

_TEST_DIR = os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))  # type: ignore[arg-type]
_LIB_DIR = os.path.abspath(os.path.normpath(os.path.join(_TEST_DIR, os.pardir, os.pardir, 'lib')))

sys.path.insert(0, _LIB_DIR)
sys.path.insert(0, _TEST_DIR)

import yaml.common  # pylint: disable=wrong-import-position


_DATA_DIR = os.path.abspath(os.path.normpath(os.path.join(_TEST_DIR, os.pardir, 'data')))
_HAS_UCS4_SUPPORT = sys.maxunicode > 0xffff


class Permutation(object):
    """Represents single permutation for a given function."""

    def __init__(self, function, value):
        self.function = function
        self.value = value
        self.name = os.path.basename(value)
        self.base, self.extension = os.path.splitext(self.name)


class TestFunctionData(object):
    """
    Cache of data for test functions.
    """

    instance = None  # type: Optional[TestFunctionData]

    def __init__(self, pytest_mode):
        # type: (bool) -> None

        self.args = sys.argv[1:]
        self.pytest_mode = pytest_mode or 'pytest' in self.args
        self.collections = []  # type: List[str]

        import test_yaml  # pylint: disable=import-outside-toplevel
        self.collections.append(test_yaml)
        if yaml.__with_libyaml__:
            import test_yaml_ext  # pylint: disable=import-outside-toplevel
            self.collections.append(test_yaml_ext)

        self.collections.append(globals())

        args = sys.argv[1:]

        self.verbose = False
        if '-v' in args:
            self.verbose = True
            args.remove('-v')
        if '--verbose' in args:
            self.verbose = True
            args.remove('--verbose')
        if 'YAML_TEST_VERBOSE' in os.environ:
            self.verbose = True

        self.include_functions = []
        self.include_filenames = []

        if args and not self.pytest_mode:
            if args:
                self.include_functions.append(args.pop(0))
            if 'YAML_TEST_FUNCTIONS' in os.environ:
                self.include_functions.extend(os.environ['YAML_TEST_FUNCTIONS'].split())

            self.include_filenames.extend(args)
            if 'YAML_TEST_FILENAMES' in os.environ:
                self.include_filenames.extend(os.environ['YAML_TEST_FILENAMES'].split())

        self.results = []
        self._function_mapping = {}
        self._extensions_to_filename = {}

        self.test_functions = self._find_test_functions(self.collections)
        self.test_filenames = self._find_test_filenames(_DATA_DIR)

    @staticmethod
    def _get_function_name(function):
        if sys.version_info[0] >= 3:
            name = function.__name__
        elif hasattr(function, 'unittest_name'):
            name = function.unittest_name
        else:
            name = function.func_name
        return name

    def parameterize(self, metafunc):
        # type: (Metafunc) -> None
        """Parameterize the test function."""

        arg_names = [
            x for x in set(metafunc.fixturenames)
            if x not in {'request', 'data', 'verbose'}
        ]
        function_name = metafunc.definition.name
        name = function_name
        filenames = []
        function = getattr(metafunc.definition, '_obj', None)

        if name not in self.test_functions:
            self.test_functions[name] = function

        if not function or (self.include_functions and name not in self.include_functions):
            return

        is_unit_test = getattr(function, 'unittest', None) or []
        if name not in self._function_mapping:
            for base, exts in self.test_filenames:
                if self.include_filenames and base not in self.include_filenames:
                    continue
                for ext in is_unit_test:
                    if ext not in exts:
                        break
                    filenames.append(os.path.join(_DATA_DIR, base+ext))
                else:
                    skip_exts = getattr(function, 'skip', [])
                    for skip_ext in skip_exts:
                        if skip_ext in exts:
                            break
                    else:
                        self._function_mapping[name] = filenames

        permutations = [
            Permutation(function_name, x)
            for x in self._function_mapping.get(function_name, None) or []
        ]
        groups = {}
        extensions = set()

        for permutation in permutations:
            if permutation.base not in groups:
                groups[permutation.base] = {}

            groups[permutation.base][permutation.extension] = permutation
            extensions.add(permutation.extension)

        if groups:
            extension_to_arg = {}
            arg_to_extension = {}

            unmatched_args = list(arg_names)
            for _iteration_index in range(2):
                if len(extension_to_arg) == len(arg_names):
                    break

                for ext in extensions:
                    if ext in extension_to_arg:
                        continue

                    match = '{}_filename'.format(ext.strip('.'))
                    for arg_name in unmatched_args:
                        if match == arg_name or len(unmatched_args) == 1:
                            unmatched_args.remove(arg_name)
                            arg_to_extension[arg_name] = ext
                            extension_to_arg[ext] = arg_name
                            break

            arg_value_tuples = []  # type: Tuple[str, ...]
            arg_ids = []  # type: List[str]

            for _group_name, group_permutations in yaml.common.iteritems(groups):
                group_values = []
                for arg_name in arg_names:
                    permutation = group_permutations.get(arg_to_extension[arg_name], None)
                    if permutation is not None:
                        group_values.append(permutation.value)

                if len(group_values) == len(arg_names):
                    if len(group_values) == 1:
                        arg_value_tuples.append(group_values[0])
                    else:
                        arg_value_tuples.append(tuple(group_values))
                    arg_ids.append(_group_name)

            metafunc.parametrize(
                ",".join(arg_names), arg_value_tuples, scope="function", ids=arg_ids)

    def _find_test_functions(self, collections):
        if not isinstance(collections, list):
            collections = [collections]
        functions = {}
        for collection in collections:
            if not isinstance(collection, dict):
                collection = vars(collection)
            for key in sorted(yaml.common.iterkeys(collection)):
                value = collection[key]
                if isinstance(value, types.FunctionType) and hasattr(value, 'unittest'):
                    functions[TestFunctionData._get_function_name(value)] = value
        return functions

    def _find_test_filenames(self, directory):
        filenames = {}
        for filename in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, filename)):
                base, ext = os.path.splitext(filename)
                if sys.version_info[0] >= 3 and base.endswith('-py2'):
                    continue
                if sys.version_info[0] >= 2 and base.endswith('-py3'):
                    continue
                if not _HAS_UCS4_SUPPORT and base.find('-ucs4-') > -1:
                    continue
                filenames.setdefault(base, []).append(ext)
                self._extensions_to_filename.setdefault(ext, []).append(filename)
        return sorted(yaml.common.iteritems(filenames))

    def execute(self, function, filenames, verbose):
        name = TestFunctionData._get_function_name(function)
        if verbose:
            sys.stdout.write('='*75+'\n')
            sys.stdout.write('%s(%s)...\n' % (name, ', '.join(filenames)))
        try:
            function(verbose=verbose, *filenames)
        except Exception as exc:
            info = sys.exc_info()
            if isinstance(exc, AssertionError):
                kind = 'FAILURE'
            else:
                kind = 'ERROR'
            if verbose:
                traceback.print_exc(limit=1, file=sys.stdout)
            else:
                sys.stdout.write(kind[0])
                sys.stdout.flush()
            raise
        else:
            kind = 'SUCCESS'
            info = None
            if not verbose:
                sys.stdout.write('.')
        sys.stdout.flush()
        return (name, filenames, kind, info)

    @staticmethod
    def get_instance():
        if TestFunctionData.instance is None:
            TestFunctionData.instance = TestFunctionData(pytest_mode=True)
        return TestFunctionData.instance


def pytest_generate_tests(metafunc):
    # type: (Metafunc) -> None
    """Parameterize given function against all permutations."""
    TestFunctionData.get_instance().parameterize(metafunc)


@fixture(scope="function", name="verbose")
def fixture_verbose():
    """Returns the data filename associated with this test."""
    return TestFunctionData.get_instance().verbose
