from semantic_version import Version, Spec
from clyde2.common import pprint_color, dict_contains
from os.path import join, abspath, relpath
import functools
def insert_dependency(candidates, new_dependency, server): 
  pass

class SpecException(Exception):

  def __init__(self, package, dep_name, spec):
    self.package = package
    self.dep_name = dep_name
    self.spec = spec

  def __str__(self):
    return "Package {0} requires version {1} of {2}. This is an invalid specification".format(
      self.package.name,
      self.spec, 
      self.dep_name
    )



def get_spec(candidates, name):
  specs = []
  for package in candidates:
    deps = package.get_dependency_configurations()
    for d_name, spec in deps:
      if name == d_name:
        specs.append(spec)
        try:
          spec = Spec(*specs)
        except ValueError as e:
          raise SpecException(package, d_name, spec)
  if not specs:
    return None
  spec = Spec(*specs)
  return spec
      


def replace_by_name(candidates, new_candidate):
  to_delete = None
  for package in candidates:
    if package.name == new_candidate.name:
      to_delete = package
  if to_delete:
    candidates.remove(to_delete)
  candidates.add(new_candidate)
      
def get_frozen_packages(frozen_packages, server, traits):
  output = set()
  for name, version in frozen_packages.iteritems():
    spec = Spec('==' + version)
    
    best  = server.best(name,  spec, traits, False)
    if not best:
      raise Exception("Could not satisfy {0} Version {1}".format(name, spec))
    output.add(best)
  return output


def resolve_package_dependencies(root_package, server, traits, fetch_remote):
  pass
  
  candidates = set([root_package])
  new_candidates = candidates.copy()

  while True: 
    for package in candidates:
      for name, version in package.get_dependency_configurations():
        spec = get_spec(candidates, name)
        best = server.best(name, spec, traits, fetch_remote)
        if not best:
          raise Exception("Could not satisfy {0} Version {1}".format(name, spec))
        replace_by_name(new_candidates, best)
    if candidates == new_candidates:
      break
    else:
      candidates = new_candidates.copy()

  return candidates

def insert_per_dependency_include(libinfo):
  if 'libraries' in libinfo:
    for depname, depinfo in libinfo['libraries'].iteritems():
      pass 
      #libinfo['include'].add(join('deps', depname, 'include'))
    #libinfo['include'].add(join('deps', libinfo['name'], 'include'))

def add_includes_for_libraries(library, depth):
  if depth == 0:
    if 'variant' in library and 'platform' in library:
      if library['variant'] == 'test':
        library['type'] = 'application'
  insert_per_dependency_include(library)


def gather_include_paths(libraries, library, depth):
  if 'include' in library:
    libraries |= library['include']


def gather_library_names(libraries, library, depth):
  if 'name' in library and depth != 0:
    libraries.add(library['name'])


def insert_dependencies(libraries, library, depth):
  # All libraries should include all other ones?
  if 'include' in library:
    library['include'] |= set(map(abspath, libraries))

    
def walk_tree(tree, visitor, depth = 0):
  name, info = tree.iteritems().next()
  visitor(info, depth)
  if 'libraries' in info:
    for libname, libinfo in info['libraries'].iteritems():
      walk_tree({libname: libinfo}, visitor, depth + 1)


def create_build_tree(package, top = True, visited = None):
  if not visited:
    visited = set()

  name = package.name

  visited.add(name)

  deps = package.get_inflated_dependencies()

  def is_not_visited(dep):
    if dep.name in visited:
      return False
    else:
      return True

  deps = filter(is_not_visited, deps)


  libraries = map(lambda a: create_build_tree(a, False, visited), deps)

  new_libraries = {}
  for lib in libraries:
    new_libraries.update(lib)
  output  = {
    name : {
      'name'      : package.config['name'],
      'type'      : package.config['type'],
      'version'   : package.config['version'],
      'platform'  : package.traits['platform'],
      'sources'   : package.get_source_files(),
      'headers'   : package.get_header_files(),
      'include'   : package.get_include_paths(),
      'cflags'    : package.get_cflags(),
      'libraries' : new_libraries
    }
  }
  if (top):
    output[name]['variant'] = package.traits['variant']
    walk_tree(output, add_includes_for_libraries)
    libraries = set()
    walk_tree(output, functools.partial(gather_include_paths, libraries))

    walk_tree(output, functools.partial(insert_dependencies, libraries))


  else:
    output[name]['variant'] = 'src'
  return output

  
