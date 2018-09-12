import inspect
import sys


def _format_args(frame):
    arginfo = inspect.getargvalues(frame)
    args = []
    for key, value in arginfo.locals.items():
        if key not in arginfo.args:  # pragma: nocoverage
            continue
        args.append('%s=%r' % (key, value))

    return ','.join(args) or ''


def debug(msg='', *args):
    frame = sys._getframe(1)
    context = frame.f_globals['__name__']
    func = frame.f_code.co_name
    sys.stderr.write("+ %s.%s(%s): %s %s\n" % (context, func, _format_args(frame),
                                               msg, ', '.join(args)))
    sys.stderr.flush()
