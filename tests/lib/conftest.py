"""
Setup environment for 'pytest' to work.
"""
# cspell:ignore metafunc,maxunicode

import inspect
import os
import sys
import types
import traceback
import pprint

import pytest
from pytest import fixture, FixtureRequest, Metafunc

try:
    from typing import List, Optional
except ImportError:
    pass

_TEST_DIR = os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))  # type: ignore[arg-type]
_LIB_DIR = os.path.abspath(os.path.normpath(os.path.join(_TEST_DIR, os.pardir, os.pardir, 'lib')))

sys.path.insert(0, _LIB_DIR)
sys.path.insert(0, _TEST_DIR)

import yaml.common


_DATA_DIR = os.path.abspath(os.path.normpath(os.path.join(_TEST_DIR, os.pardir, 'data')))
_HAS_UCS4_SUPPORT = sys.maxunicode > 0xffff


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

        import test_yaml
        self.collections.append(test_yaml)
        if yaml.__with_libyaml__:
            import test_yaml_ext
            self.collections.append(test_yaml_ext)

        self.collections.append(globals())
        self.test_functions = self._find_test_functions(self.collections)
        self.test_filenames = self._find_test_filenames(_DATA_DIR)

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

        for function in self.test_functions:
            if yaml.common.PY3:
                name = function.__name__
            else:
                name = function.func_name

            filenames = []

            if self.include_functions and name not in self.include_functions:
                continue
            if function.unittest:
                for base, exts in self.test_filenames:
                    if self.include_filenames and base not in self.include_filenames:
                        continue
                    for ext in function.unittest:
                        if ext not in exts:
                            break
                        filenames.append(os.path.join(_DATA_DIR, base+ext))
                    else:
                        skip_exts = getattr(function, 'skip', [])
                        for skip_ext in skip_exts:
                            if skip_ext in exts:
                                break

            self._function_mapping[name] = filenames

    def _find_test_functions(self, collections):
        if not isinstance(collections, list):
            collections = [collections]
        functions = []
        for collection in collections:
            if not isinstance(collection, dict):
                collection = vars(collection)
            for key in sorted(yaml.common.iterkeys(collection)):
                value = collection[key]
                if isinstance(value, types.FunctionType) and hasattr(value, 'unittest'):
                    functions.append(value)
        return functions

    def _find_test_filenames(self, directory):
        filenames = {}
        for filename in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, filename)):
                base, ext = os.path.splitext(filename)
                if yaml.common.PY3 and base.endswith('-py2'):
                    continue
                if yaml.common.PY2 and base.endswith('-py3'):
                    continue
                if not _HAS_UCS4_SUPPORT and base.find('-ucs4-') > -1:
                    continue
                filenames.setdefault(base, []).append(ext)
        return sorted(yaml.common.iteritems(filenames))

    def execute(self, function, filenames, verbose):
        if yaml.common.PY3:
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

    def display(self, results, verbose):
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
                traceback.print_exception(file=sys.stdout, *info)
            else:
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
                sys.stdout.write(data)
                if data and data[-1] != '\n':
                    sys.stdout.write('\n')
        sys.stdout.write('='*75+'\n')
        sys.stdout.write('TESTS: %s\n' % total)
        if failures:
            sys.stdout.write('FAILURES: %s\n' % failures)
        if errors:
            sys.stdout.write('ERRORS: %s\n' % errors)
        return not (failures or errors)

    def get_files(self, function, fixture_name):
        """Return filename for this test."""
        filenames = self._function_mapping.get(function, None)
        if filenames is not None:
            parts = ['.{}'.format(name) for name in set(fixture_name.split('_'))]
            output_filenames = []
            for part in parts:
                output_filenames.extend([filename for filename in filenames if filename.endswith(part)])
            if output_filenames:
                filenames = output_filenames
        return filenames

    def get_file(self, function, fixture_name):
        """Return filename for this test."""
        files = self.get_files(function, fixture_name)
        result = files[0] if files else None
        if result is None:
            pytest.skip('No test data found for %s' % function)
        return result

    @staticmethod
    def get_instance():
        if TestFunctionData.instance is None:
            TestFunctionData.instance = TestFunctionData(pytest_mode=True)
        return TestFunctionData.instance


def pytest_generate_tests(metafunc):
    # type: (Metafunc) -> None
    for fixture_name in set(metafunc.fixturenames):
        filenames = TestFunctionData.get_instance().get_files(metafunc.definition.name, fixture_name)
        if fixture_name not in {'request', 'data'} and filenames:
            metafunc.parametrize(fixture_name, filenames)


@fixture(scope="function", name="verbose")
def fixture_verbose():
    """Returns the data filename associated with this test."""
    return TestFunctionData.get_instance().verbose


# @fixture(scope="function", name="canonical_filename")
# def fixture_canonical_filename(request):
#     # type: (FixtureRequest) -> str
#     """Returns the data filename associated with this test."""
#     return TestFunctionData.get_instance().get_file(request.node.name, request.fixturename)
#
#
# @fixture(scope="function", name="code_filename")
# def fixture_code_filename(request):
#     # type: (FixtureRequest) -> str
#     """Returns the data filename associated with this test."""
#     return TestFunctionData.get_instance().get_file(request.node.name, request.fixturename)
#
#
# @fixture(scope="function", name="data_filename")
# def fixture_data_filename(request):
#     # type: (FixtureRequest) -> str
#     """Returns the data filename associated with this test."""
#     return TestFunctionData.get_instance().get_file(request.node.name, request.fixturename)
#
#
# @fixture(scope="function", name="detect_filename")
# def fixture_detect_filename(request):
#     # type: (FixtureRequest) -> str
#     """Returns the data filename associated with this test."""
#     return TestFunctionData.get_instance().get_file(request.node.name, request.fixturename)
#
#
# @fixture(scope="function", name="error_filename")
# def fixture_error_filename(request):
#     # type: (FixtureRequest) -> str
#     """Returns the data filename associated with this test."""
#     return TestFunctionData.get_instance().get_file(request.node.name, request.fixturename)
#
#
# @fixture(scope="function", name="events_filename")
# def fixture_events_filename(request):
#     # type: (FixtureRequest) -> str
#     """Returns the data filename associated with this test."""
#     return TestFunctionData.get_instance().get_file(request.node.name, request.fixturename)
#
#
# @fixture(scope="function", name="input_filename")
# def fixture_input_filename(request):
#     # type: (FixtureRequest) -> str
#     """Returns the data filename associated with this test."""
#     return TestFunctionData.get_instance().get_file(request.node.name, request.fixturename)
#
#
# @fixture(scope="function", name="marks_filename")
# def fixture_marks_filename(request):
#     # type: (FixtureRequest) -> str
#     """Returns the data filename associated with this test."""
#     return TestFunctionData.get_instance().get_file(request.node.name, request.fixturename)
#
#
# @fixture(scope="function", name="path_filename")
# def fixture_path_filename(request):
#     # type: (FixtureRequest) -> str
#     """Returns the data filename associated with this test."""
#     return TestFunctionData.get_instance().get_file(request.node.name, request.fixturename)
#
#
# @fixture(scope="function", name="recursive_filename")
# def fixture_recursive_filename(request):
#     # type: (FixtureRequest) -> str
#     """Returns the data filename associated with this test."""
#     return TestFunctionData.get_instance().get_file(request.node.name, request.fixturename)
#
#
# @fixture(scope="function", name="sorted_filename")
# def fixture_sorted_filename(request):
#     # type: (FixtureRequest) -> str
#     """Returns the data filename associated with this test."""
#     return TestFunctionData.get_instance().get_file(request.node.name, request.fixturename)
#
#
# @fixture(scope="function", name="structure_filename")
# def fixture_structure_filename(request):
#     # type: (FixtureRequest) -> str
#     """Returns the data filename associated with this test."""
#     return TestFunctionData.get_instance().get_file(request.node.name, request.fixturename)
#
#
# @fixture(scope="function", name="tokens_filename")
# def fixture_tokens_filename(request):
#     # type: (FixtureRequest) -> str
#     """Returns the data filename associated with this test."""
#     return TestFunctionData.get_instance().get_file(request.node.name, request.fixturename)
#
#
# @fixture(scope="function", name="unicode_filename")
# def fixture_unicode_filename(request):
#     # type: (FixtureRequest) -> str
#     """Returns the data filename associated with this test."""
#     return TestFunctionData.get_instance().get_file(request.node.name, request.fixturename)
