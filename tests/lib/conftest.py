"""Setup environment for 'pytest' to work."""

import inspect
import os
import sys
import sys, os, os.path, types, traceback, pprint

from pytest import fixture

_TEST_DIR = os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))  # type: ignore[arg-type]
_LIB_DIR = os.path.abspath(os.path.normpath(os.path.join(_TEST_DIR, os.pardir, os.pardir, 'lib')))

sys.path.insert(0, _LIB_DIR)
sys.path.insert(0, _TEST_DIR)

import yaml.common


_DATA_DIR = os.path.abspath(os.path.normpath(os.path.join(_TEST_DIR, os.pardir, 'data')))

has_ucs4 = sys.maxunicode > 0xffff


class TestFunctionData(object):
    def __init__(self):
        self.filenames = self.find_test_filenames(_DATA_DIR)

    def find_test_functions(self, collections):
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

    def find_test_filenames(self, directory):
        filenames = {}
        for filename in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, filename)):
                base, ext = os.path.splitext(filename)
                if yaml.common.PY3 and base.endswith('-py2'):
                    continue
                if yaml.common.PY2 and base.endswith('-py3'):
                    continue
                if not has_ucs4 and base.find('-ucs4-') > -1:
                    continue
                filenames.setdefault(base, []).append(ext)
        return sorted(yaml.common.iteritems(filenames))

    def parse_arguments(self, args):
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
        include_functions = []
        if args:
            include_functions.append(args.pop(0))
        if 'YAML_TEST_FUNCTIONS' in os.environ:
            include_functions.extend(os.environ['YAML_TEST_FUNCTIONS'].split())
        include_filenames = []
        include_filenames.extend(args)
        if 'YAML_TEST_FILENAMES' in os.environ:
            include_filenames.extend(os.environ['YAML_TEST_FILENAMES'].split())
        return include_functions, include_filenames, verbose

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

    def run(self, collections, args=None):
        test_functions = self.find_test_functions(collections)
        test_filenames = self.find_test_filenames(_DATA_DIR)
        include_functions, include_filenames, verbose = self.parse_arguments(args)
        results = []
        for function in test_functions:
            if yaml.common.PY3:
                name = function.__name__
            else:
                name = function.func_name

            if include_functions and name not in include_functions:
                continue
            if function.unittest:
                for base, exts in test_filenames:
                    if include_filenames and base not in include_filenames:
                        continue
                    filenames = []
                    for ext in function.unittest:
                        if ext not in exts:
                            break
                        filenames.append(os.path.join(DATA, base+ext))
                    else:
                        skip_exts = getattr(function, 'skip', [])
                        for skip_ext in skip_exts:
                            if skip_ext in exts:
                                break
                        else:
                            result = self.execute(function, filenames, verbose)
                            results.append(result)
            else:
                result = self.execute(function, [], verbose)
                results.append(result)
        return self.display(results, verbose=verbose)

    def get_file(self, request):
        fixture_name = request.fixturename
        # test_name = request.node.name

        parts = ['.{}'.format(name) for name in set(fixture_name.split('_'))]
        for part in parts:
            for name, entries in self.filenames:
                if part in entries:
                    return os.path.join(os.path.join(_DATA_DIR, '{}{}'.format(name, part)))

        return None


TEST_DATA = TestFunctionData()


@fixture(scope="function", name="verbose")
def fixture_verbose():
    """Returns the data filename associated with this test."""
    return True


def _get_file(request):
    return TEST_DATA.get_file(request)


@fixture(scope="function", name="canonical_filename")
def fixture_canonical_filename(request):
    """Returns the data filename associated with this test."""
    return _get_file(request)


@fixture(scope="function", name="code_filename")
def fixture_code_filename(request):
    """Returns the data filename associated with this test."""
    return _get_file(request)


@fixture(scope="function", name="data_filename")
def fixture_data_filename(request):
    """Returns the data filename associated with this test."""
    return _get_file(request)


@fixture(scope="function", name="detect_filename")
def fixture_detect_filename(request):
    """Returns the data filename associated with this test."""
    return _get_file(request)


@fixture(scope="function", name="error_filename")
def fixture_error_filename(request):
    """Returns the data filename associated with this test."""
    return _get_file(request)


@fixture(scope="function", name="events_filename")
def fixture_events_filename(request):
    """Returns the data filename associated with this test."""
    return _get_file(request)


@fixture(scope="function", name="input_filename")
def fixture_input_filename(request):
    """Returns the data filename associated with this test."""
    return _get_file(request)


@fixture(scope="function", name="marks_filename")
def fixture_marks_filename(request):
    """Returns the data filename associated with this test."""
    return _get_file(request)


@fixture(scope="function", name="path_filename")
def fixture_path_filename(request):
    """Returns the data filename associated with this test."""
    return _get_file(request)


@fixture(scope="function", name="recursive_filename")
def fixture_recursive_filename(request):
    """Returns the data filename associated with this test."""
    return _get_file(request)


@fixture(scope="function", name="sorted_filename")
def fixture_sorted_filename(request):
    """Returns the data filename associated with this test."""
    return _get_file(request)


@fixture(scope="function", name="structure_filename")
def fixture_structure_filename(request):
    """Returns the data filename associated with this test."""
    return _get_file(request)


@fixture(scope="function", name="tokens_filename")
def fixture_tokens_filename(request):
    """Returns the data filename associated with this test."""
    return _get_file(request)


@fixture(scope="function", name="unicode_filename")
def fixture_unicode_filename(request):
    """Returns the data filename associated with this test."""
    return _get_file(request)
