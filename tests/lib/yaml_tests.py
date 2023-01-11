from test_canonical import *
from test_constructor import *
from test_emitter import *
from test_errors import *
from test_input_output import *
from test_mark import *
from test_multi_constructor import *
from test_reader import *
from test_recursive import *
from test_representer import *
from test_resolver import *
from test_sort_keys import *
from test_structure import *  # type: ignore[no-redef]
from test_tokens import *

if __name__ == '__main__':
    import test_appliance
    test_appliance.run(globals())

