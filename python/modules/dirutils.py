import contextlib
import errno
import os
import shutil
import time
import zipfile

from acibuild.logutils import debug


def safe_mkdir(directory):
    try:
        os.makedirs(directory)
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise


def get_homedir():
    # HOMEPATH is Windows
    return os.environ.get('HOMEPATH', 'HOME')


@contextlib.contextmanager
def safe_chdir(newdir):
    curdir = os.getcwd()
    os.chdir(newdir)
    try:
        yield
    finally:
        os.chdir(curdir)


# FIXME: Write tests for this
def clean_directory(directory):  # pragma: nocoverage
    """Removes all the files and directories in the current directory"""
    for filename in os.listdir(directory):
        full = os.path.join(directory, filename)
        if os.path.isdir(full):
            shutil.rmtree(full)
        else:
            os.remove(full)


def clean_directory_by_age(element, extremity_date, exclude_list, lockfile='never-delete'):
    filename = os.path.basename(element)
    if filename in exclude_list:
        debug(element + " excluded")
        return
    try:
        if os.path.isdir(element):
            files = os.listdir(element)
            if lockfile in files:
                debug("%s build is locked for deletion, lockfile:%s" % (element, lockfile))
                return
            for el in files:
                element_abs = os.path.join(element, el)
                clean_directory_by_age(element_abs, extremity_date, exclude_list, lockfile=lockfile)
            if os.listdir(element) == []:
                created_date = time.strftime("%Y/%m/%d", time.localtime(os.path.getmtime(element)))
                if extremity_date > created_date:
                    debug(element + " is empty and being deleted")
                    shutil.rmtree(element)
        else:
            if os.path.exists(element):
                created_date = time.strftime("%Y/%m/%d", time.localtime(os.path.getmtime(element)))
            elif os.path.islink(element):
                parent = os.path.dirname(element)
                created_date = time.strftime("%Y/%m/%d", time.localtime(os.path.getmtime(parent)))
            if extremity_date > created_date:
                debug("File %s created on %s is being deleted" % (element, created_date))
                if os.path.isfile(element):
                    os.remove(element)
                elif os.path.islink(element):
                    os.unlink(element)
    except Exception, e:
            debug('Failed delete: ' + element + " Error:" + str(e))
    finally:
            pass


def remove_files_by_ext(exts):
#    for root, dirs, files in os.walk('.'):
#        for currentFile in files:
#            if any(currentFile.lower().endswith(ext) for ext in exts):
#                print "Removing file: " + currentFile
#                os.remove(os.path.join(root, currentFile))
    for f in os.listdir('.'):
        if os.path.isfile(os.path.join('.', f)) and any(f.lower().endswith(ext) for ext in exts):
            print "Removing file: " + f
            os.remove(f)


def copy_and_overwrite(from_path, to_path, ignore_files=[]):
    if os.path.exists(to_path):
        shutil.rmtree(to_path)
    try:
        shutil.copytree(from_path, to_path, symlinks=True, ignore=shutil.ignore_patterns(*ignore_files))
    except:
        debug("Errors occured while copying artifact %s" % (from_path))


def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)


def unzip(source_filename, dest_dir):
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    with zipfile.ZipFile(source_filename) as zf:
        zf.extractall(dest_dir)
