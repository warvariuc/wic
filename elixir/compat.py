import sys

if sys.version_info[0] < 3:
    PY3 = False

    def b(s):
        return s

    def u(s):
        return unicode(s, "unicode_escape")

    import StringIO
    StringIO = BytesIO = StringIO.StringIO
    text_type = unicode
    binary_type = str
    string_types = basestring,
    integer_types = (int, long)

    def with_metaclass(meta, base=object):
        class _ElixirBase(base):
            __metaclass__ = meta
        return _ElixirBase

    execfile_ = execfile
else:
    PY3 = True

    def b(s):
        return s.encode("latin-1")

    def u(s):
        return s

    import io
    StringIO = io.StringIO
    BytesIO = io.BytesIO
    text_type = str
    binary_type = bytes
    string_types = str,
    integer_types = int,

    exec_ = eval("exec")

    def execfile_(file, globals=globals(), locals=locals()):
        f = open(file, "r")
        try:
            exec_(f.read()+"\\n", globals, locals)
        finally:
            f.close()

    def with_metaclass(meta, base=object):
        ns = dict(base=base, meta=meta)
        exec_("""class _ElixirBase(base, metaclass=meta):
    pass""", ns)
        return ns["_ElixirBase"]

long_type = integer_types[-1]

