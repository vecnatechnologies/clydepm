from sys import stdout
from sys import stdout
from os.path import join, splitext, relpath, split
import StringIO
import os
from clyde2.common import is_c, is_cpp
from clyde2.common import pprint_color, dict_contains

from os.path import join, splitext, relpath, split
import os
from clyde2.common import is_c, is_cpp
from clyde2.common import pprint_color, dict_contains
import Queue


def topological_sort(library):
  output = {}
  q = Queue.Queue()
  library['distance'] = 0
  q.put(library)
  while not q.empty():
    current = q.get()
    d = current['distance'] 
    name = current['name']
    if d in output:
      output[d].append(name)
    else:
      output[d] = [name]
    for libname, lib in current['libraries'].iteritems():
      print libname
      if 'distance' not in lib:
        lib['distance'] = current['distance'] + 1
        q.put(lib)
  print output




def generate_file(tree, prefix = '', toolchain = None, root = None):
  output = StringIO.StringIO()
  print pprint_color(tree)

  for libname, library  in tree.iteritems():
    topological_sort(library)
