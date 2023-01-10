import sys

import yaml

import test_appliance


def main(args=None):
    collections = []
    import yaml_tests
    collections.append(yaml_tests)
    if yaml.__with_libyaml__:
        import yaml_tests_ext
        collections.append(yaml_tests_ext)
    return test_appliance.run(collections, args)

if __name__ == '__main__':
    sys.exit(main())
