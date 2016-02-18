#!/usr/bin/env python
import sys, os
from subprocess import Popen, PIPE
import json

from os.path import splitext, join, realpath
import shutil
import yaml
from distutils.dir_util import copy_tree
import distutils
from termcolor import colored

from .common import temp_cwd, dict_contains, stable_sha 

class CompilationError(Exception):

    def __init__(self, stderr = None):
        self.stderr = stderr
        Exception.__init__(self)

    def __repr__(self):
      return u"Compilation Failed\n\n\t" + str(self.stderr.decode("utf-8"))

    def __str__(self):
      return "Compilation Error: \n\n" + str(self.stderr.decode('utf-8'))

class PackageError(Exception):

    def __init__(self, error = None):
        self.error = error
        Exception.__init__(self)

    def __str__(self):
      return self.error

    def __repr__(self):
        return self.__str__()

class EmptyPackage(object):

  def __init__(self, name, version):
      self.name = name
      self.version = version

  def __hash__(self):
      h = int(stable_sha({'name': self.name, 
                         }), 16)
      return h
  def __repr__(self):
    return "{0}-{1}".format(self.name, self.version)

  def __eq__(self, other):
    return hash(self) == hash(other)


class Package(object):

  @staticmethod
  def create_new_package(path = None, package_type = 'library', configuration = None):
    print ("Creating new package")
    configs = [join(path, 'config.yaml'), join(path, 'descriptor.yaml')]
    for config in configs:
      if os.path.exists(config):
        raise PackageError("Package already exists at {0}".format(path))
    # Create initial directory structure and config.yaml
    # For now, just do it manually
    # TODO: Make class for handling directory structures that plays well
    # with package variants

    directories = ['src',
                   'include',
                   'private_include'
                  ]
    directories = [join(path, d) for d in directories]

    for dir in directories:
      if not os.path.exists(dir):
        os.makedirs(dir)


    dirname = os.path.split(path)[1]

    package_config = {
      'name'            : dirname,
      'author'          : configuration['General']['user.name'],
      'author-email'    : configuration['General']['user.email'],
      'cflags'          : {'gcc' : '--std=c99'},
      'version'         : '0.0.0',
      'type'            : package_type,
      'url'             : 'http://example.com'
    
    }
    with open('config.yaml', 'w') as f:
      f.write(yaml.dump(package_config))
      

  def __init__(self, 
               path, 
               form = 'binary', 
               traits = None, 
               root_package = None):

    self.config = None
    # TODO: Clean up multiple types of config files
    if not os.path.exists(path):
      raise Exception("Attempting to use nonexistant path {0} as Package".format(path))
    try: 
      if form == 'source':
        configs = [join(path, 'config.yaml'), join(path, 'descriptor.yaml')]
      elif form == 'binary':
        configs = [join(path, 'descriptor.yaml'),join(path, 'config.yaml')]
      else:
        raise Exception("Invalid form {0}".format(form))
      for config_file in configs:
        if os.path.exists(config_file):
          with open(config_file,'r') as f:
            self.config = yaml.load(f)
            break
        else:
          pass
      if not self.config:
        raise PackageError("No package (missing config.yaml) at {0}".format(path))

    except IOError as io:
      raise PackageError("No package (missing config.yaml) at {0}".format(path))
    

    if traits is  None:
      self.traits = {}
    else:
      self.traits = traits.copy()

    self.path         = path

    self.name         = self.config['name']
    self.include      = realpath(join(self.path, 'include'))
    self.private_include = realpath(join(self.path, 'private_include'))

    self.root_package = root_package
    self.ignored_deps = []

    self.build_dir =    realpath(join(path,      'build'))
    self.archive_dir =  realpath(join(path,      'archive'))
    self.output_dir =   realpath(join(path,      'output'))
    self.dependency_dir = realpath(join(path,    'dependencies'))

    self.form = form

    self.output_dirs = {}

    self.evaluate_config_sugar()
    self.create_build_directories()

    if not os.path.exists(self.dependency_dir):
      os.mkdir(self.dependency_dir)
  
  def get_archive_dir(self):
    return self.archive_dir

  def get_path(self):
    return self.path

  def get_dependency_dir(self):
    return self.dependency_dir

  def get_output_dir(self):
    return self.output_dir
  
  def get_binary(self):
    return self.binary

  def get_configuration(self):
    return self.config
  
  def evaluate_config_sugar(self):
    """
    Transform the config dictionary, evaluating some
    special config directives into a standardized form.

    For example, the src variant is created automatically,
    and the dependencies are taken from the top level requires
    statement.

    Future versions may do a similar thing for the test variant
    """
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
      raise PackageError("Variants should be specified as a list. \n"
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

  def get_hash(self, method = 'timestamp'):
    """
    Returns a hash of the packages sources.
    The sha is based on the last modified timestamp of 
    every file in all variant directories, include, and private_include
    """
    return "asdf"


  def get_variants(self):
    if 'variants' in self.config:
      return self.config['variants']
    else:
      return []

  def create_build_directories(self):
    if not os.path.exists(self.build_dir):
      os.mkdir(self.build_dir)

    self.output_dirs['include'] = join(self.output_dir,  'include', self.name)
    self.output_dirs['lib']     = join(self.output_dir,  'lib', self.name)
    self.output_dirs['bin']     = join(self.output_dir,  'bin', self.name)

    version_string = self.config['version']

    self.library = join( self.output_dirs['lib'], 'lib' + self.name + '-' + version_string + '.a')
    self.binary =  join( self.output_dirs['bin'], self.name + '-' + version_string + '.out')

    for key, dir in self.output_dirs.items():
      if not os.path.exists(dir):
        os.makedirs(dir)


  def clean(self):
    if os.path.exists(self.build_dir):
      shutil.rmtree(self.build_dir)

    if os.path.exists(self.dependency_dir):
      shutil.rmtree(self.dependency_dir)

    if os.path.exists(self.output_dir):
      shutil.rmtree(self.output_dir)

    if os.path.exists(self.archive_dir):
      shutil.rmtree(self.archive_dir)

  def get_form(self):
    return self.form


  def get_traits(self):
    return self.traits.copy()


  def change_extension(self, filename, new_extension):
    f, ext = os.path.splitext(filename)
    return f + new_extension


  def ignore_dependency_by_name(self, dep):
    self.ignored_deps.append(dep)


  def get_static_libraries(self):
    libs = []
    if self.root_package:
      path = join(self.root_package.dependency_dir, 'lib')
    else:
      path = join(self.dependency_dir, 'lib')

    for dep_name in self.get_dependency_configurations():
      if dep_name not in self.ignored_deps:
        d = join(path, dep_name)
        if os.path.exists(d):
          for root, dirs, filenames in os.walk(d):
            filenames = [a for a in filenames if a.endswith(".a")]
            libs.extend([join(root, f) for f in filenames])
    return libs


  def get_include_paths(self):
    includes = []
    includes.append(self.include)
    includes.append(self.private_include)

    if self.root_package:
      includes.append(join(self.root_package.dependency_dir, 'include'))
    else:
      includes.append(join(self.dependency_dir, 'include'))
    return includes

    includes.append(own_include)
    for dep_dir in os.listdir(self.dependency_dir):
      includes.append(join(self.dependency_dir, dep_dir, 'include'))
    return includes


  def get_library_paths(self):
    library_paths = []
    if self.root_package is None:
      library_patths.append(join(self.root_package.dependency_dir, 'lib'))
    return library_paths

  def create_cflags(self):
    cflags = self.traits['cflags'].split()
    if 'cflags' in self.config and 'gcc' in self.config['cflags']:
      cflags += self.config['cflags']['gcc'].split() 

    for variant_dict in self.filtered_variants:
      # We know this is a dict with key == variant_name, value = configuration
      enabled_variant = list(variant_dict.values())[0]
      if 'cflags' in enabled_variant and 'gcc' in enabled_variant['cflags']:
        cflags.append(enabled_variant['cflags']['gcc'])

    for path in self.get_include_paths():
      cflags.append('-I' + path)




    return cflags


  def copy_artifacts(self, dest, headers_only = False):
    src = realpath(join(self.output_dir))
    # Scary magic that occurs because shutil
    # has a cache of directories that where created,
    # so it doesn't recreate the directory structure
    # See:
    # http://stackoverflow.com/questions/9160227/dir-util-copy-tree-fails-after-shutil-rmtree

    def filter_not_headers(f, g):
      return ['lib', 'bin']

    distutils.dir_util._path_created = {}
    if headers_only:
      src = self.output_dir
      dest = dest
      copy_tree(src, dest)
    else:
      copy_tree(src, dest)



  def copy_headers(self):
    #headers = [realpath(join(self.include, f)) for f in os.listdir(self.include) if f.endswith('.h')]

    copy_tree(self.include, self.output_dirs['include'])
    #for header in headers:
    #  dest = join(self.output_dirs['include'])
    #  shutil.copy2(header, dest)


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
    deps = {}

    for variant in self.resolve_variants():
      # Note: the variants have already been resolved
      # This for loop simply needs to resolve the dependencies one
      # by one, potentially overwriding earlier ones
      name, value = next(iter(variant.items()))
      if 'requires' in value and value['requires'] is not None:
        requires = value['requires']
        for req_name, req_config in requires.items():
          deps[req_name] = req_config

    return deps

  def update_traits(self, extra_flags):
    if 'cflags' in self.traits:
      self.traits['cflags'] += " ".join(extra_flags)
    else:
      self.traits['cflags'] = extra_flags

    
  def foreign_build(self):
    build_script = join(self.path, 'build.sh')
    log = join(self.path, 'build_output.txt')
    with temp_cwd(self.path):
      if os.path.exists(build_script):
        print("Running build.sh")
        os.environ['CFLAGS']  + self.traits['cflags']
        print('CFLAGS', self.traits['cflags'])
        os.environ['VERSION'] = self.config['version']
        del os.environ['CC']

        print("VERSION=", self.config['version'])
        args = [build_script]
        bash = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr = bash.communicate()
        del os.environ['CFLAGS']
        del os.environ['VERSION']

        with open(log, 'w') as f:
          print("Writing to {0}".format(log))
          f.write(stdout)

        if bash.returncode !=0:
          raise Exception("Compilation failed. See {0} for details.".format(log))
      pass

  def create_archive(self, descriptor):
    archive_dir = self.get_archive_dir()
    if os.path.exists(archive_dir):
      shutil.rmtree(archive_dir)

    os.mkdir(archive_dir)
    archive_output_dir = join(archive_dir, os.path.split(self.get_output_dir())[1])
    os.mkdir(archive_output_dir)
    # Copy build artifacts
    self.copy_artifacts(archive_output_dir)
    with open(join(archive_dir, 'descriptor.yaml'), 'w') as f:
      yaml.dump(descriptor, f)

  def build(self, extra_flags = ''):

    # Copy headers first, so we can add 
    # output/.../include
    # To allow a package to include it's own header files
    # within header files
    self.copy_headers()
    self.update_traits(extra_flags)
    if 'type' in self.config and self.config['type'] == 'foreign':
      self.form = 'binary'
      return self.foreign_build()

    try:
      self.compile(extra_flags)
    except CompilationError as e:
      #print (str(e))
      raise e
    self.form = 'binary'


  def compile(self, extra_flags):

    source_names = []
    object_names = []

    sources = []
    objects = []


    for variant in self.filtered_variants:
      variant_name = list(variant.keys())[0]
      variant_dir = self.variant_dirs[variant_name]

      # List out sources without full paths so we can create a list of object files
      # separately
      try:
        new_source_names = [f for f in os.listdir(variant_dir) if f.endswith('.c') or f.endswith('.cpp')]
      except OSError:
        print (colored("Directory for variant {0} does not exist".format(variant_name), 'red'))
        new_source_names = []

      new_object_names = [self.change_extension(f, '.o') for f in new_source_names]

      source_names.extend(new_source_names)
      object_names.extend(new_object_names)
    
      # Construct full path names
      new_sources = [os.path.realpath(join(variant_dir, f)) for f in new_source_names]
      new_objects = [os.path.realpath(join(self.path, 'build', f)) for f in new_object_names]

      sources.extend(new_sources)
      objects.extend(new_objects)

    stuff = list(zip(sources, objects))
    cflags = self.create_cflags()
    cflags.extend(extra_flags.split())

    
    if os.getenv('CC'):
      compiler_prefix = os.getenv('CC').split()[0].split('gcc')[0]
    else:
      compiler_prefix = ''
    # If any of the inputs are C++ files,
    # then the final links must be performed by g++, not gcc
    
    final_compiler = 'gcc'
    for source, object in stuff:
      if source.endswith('.c'):
        compiler = 'gcc'
      elif source.endswith('.cpp'):
        compiler = 'g++'
        final_compiler = 'g++'

      if self.config['type'] == 'library':
        args = [compiler_prefix + compiler] + ['-c', '-o', object] + [source] + cflags
      elif self.config['type'] == 'application':
        args = [compiler_prefix + compiler] + ['-c', '-o', object] + [source] + cflags
      
      print("Compiling {0}".format(os.path.split(source)[1]))
      print((colored(" ".join(args), 'yellow')))
      gcc = Popen(args, stdout=PIPE, stderr=PIPE)
      stdout, stderr = gcc.communicate()
      print(stdout)

      if gcc.returncode != 0:
          raise CompilationError(stderr = stderr)

    
    libraries = self.get_static_libraries()
    if self.config['type'] == 'application' or ('variant' in self. traits and
                                                self.traits['variant'] ==
                                                'test'):


      args = [compiler_prefix + final_compiler] +  ['-o', self.binary] + objects + libraries + cflags

      print(colored(" ".join(args), 'yellow'))
      gcc = Popen(args, stdout=PIPE, stderr=PIPE)
      stdout, stderr = gcc.communicate()

      print(stdout)

      if gcc.returncode != 0:
          raise CompilationError(stderr = stderr)

    elif self.config['type'] == 'library':
      print((colored("Linking {0}".format(os.path.split(self.library)[1]),"red")))
      args = [compiler_prefix + 'ld', '-r','-o', self.library] + objects + libraries

      print((colored(" ".join(args), 'yellow')))
      ar = Popen(args, stdout=PIPE, stderr=PIPE)
      stdout, stderr = ar.communicate()
      print(stdout)

      if ar.returncode != 0:
        raise CompilationError(stderr = stderr)

    else:
      raise Exception("Clyde doesn't know how to build type: {0}".format(self.config['type']))

  def __repr__(self):
    return "{0}-{1}".format(self.name, self.config['version'])
    return "Package('{0}')".format(self.path)

  def __hash__(self):
      h = int(stable_sha({'name': self.name, 
                         }), 16)
      return h

  def __eq__(self, other):
    return hash(self) == hash(other)


if __name__ == '__main__':

    if len(sys.argv) > 1:
        p = Package(os.getcwd())
        if sys.argv[1] == 'build':
            p.build()
        elif sys.argv[1] == 'clean':
            p.clean()
    else:
        p = Package('hello')
        p.build()


