import hashlib, os, sys
from os.path import join, realpath
import shutil
from distutils.dir_util import copy_tree
import pkgutil

from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import Terminal256Formatter
from pygments.styles import get_style_by_name
from pprint import pformat

from os.path import join, splitext, relpath
import tempfile
from termcolor import colored

from clyde2.clyde_logging import get_logger
logger = get_logger()


from pkg_resources import resource_filename

style = get_style_by_name('friendly')
def pprint_color(obj):
  print highlight(pformat(obj), PythonLexer(), Terminal256Formatter(style=style))


def resource(name):
  filename = resource_filename(__name__, join('../', name))
  return filename


def template_resource(template):
  return realpath(resource(join('templates', template)))



def stable_sha(data):
  """
  Calculate a shaw of a potentailly nested dictionary of 
  strings in a consistant way.

  The dictionary is processed in sorted order recursively,
  and hashses of the contents are appended, and then hashed 
  again
  """
  hash = ""
  if isinstance(data, dict):
    sorted_data = sorted(data.items())
    for k, v in sorted_data:
      hash += stable_sha(v) + "\n"
    return hashlib.sha1(hash.encode('utf-8')).hexdigest()
  elif isinstance(data, bytes):
    return hashlib.sha1(data).hexdigest()
  elif isinstance(data, str):
    return hashlib.sha1(data.encode('utf-8')).hexdigest()
  elif isinstance(data, list):
    for value in data:
      hash += stable_sha(value) + "\n"
      return hashlib.sha1(hash.encode('utf-8')).hexdigest()
  raise Exception("Can't hash dict containing {0}".format(type(data)))


def read_template(template):
  return pkgutil.get_data('clydepm.templates', template)


class temporary_path(object):
  """
  A simple context manager for adding something to the 
  system PATH for a controlled period of time
  """

  def __init__(self, path):
    self.path = path

  def __enter__(self):
    self.old_path = sys.path[:]
    sys.path.append(self.path)

  def __exit__(self, type, value, traceback):
    sys.path = self.old_path


class temporary_env(object):
  """
  A simple context manager for extending the system environment
  """

  def __init__(self, env_dict):
    self.env_dict = env_dict

  def __enter__(self):
    self.updated_mappings = {}
    self.added_mappings = set()
    for key, value in self.env_dict.iteritems():
      if key in os.environ:
        self.updated_mappings[key] = os.environ[key]
      else:
        self.added_mappings.add(key)

      os.environ[key] = value

  def __exit__(self, type, value, traceback):
    for key, value in self.updated_mappings.iteritems():
      if key in os.environ:
        os.environ[key] = value
    for key in self.added_mappings:
      del os.environ[key]



class temp_dir(object):

  def __init__(self):
    self.dir = tempfile.mkdtemp()

  def __enter__(self):
    return self.dir

  def __exit__(self, type, value, traceback):
    shutil.rmtree(self.dir)

class temp_cwd(object):
  """
  A simple context manager for changing directories
  """

  def __init__(self, path):
    self.path = path

  def __enter__(self):
    self.old_path = os.getcwd()
    os.chdir(self.path)

  def __exit__(self, type, value, traceback):
    os.chdir(self.old_path)



def dict_contains(superset, subset):
  return all(item in list(superset.items()) for item in list(subset.items()))


def list_contains(list, d):
  for item in list:
    if dict_contains(item, d):
      return True
  return False


def listdir_fullpath(d):
  return [os.path.join(d, f) for f in os.listdir(d)]

valid_source_extensions = ['.cpp', '.c', '.cc', '.c++']
valid_header_extensions = ['.h', '.hpp']


def ext(file):
  return splitext(file)[1]

def is_cpp(file):
  return ext(file) in ['.cpp', 'cc', 'c++']

def is_c(file):
  return ext(file) in ['.c']


def fail(str):
  logger.error(colored("Error: " + str, 'red') + '\n')
  sys.exit(1)

def warn(str):
  logger.warn(colored("Warning: " + str, 'yellow'))
