if __name__ == '__main__':
    import distutils.util
    import os
    import sys
    build_lib = 'build/lib'
    build_lib_ext = os.path.join('build', 'lib.{}-{}.{}'.format(distutils.util.get_platform(), *sys.version_info))
    sys.path.insert(0, build_lib)
    sys.path.insert(0, build_lib_ext)
    import test_appliance
    import yaml_tests_ext
    test_appliance.run(yaml_tests_ext)
