import sys

import test_appliance


def main(args=None):
    collections = []

    try:
        import yaml

        import yaml_tests

        collections.append(yaml_tests)
        if yaml.__with_libyaml__:
            import yaml_tests_ext
            collections.append(yaml_tests_ext)

        success = test_appliance.run(collections, list(args or []))
    except ImportError:
        success = False

    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main(sys.argv))
