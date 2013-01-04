from pygit2 import GIT_OBJ_BLOB, GIT_OBJ_TREE, GIT_OBJ_COMMIT, GIT_OBJ_TAG
import re
import binascii

HEX_RE = re.compile(r'^[0-9a-f]{40}$')


def is_valid_value(value):
    if value is None or value == '':
        return False
    return True


def is_valid_hex(value):
    if HEX_RE.match(str(value)):
        return True
    return False


def parse_path(path):
    path = '/' + path.rstrip('/')
    if not path.startswith('/'):
        path = '/' + path
    path = re.sub(r'/+', '/', path)

    dirname = None
    filename = None
    m = re.match(r'(.*?)([^/]*)$', path)
    if m:
        dirname = m.group(1)
        filename = m.group(2)
    if filename is None:
        filename = ''
    return dirname, filename


def make_dir_paths(path):
    segments = path.split('/')[0:-1]
    dirs = []
    if len(segments) == 0:
        dirs.append('/')

    for i in range(len(segments)):
        parts = segments[0:i + 1]
        parts.append('')
        dirs.insert(0, '/'.join(parts))

    return dirs


def entry_to_dict(entry):
    obj = entry.to_object()

    type = {
        GIT_OBJ_BLOB: 'blob',
        GIT_OBJ_COMMIT: 'commit',
        GIT_OBJ_TREE: 'tree',
        GIT_OBJ_TAG: 'tag',
    }[obj.type]

    d = {
        'name': entry.name,
        'sha1': entry.hex,
        'mode': oct(entry.filemode),
        'type': type,
        'size': len(obj.read_raw()),
    }
    if type != 'blob':
        del d['size']
    return d


def sha_hex2bin(sha):
    return binascii.unhexlify(sha.encode('ascii'))
