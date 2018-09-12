import os
import subprocess
import sys

from acibuild.logutils import debug


def command(cmd, shell=False, env=None):
    call_env = os.environ.copy()
    if env is not None:
        call_env.update(env)
    debug("executing")
    retval = 0
    if os.environ.get('INVADE_BUILD_LOG', 'false') == 'true' and 'build' in " ".join(cmd):
        file = open("build.log", "w")
        retval = subprocess.call(cmd, shell=shell, env=call_env, stdout=file, stderr=file)
        file.close()
    else:
        retval = subprocess.call(cmd, shell=shell, env=call_env)
    debug("done, retval=%d" % (retval, ))
    return retval


def check_command(cmd, shell=True):
    debug("executing")
    subprocess.check_call(cmd, shell=shell, env=os.environ)


def check_output(args, shell=False):
    debug("executing")
    output = subprocess.check_output(args, stderr=1, shell=shell)
    if hasattr(sys.stderr, 'flush'):
        sys.stderr.flush()
    return output


def check_piped_output(cmd1_args=[], cmd2_args=[]):
    #FIX ME: Doesn't work on windows
    p1 = subprocess.Popen(cmd1_args, stdout=subprocess.PIPE)
    p2 = subprocess.Popen(cmd2_args, stdin=p1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
    output = p2.communicate()[0]
    return [output, p2.returncode]
