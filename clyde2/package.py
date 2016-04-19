import yaml
from os.path import realpath, join, splitext, isfile, relpath
from os import listdir
from semantic_version import Version, Spec
from .common import listdir_fullpath, dict_contains, fail
import os

from clyde2.clyde_logging import get_logger
logger = get_logger()

valid_source_extensions = ['.cpp', '.c', '.cc', '.c++']
valid_header_extensions = ['.h', '.hpp']
class Package(object):

  def __init__(self, name, version):
    self.name = name
    self.version = version


class ClydePackage(object):

  def __init__(self, path, traits = None):
    self.path = realpath(path)
    config_file = join(path, 'config.yaml')

    self.deps = []
    self.inflated_deps = set()

    with open(config_file,'r') as f:
      self.config = yaml.load(f)
      self.name  = self.config['name']
      self.version  = Version(self.config['version'], partial=True)


      if 'cflags' in traits:
        if type(self.config['cflags']) == dict:
          self.config['cflags'] = self.config['cflags']['gcc']
          self.config['cflags'] += traits['cflags']
        else:
          self.config['cflags'] += traits['cflags']

    self.evaluate_config_sugar(traits)


  def __repr__(self):
    return "ClydePackage(" + self.config['name'] + ", " + self.config['version'] + ")" 
    

  def inflate(self, dependencies):
    """
      Resolve the internal dependency links to point
      at actual packages, rather than names and specs

      dependencies is a list of dependencies whos version
      is already correct based on global dependency specifications
      of all packages in the build tree.
    """

    for name, version in self.get_dependency_configurations():
      if name in dependencies:
        self.inflated_deps.add(dependencies[name])
      else:
        raise fail("Could not inflate {0}".format(name))



  def get_inflated_dependencies(self):
    return self.inflated_deps


  def get_dependency_configurations(self):
    """
    Return an array of dictionaries
    with dependency names, version strings.

    Dependencies are computed by looking at the list
    of enabled variants, and getting their dependencies, 
    potentially overwriting original dependencies
    
    If the version is local
      then base-version and local-path will be set


    """
    deps = []

    for variant in self.resolve_variants():
      # Note: the variants have already been resolved
      # This for loop simply needs to resolve the dependencies one
      # by one, potentially overwriding earlier ones
      name, value = next(iter(variant.items()))
      if 'requires' in value and value['requires'] is not None:
        requires = value['requires']
        for req_name, req_config in requires.items():
          deps.append((req_name, req_config['version']))

    return deps


  def get_files_in_dir(self, dir, extensions):

    def valid(file):
      f, ext = splitext(file)
      return isfile(file) and ext in extensions
    dir = join(self.path, dir)
    if not os.path.exists(dir):
      return set()
    files = filter(valid, listdir_fullpath(dir))
    return set(files)


  def get_source_files(self, rel = None):
    files = []
    if 'variant' in self.traits and self.traits['variant'] == 'test':
      pass
    for variant in self.resolve_variants():
      variant = variant.keys()[0]
      files.extend( self.get_files_in_dir(variant, valid_source_extensions))
    return self.make_relative(files, rel)


  def get_include_paths(self, rel = None):
    files = set([join(self.path, 'include')])
    return self.make_relative(files, rel)


  def get_header_files(self, rel = None):
    files = self.get_files_in_dir('include', valid_header_extensions)
    return self.make_relative(files, rel)


  def get_cflags(self):
    return self.config['cflags']


  def make_relative(self, paths, rel):
    if rel:
      return set(map(lambda f: relpath(f, rel), paths))
    else:
        return paths


  def evaluate_config_sugar(self, traits):
    """
    Transform the config dictionary, evaluating some
    special config directives into a standardized form.

    For example, the src variant is created automatically,
    and the dependencies are taken from the top level requires
    statement.

    Future versions may do a similar thing for the test variant
    """

    if traits is  None:
      self.traits = {}
    else:
      self.traits = traits.copy()

    # Do some configuration parsing magic

    if 'requires' in self.config:
      for name, details in self.config['requires'].iteritems():
        version = details['version']
        self.deps.append ((name, version))



    if 'variants' not in self.config:
      self.config['variants'] = [
      ]


    if 'requires' in self.config and self.config['requires'] is not None:
      src = {'requires' : self.config['requires']}
    else:
      src = {}
    try:
      self.config['variants'].insert(0, { 
        'src' : src
        
      }) 
    except AttributeError as e:
      raise Exception("Variants should be specified as a list. \n"
                     "Hint: Try putting a - character before each variant")


  def resolve_variants(self):
    """
    This method handles multiple package variants.
    
    Package variants are just alternate directories of source files 
    that are conditionally compiled and linked together.

    For example, running test cases requires the src variant linked 
    with the test suite object files + dependencies.


    This method does not handle resolving dependency overriding, only
    determining which variants will get linked.

    """

    def evaluate_clause(clause):
      if 'or' in clause or 'and' in clause:
        raise Exception("Reserved keyword 'and || or' used.")
      v = dict_contains(self.traits, clause)
      return v
    
    def process_effects(variant_name, variant_details):
      """
      This nested function handles the effects of a 
      given clause.
      
      Right now, the only relevant effect is 'replace',
      which causes a variant to replace an existing variant
      
      """
      if 'replaces' in variant_details:
        enabled_variants.remove(variant_details['replaces'])
      enabled_variants.add(variant_name)

      if 'cflags'  in variant_details:
        if type(variant_details['cflags']) == dict:
          self.config['cflags'] += variant_details['cflags']['gcc']
        else:
          self.config['cflags'] += " "  + variant_details['cflags']
    # Beginning of main function
    if 'filtered_variants' in self.__dict__:
      return self.filtered_variants
      
    enabled_variants = set(['src'])
    variants = self.get_variants()
    
    for variant in variants:
      assert len(variant) == 1
      for name, details in  variant.items():
        if 'when' in details:
          enabled = evaluate_clause(details['when'])
          if enabled:
            process_effects(name, details)
    self.variant_dirs = {}
    for variant_name in enabled_variants:
      self.variant_dirs[variant_name] =  join(self.path, variant_name)

    self.filtered_variants = [a for a in self.get_variants() if list(a.keys())[0] in enabled_variants]
    return self.filtered_variants

  def get_variants(self):
    if 'variants' in self.config:
      return self.config['variants']
    else:
      return []


  def __hash__(self):
    return hash(self.name + str(self.version))


  def __eq__(self, other):
    return self.name == other.name and self.version == other.version

  @staticmethod
  def create_new_package(path = None, package_type = 'library', configuration = None):
    logger.info("Creating new package")
    configs = [join(path, 'config.yaml'), join(path, 'descriptor.yaml')]
    for config in configs:
      if os.path.exists(config):
        fail("Package already exists at {0}".format(path))
    # Create initial directory structure and config.yaml
    # For now, just do it manually
    # TODO: Make class for handling directory structures that plays well
    # with package variants

    dirname = os.path.split(path)[1]

    directories = ['src',
                   join('include', dirname),
                  ]
    directories = [join(path, d) for d in directories]

    for dir in directories:
      if not os.path.exists(dir):
        os.makedirs(dir)



    package_config = {
      'name'            : dirname,
      'author'          : str(configuration['General']['user.name']),
      'author-email'    : str(configuration['General']['user.email']),
      'cflags'          : {'gcc' : '-std=c++11'},
      'version'         : '0.0.0',
      'type'            : package_type,
      'url'             : 'http://example.com'
    
    }
    with open('config.yaml', 'w') as f:
      f.write(yaml.dump(package_config))


class TestPackage():

  def __init__(self, name, version, dependencies = None):
    self.name = name
    self.version = version
    if dependencies:
      self.deps = dependencies
    else:
      self.deps = []

  def get_dependencies(self):
    return self.deps

  def __repr__(self):
    return "TestPackage(" + self.name + ", " + str(self.version) + ")" 

    
  def __hash__(self):
    return hash(self.name + str(self.version))

  def __eq__(self, other):
    return self.name == other.name and self.version == other.version

