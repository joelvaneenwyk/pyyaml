# pyright: strict
# pyright: reportTypeCommentUsage=false
# cspell:ignore metafunc,maxunicode

import difflib
import inspect
import os
import os.path
import pprint
import sys
import traceback
import types

try:
    from pytest import Metafunc  # type: ignore[import]
except ImportError:
    try:
        from _pytest.python import Metafunc  # type: ignore[import]
    except ImportError:
        class MetaFunc:
            pass

try:
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from typing import Any, Dict, Generator, List, Optional, Tuple, Union
except ImportError:
    pass

YAML_ROOT_DIR = os.path.abspath(os.path.join(
    str(os.path.dirname(inspect.getfile(inspect.currentframe()))),  # type: ignore[arg-type]
    os.pardir, os.pardir))
sys.path.insert(0, os.path.join(YAML_ROOT_DIR, 'lib'))
sys.path.insert(0, os.path.join(YAML_ROOT_DIR, 'tests', 'lib'))

import yaml.common

HAS_UCS4_SUPPORT = sys.maxunicode > 0xffff
DATA_DIR = os.path.join(YAML_ROOT_DIR, 'tests', 'data')


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


class InternalTestFunctions(object):
    """
    Cache of data for test functions.
    """

    instance = None  # type: Optional[InternalTestFunctions]

    def __init__(self, pytest_mode):
        # type: (bool) -> None

        self.args = sys.argv[1:]
        self.pytest_mode = pytest_mode or 'pytest' in self.args
        self.collections = []  # type: List[Any]

        import yaml_tests  # pylint: disable=import-outside-toplevel
        self.collections.append(yaml_tests)
        if yaml.__with_libyaml__:  # type: ignore
            import yaml_tests_ext  # pylint: disable=import-outside-toplevel
            self.collections.append(yaml_tests_ext)
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
        self.functions = {}  # type: Dict[str, Any]

        for collection in self.collections:
            if isinstance(collection, dict):
                mapping = collection  # type: Dict[str, Any]
            else:
                mapping = vars(collection)
            for key in sorted(yaml.common.iterkeys(mapping)):
                self._add_function(mapping[key])

        for filename in self._find_test_filenames(DATA_DIR):
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

        extension_to_arg = {}  # type: Dict[str, str]
        arg_to_extension = {}  # type: Dict[str, str]

        unit_test_extensions = getattr(function, 'unittest', None) or []  # type: List[str]
        skip_exts = getattr(function, 'skip', None) or []  # type: List[str]

        filenames = []  # type: List[str]
        if function_name not in self._function_mapping:
            for data_file in self.test_filenames:
                if self.include_filenames and data_file.base not in self.include_filenames:
                    continue

                for extension in unit_test_extensions:
                    if extension in unit_test_extensions and extension == data_file.extension and extension not in skip_exts:
                        filenames.append(data_file.filename)

            self._function_mapping[function_name] = filenames

        file_extensions = {os.path.splitext(x)[1].lower() for x in filenames}
        all_extensions = list(set(self._extensions_to_filename.keys()))
        unknown_extensions = set(unit_test_extensions).difference(set(unit_test_extensions + list(file_extensions)).intersection(all_extensions))
        if unknown_extensions:
            raise Exception('Unknown extensions: {}'.format(unknown_extensions))

        def _normalize(input):
            # type: (str) -> str
            return input.replace('-', '_').replace('_filename', '').strip('.').lower()

        extension_matches = file_extensions or unit_test_extensions or all_extensions
        possibilities = {
            _normalize(x): x
            for x in extension_matches
        }

        unmatched_args = list(arg_names)
        _iteration_index = 0
        while (len(extension_to_arg) != len(arg_names)
                    and unmatched_args
                    and _iteration_index < 10):
            arg_name = unmatched_args[_iteration_index % len(unmatched_args)]
            _iteration_index += 1

            matches = difflib.get_close_matches(
                _normalize(arg_name),
                list(possibilities.keys()),
                1, 0.6)
            if matches or len(unmatched_args) == 1:
                if matches:
                    extension = possibilities.pop(matches[0], '')
                else:
                    extension = list(possibilities.values())[0]
                arg_to_extension[arg_name] = extension
                extension_to_arg[extension] = arg_name
                unmatched_args.remove(arg_name)

        if unmatched_args:
            raise Exception("Invalid argument match.")
        permutations = [
            Permutation(function_name, x)
            for x in filenames or []
        ]
        groups = {}  # type: Dict[str, Dict[str, Permutation]]

        for permutation in permutations:
            if permutation.base not in groups:
                groups[permutation.base] = {}

            groups.setdefault(permutation.base, {})[permutation.extension] = permutation

        if groups:
            arg_value_tuples = []  # type: List[Union[str, Tuple[str, ...]]]
            arg_ids = []  # type: List[str]

            for group_name, group_permutations in yaml.common.iteritems(groups):
                group_values = []  # type: List[str]
                for arg_name in arg_names:
                    group_permutation = group_permutations.get(arg_to_extension[arg_name], None)
                    if group_permutation is not None:
                        group_values.append(group_permutation.value)

                if len(group_values) == len(arg_names):
                    if len(group_values) == 1:
                        arg_value_tuples.append(group_values[0])
                    else:
                        arg_value_tuples.append(tuple(group_values))
                    arg_ids.append(group_name)

            metafunc.parametrize(
                ",".join(arg_names), arg_value_tuples, scope="function", ids=arg_ids)

    def _add_function(self, function):
        # type: (Any) -> Optional[Any]
        if isinstance(function, Metafunc):
            function_value = getattr(function.definition, '_obj', None)  # type: Optional[Any]
        else:
            function_value = function
        function_name = InternalTestFunctions._get_function_name(function_value)
        if (function_name
                and function_name not in self.functions
                and (isinstance(function_value, types.FunctionType) or hasattr(function_value, 'unittest'))):
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
                if not HAS_UCS4_SUPPORT and base.find('-ucs4-') > -1:
                    continue
                yield path

    def execute(self, function, filenames, verbose):
        # type: (Any, List[str], bool) -> Tuple[Optional[str], List[str], str, Optional[Any]]
        """Execute test function and pass in filenames as arguments."""

        function_name = InternalTestFunctions._get_function_name(function)
        if verbose:
            sys.stdout.write('='*75+'\n')
            sys.stdout.write('%s(%s)...\n' % (function_name, ', '.join(filenames)))

        info = None  # type: Optional[Any]
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
        return function_name, filenames, kind, info

    @staticmethod
    def get_instance():
        """Return singleton instance of this class."""
        if InternalTestFunctions.instance is None:
            InternalTestFunctions.instance = InternalTestFunctions(pytest_mode=True)
        return InternalTestFunctions.instance


def find_test_functions(collections):
    # type: (Union[types.ModuleType, List[types.ModuleType]]) -> List[types.FunctionType]
    if not isinstance(collections, list):
        collections = [collections]
    functions = []  # type: List[types.FunctionType]
    for collection_value in collections:
        if isinstance(collection_value, dict):
            collection = collection_value
        else:
            collection = vars(collection_value)  # type: ignore
        for key in sorted(yaml.common.iterkeys(collection)):
            value = collection[key]  # type: Any
            if isinstance(value, types.FunctionType) and hasattr(value, 'unittest'):
                functions.append(value)
    return functions

def find_test_filenames(directory):
    # type: (str) -> List[Tuple[str, List[str]]]
    filenames = {}  # type: Dict[str, List[str]]
    for filename in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, filename)):
            base, ext = os.path.splitext(filename)
            if sys.version_info[0] >= 3 and base.endswith('-py2'):
                continue
            if sys.version_info[0] == 2 and base.endswith('-py3'):
                continue
            if not HAS_UCS4_SUPPORT and base.find('-ucs4-') > -1:
                continue
            filenames.setdefault(base, []).append(ext)
    return sorted(yaml.common.iteritems(filenames))

def parse_arguments(args):
    # type: (Optional[List[str]]) -> Tuple[List[str], List[str], bool]
    if args is None:
        args = sys.argv[1:]
    verbose = False
    if '-v' in args:
        verbose = True
        args.remove('-v')
    if '--verbose' in args:
        verbose = True
        args.remove('--verbose')
    if 'YAML_TEST_VERBOSE' in os.environ:
        verbose = True
    include_functions = []  # type: List[str]
    if args:
        include_functions.append(args.pop(0))
    if 'YAML_TEST_FUNCTIONS' in os.environ:
        include_functions.extend(os.environ['YAML_TEST_FUNCTIONS'].split())
    include_filenames = []  # type: List[str]
    include_filenames.extend(args)
    if 'YAML_TEST_FILENAMES' in os.environ:
        include_filenames.extend(os.environ['YAML_TEST_FILENAMES'].split())
    return include_functions, include_filenames, verbose

def execute(function, filenames, verbose):
    # type: (Any, List[str], bool) -> Tuple[Optional[str], List[str], str, Optional[Any]]
    if sys.version_info[0] >= 3:
        name = function.__name__
    elif hasattr(function, 'unittest_name'):
        name = function.unittest_name
    else:
        name = function.func_name
    if verbose:
        sys.stdout.write('='*75+'\n')
        sys.stdout.write('%s(%s)...\n' % (name, ', '.join(filenames)))
    try:
        function(verbose=verbose, *filenames)
    except Exception as exc:
        info = sys.exc_info()  # type: Optional[Any]
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

def display(results, verbose):
    # type: (List[Tuple[Optional[str], List[str], str, Optional[Any]]], bool) -> bool
    if results and not verbose:
        sys.stdout.write('\n')
    total = len(results)
    failures = 0
    errors = 0
    for name, filenames, kind, info in results:
        if kind == 'SUCCESS':
            continue
        if kind == 'FAILURE':
            failures += 1
        if kind == 'ERROR':
            errors += 1
        sys.stdout.write('='*75+'\n')
        sys.stdout.write('%s(%s): %s\n' % (name, ', '.join(filenames), kind))
        if kind == 'ERROR':
            traceback.print_exception(file=sys.stdout, *info)  # type: ignore
        elif info:
            sys.stdout.write('Traceback (most recent call last):\n')
            traceback.print_tb(info[2], file=sys.stdout)
            sys.stdout.write('%s: see below\n' % info[0].__name__)
            sys.stdout.write('~'*75+'\n')
            for arg in info[1].args:
                pprint.pprint(arg, stream=sys.stdout)

        for filename in filenames:
            sys.stdout.write('-'*75+'\n')
            sys.stdout.write('%s:\n' % filename)
            data = open(filename, 'rb').read()
            sys.stdout.write(yaml.common.ensure_str(data))
            if data and data[-1] != int('\n'):
                sys.stdout.write('\n')
    sys.stdout.write('='*75+'\n')
    sys.stdout.write('TESTS: %s\n' % total)
    if failures:
        sys.stdout.write('FAILURES: %s\n' % failures)
    if errors:
        sys.stdout.write('ERRORS: %s\n' % errors)
    return not bool(failures or errors)

def run(collections, args=None):
    # type: (Any, Optional[List[str]]) -> bool
    test_functions = find_test_functions(collections)
    test_filenames = find_test_filenames(DATA_DIR)
    include_functions, include_filenames, verbose = parse_arguments(args)
    results = []  # type: List[Tuple[Optional[str], List[str], str, Optional[Any]]]
    for function in test_functions:
        if sys.version_info[0] >= 3:
            name = function.__name__
        else:
            name = function.func_name

        if include_functions and name not in include_functions:
            continue

        attr_unittest = getattr(function, 'unittest', None)
        if isinstance(attr_unittest, list):
            function_unittest = attr_unittest  # type: List[str]
        else:
            function_unittest = []

        if function_unittest:
            for base, exts in test_filenames:
                if include_filenames and base not in include_filenames:
                    continue
                filenames = []  # type: List[str]
                for ext in function_unittest:
                    if ext not in exts:
                        break
                    filenames.append(os.path.join(DATA_DIR, base+ext))
                else:
                    skip_exts = getattr(function, 'skip', [])
                    for skip_ext in skip_exts:
                        if skip_ext in exts:
                            break
                    else:
                        result = execute(function, filenames, verbose)
                        results.append(result)
        else:
            result = execute(function, [], verbose)
            results.append(result)
    return display(results, verbose=verbose)
