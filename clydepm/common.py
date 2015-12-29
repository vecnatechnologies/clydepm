import hashlib, os, sys
from os.path import join
from distutils.dir_util import copy_tree

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


