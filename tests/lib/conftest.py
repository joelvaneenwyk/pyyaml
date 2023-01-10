"""
Setup environment for 'pytest' to work.
"""
# pyright: strict
# pyright: reportTypeCommentUsage=false
# cspell:ignore metafunc,maxunicode

import inspect
import os
import sys
import types
import traceback

from pytest import fixture, Metafunc

try:
    from typing import List, Optional, Tuple, Any, Dict, Set, Generator
except ImportError:
    pass

_TEST_DIR = os.path.abspath(str(os.path.dirname(str(inspect.getfile(inspect.currentframe())))))  # type: str
_LIB_DIR = os.path.abspath(os.path.normpath(os.path.join(_TEST_DIR, os.pardir, os.pardir, 'lib')))

sys.path.insert(0, _LIB_DIR)
sys.path.insert(0, _TEST_DIR)

import yaml.common  # pylint: disable=wrong-import-position


_DATA_DIR = os.path.abspath(os.path.normpath(os.path.join(_TEST_DIR, os.pardir, 'data')))
_HAS_UCS4_SUPPORT = sys.maxunicode > 0xffff


class DataFile(object):
    """Represents a single data file."""

    def __init__(self, filename):
        # type: (str) -> None
        self.filename = filename
        self.name = os.path.basename(filename)
        self.base, self.extension = os.path.splitext(self.name)


class Permutation(object):
    """Represents single permutation for a given function."""

    def __init__(self, function, value):
        # type: (Any, str) -> None
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
        self.collections = []  # type: List[Any]

        import test_yaml  # pylint: disable=import-outside-toplevel
        self.collections.append(test_yaml)
        if yaml.__with_libyaml__:  # type: ignore
            import test_yaml_ext  # pylint: disable=import-outside-toplevel
            self.collections.append(test_yaml_ext)
        self.collections.append(globals())

        args = sys.argv[1:]  # type: List[str]

        self.verbose = False
        if '-v' in args:
            self.verbose = True
            args.remove('-v')
        if '--verbose' in args:
            self.verbose = True
            args.remove('--verbose')
        if 'YAML_TEST_VERBOSE' in os.environ:
            self.verbose = True

        self.include_functions = []  # type: List[str]
        self.include_filenames = []  # type: List[str]

        if args and not self.pytest_mode:
            if args:
                self.include_functions.append(args.pop(0))
            if 'YAML_TEST_FUNCTIONS' in os.environ:
                self.include_functions.extend(os.environ['YAML_TEST_FUNCTIONS'].split())

            self.include_filenames.extend(args)
            if 'YAML_TEST_FILENAMES' in os.environ:
                self.include_filenames.extend(os.environ['YAML_TEST_FILENAMES'].split())

        self.results = []  # type: List[str]
        self._function_mapping = {}  # type: Dict[str, Any]
        self._extensions_to_filename = {}  # type: Dict[str, List[DataFile]]

        self.test_filenames = []  # type: List[DataFile]
        self.functions = {}

        for collection in self.collections:
            if isinstance(collection, dict):
                mapping = collection  # type: Dict[str, Any]
            else:
                mapping = vars(collection)
            for key in sorted(yaml.common.iterkeys(mapping)):
                self._add_function(mapping[key])

        for filename in self._find_test_filenames(_DATA_DIR):
            file_data = DataFile(filename)
            self.test_filenames.append(file_data)
            self._extensions_to_filename.setdefault(file_data.extension, []).append(file_data)

    @staticmethod
    def _get_function_name(function):
        # type: (Any) -> Optional[str]
        if hasattr(function, 'unittest_name'):
            name = function.unittest_name
        elif sys.version_info[0] >= 3:
            name = getattr(function, '__name__', None)
        elif hasattr(function, 'func_name'):
            name = function.func_name
        else:
            name = None
        return name

    def parameterize(self, metafunc):
        # type: (Metafunc) -> None
        """Parameterize the test function."""

        arg_names = [
            x for x in set(metafunc.fixturenames)
            if x not in {'request', 'data', 'verbose'}
        ]
        function_name = metafunc.definition.name
        function = self._add_function(metafunc)

        if not function or (self.include_functions and function_name not in self.include_functions):
            return

        filenames = []  # type: List[str]
        exts = getattr(function, 'unittest', None) or []
        if function_name not in self._function_mapping:
            for data_file in self.test_filenames:
                if self.include_filenames and data_file.base not in self.include_filenames:
                    continue

                skip_exts = getattr(function, 'skip', None) or []
                for ext in exts:
                    if ext in exts and ext == data_file.extension and ext not in skip_exts:
                        filenames.append(data_file.filename)

            self._function_mapping[function_name] = filenames

        permutations = [
            Permutation(function_name, x)
            for x in filenames or []
        ]
        groups = {}  # type: Dict[str, Dict[str, Permutation]]
        extensions = set()  # type: Set[str]

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

            arg_value_tuples = []  # type: List[Tuple[str, ...]]
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

    def _add_function(self, function):
        # type: (Any) -> Optional[Any]
        if isinstance(function, Metafunc):
            function_value = getattr(function.definition, '_obj', None)  # type: Optional[Any]
        else:
            function_value = function
        function_name = TestFunctionData._get_function_name(function_value)
        if function_name not in self.functions and (isinstance(function_value, types.FunctionType) or hasattr(function_value, 'unittest')):
            self.functions[function_name] = function_value
        return self.functions.get(function_name, None) if function_name is not None else None

    def _find_test_filenames(self, directory):
        # type: (str) -> Generator[str, None, None]
        for filename in os.listdir(directory):
            path = os.path.join(directory, filename)
            if os.path.isfile(path):
                base, _extension = os.path.splitext(filename)
                if sys.version_info[0] >= 3 and base.endswith('-py2'):
                    continue
                if sys.version_info[0] >= 2 and base.endswith('-py3'):
                    continue
                if not _HAS_UCS4_SUPPORT and base.find('-ucs4-') > -1:
                    continue
                yield path

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
