import codecs
import os
import os.path
import tempfile

import yaml
import yaml.common


def _unicode_open(file, encoding, errors='strict'):
    if yaml.common.PY2:
        info = codecs.lookup(encoding)
        if isinstance(info, tuple):
            reader = info[2]
            writer = info[3]
        else:
            reader = info.streamreader
            writer = info.streamwriter
        srw = codecs.StreamReaderWriter(file, reader, writer, errors)
        srw.encoding = encoding
        return srw
    return file

def test_unicode_input(unicode_filename, verbose=False):
    data = open(unicode_filename, 'rb').read().decode('utf-8')
    value = ' '.join(data.split())
    if yaml.common.PY3:
        output = yaml.full_load(data)
        assert output == value, (output, value)
        output = yaml.full_load(yaml.common.StringIO(data))
    else:
        output = yaml.full_load(_unicode_open(yaml.common.BytesIO(yaml.common.ensure_binary(data)), 'utf-8'))
    assert output == value, (output, value)
    tests = []
    if yaml.common.PY2:
        tests.append(data)
    tests.extend([
        data.encode('utf-8'),
        codecs.BOM_UTF8+data.encode('utf-8'),
        codecs.BOM_UTF16_BE+data.encode('utf-16-be'),
        codecs.BOM_UTF16_LE+data.encode('utf-16-le')])
    for input in tests:
        if verbose:
            print("INPUT:", repr(input[:10]), "...")
        output = yaml.full_load(input)
        assert output == value, (output, value)
        output = yaml.full_load(yaml.common.BytesIO(input))
        assert output == value, (output, value)

test_unicode_input.unittest = ['.unicode']

def test_unicode_input_errors(unicode_filename, verbose=False):
    data = open(unicode_filename, 'rb').read().decode('utf-8')
    for input in [data.encode('utf-16-be'),
            data.encode('utf-16-le'),
            codecs.BOM_UTF8+data.encode('utf-16-be'),
            codecs.BOM_UTF8+data.encode('utf-16-le')]:

        try:
            yaml.full_load(input)
        except yaml.YAMLError as exc:
            if verbose:
                print(exc)
        else:
            raise AssertionError("expected an exception")
        try:
            yaml.full_load(yaml.common.BytesIO(input))
        except yaml.YAMLError as exc:
            if verbose:
                print(exc)
        else:
            raise AssertionError("expected an exception")

test_unicode_input_errors.unittest = ['.unicode']

def test_unicode_output(unicode_filename, verbose=False):
    data = yaml.common.ensure_text(open(unicode_filename, 'rb').read())
    value = ' '.join(data.split())
    for allow_unicode in [False, True]:
        data1 = yaml.dump(value, allow_unicode=allow_unicode)
        for encoding in [None, 'utf-8', 'utf-16-be', 'utf-16-le']:
            stream = yaml.common.StringIO()
            yaml.dump(value, _unicode_open(stream, 'utf-8'), encoding=encoding, allow_unicode=allow_unicode)
            data2 = stream.getvalue()
            data3 = yaml.dump(value, encoding=encoding, allow_unicode=allow_unicode)

            if yaml.common.PY2:
                stream = yaml.common.BytesIO()
                yaml.dump(value, stream, encoding=encoding, allow_unicode=allow_unicode)
                data4 = stream.getvalue()

                assert isinstance(data1, yaml.common.string_types), (type(data1), encoding)
                data1.decode('utf-8')
                assert isinstance(data2, yaml.common.binary_type), (type(data2), encoding)
                data2.decode('utf-8')
                if encoding is None:
                    assert isinstance(data3, yaml.common.string_types), (type(data3), encoding)
                    assert isinstance(data4, yaml.common.string_types), (type(data4), encoding)
                else:
                    assert isinstance(data3, yaml.common.string_types), (type(data3), encoding)
                    data3.decode(encoding)
                    assert isinstance(data4, yaml.common.string_types), (type(data4), encoding)
                    data4.decode(encoding)
            else:
                if encoding is not None:
                    assert isinstance(data3, bytes)
                    data3 = data3.decode(encoding)
                stream = yaml.common.BytesIO()
                if encoding is None:
                    try:
                        yaml.dump(value, stream, encoding=encoding, allow_unicode=allow_unicode)
                    except TypeError as exc:
                        if verbose:
                            print(exc)
                        data4 = None
                    #else:
                    #    raise AssertionError("expected an exception")
                else:
                    yaml.dump(value, stream, encoding=encoding, allow_unicode=allow_unicode)
                    data4 = stream.getvalue()
                    if verbose:
                        print("BYTES:", data4[:50])
                    data4 = data4.decode(encoding)

                assert isinstance(data1, str), (type(data1), encoding)
                assert isinstance(data2, str), (type(data2), encoding)

test_unicode_output.unittest = ['.unicode']

def test_file_output(unicode_filename, verbose=False):
    with open(unicode_filename, 'rb') as file:
        data = file.read().decode('utf-8')
    handle, filename = tempfile.mkstemp()
    os.close(handle)
    try:
        stream = yaml.common.StringIO()
        if yaml.common.PY2:
            yaml.dump(data, stream, allow_unicode=True)
            data1 = stream.getvalue()
            stream = open(filename, 'wb')
            yaml.dump(data, stream, allow_unicode=True)
            stream.close()
            data2 = open(filename, 'rb').read()
            stream = open(filename, 'wb')
            yaml.dump(data, stream, encoding='utf-16-le', allow_unicode=True)
            stream.close()
            data3 = open(filename, 'rb').read().decode('utf-16-le')[1:].encode('utf-8')
            stream = _unicode_open(open(filename, 'wb'), 'utf-8')
            yaml.dump(data, stream, allow_unicode=True)
            stream.close()
            data4 = open(filename, 'rb').read()
        else:
            yaml.dump(data, stream, allow_unicode=True)
            data1 = stream.getvalue()
            stream = yaml.common.BytesIO()
            yaml.dump(data, stream, encoding='utf-16-le', allow_unicode=True)
            data2 = stream.getvalue().decode('utf-16-le')[1:]
            with open(filename, 'w', encoding='utf-16-le') as stream:
                yaml.dump(data, stream, allow_unicode=True)
            with open(filename, 'r', encoding='utf-16-le') as file:
                data3 = file.read()
            with open(filename, 'wb') as stream:
                yaml.dump(data, stream, encoding='utf-8', allow_unicode=True)
            with open(filename, 'r', encoding='utf-8') as file:
                data4 = file.read()
        assert data1 == data2, (data1, data2)
        assert data1 == data3, (data1, data3)
        assert data1 == data4, (data1, data4)
    finally:
        if os.path.exists(filename):
            os.unlink(filename)

test_file_output.unittest = ['.unicode']

def test_unicode_transfer(unicode_filename, verbose=False):
    data = open(unicode_filename, 'rb').read().decode('utf-8')
    for encoding in [None, 'utf-8', 'utf-16-be', 'utf-16-le']:
        input = data
        if encoding is not None:
            input = (u'\ufeff'+input).encode(encoding)
        output1 = yaml.emit(yaml.parse(input), allow_unicode=True)
        if encoding is None:
            stream = yaml.common.StringIO()
        else:
            stream = yaml.common.BytesIO()
        yaml.emit(yaml.parse(input), _unicode_open(stream, 'utf-8'), allow_unicode=True)
        output2 = stream.getvalue()
        if encoding is None:
            assert isinstance(output1, yaml.common.string_types), (type(output1), encoding)
        else:
            assert isinstance(output1, yaml.common.string_types), (type(output1), encoding)
            if yaml.common.PY2:
                output1.decode(encoding)
            assert isinstance(output2, yaml.common.binary_type if yaml.common.PY3 else yaml.common.string_types), (type(output2), encoding)
            if yaml.common.PY2:
                output2.decode('utf-8')


test_unicode_transfer.unittest = ['.unicode']

if __name__ == '__main__':
    import test_appliance
    test_appliance.run(globals())
