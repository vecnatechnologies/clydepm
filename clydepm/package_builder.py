from .package import Package, EmptyPackage
import os
import sys
import hashlib
import shutil
import yaml
from os.path import splitext, join, realpath
from .common import stable_sha, list_contains
from .git_package_server import LocalGitPackageServer, LocalForeignPackagerServer
import tarfile
from distutils.dir_util import copy_tree
import pprint
from graphviz import Digraph

pp = pprint.PrettyPrinter(indent=4)


class PackageBuilder(object):
  """
  A package server maintains a database that stores packages in 
  various forms. Currently supported forms are binary and source.
  
  Package versions are specified as GIT_RESPEC, with a few keywords
  reserved for special purposes. In future versions of this server,
  the versioning system may include other methods for retrieving packages
  that don't actually use the version as  GIT_REFSPEC directly.
  
  Right now, local is a reserved version name used to indicate 
  a package should be retrieved from a locally accessible directory
  rather than specifying a specific version.

  In addition, packages have various traits (usually only for binary forms),
  that represent how the package was actually built.


  To support caching and remote repositories, a package server can
  have references to upstream PackageServers, so that if a package
  cannot be retrieved locally, it can be retrieved remotely.

  For binary packages, the search order is as follows:

    Local cache
    Remote cache
    Local source cache and build
    Remote source cache retrieve, and build from local cache

  For source packages, the search is:
    Local source cache Remote source cache

  Note, there really isn't a difference from cache and source cache.

  The only difference is form of the requested package


  """
  def __init__(self, configuration):
    self.u = Digraph('unix', filename='build.gv')
    self.counter = 1
    self.u.body.append('size="6,6"')
    self.u.node_attr.update(color='lightblue2', style='filled')


    self.root_package = None

    self.build_trace = []
    package_root = configuration['General']['package-root']
    git_root     = configuration['General']['git-root']

    self.configuration = configuration

    if package_root is None:
      self.root_directory = realpath(os.getcwd())
    else:
      self.root_directory = realpath(package_root)

    if git_root is None:
      self.local_git = LocalGitPackageServer(join(self.root_directory, 'git-server'))
    else:
      self.local_git = LocalGitPackageServer(git_root)

    self.all_deps = set()


    self.package_servers = [self.local_git]

    self.package_directory = join(self.root_directory, '.packages')

    if not os.path.exists(self.package_directory):
      os.makedirs(self.package_directory)

  def store_tarball(self, tarball_path):
    """
    Extract and store a tarball in local cache
    """

    if tarball_path.endswith('.tar.gz'):
      sha = os.path.split(tarball_path.replace('.tar.gz', ''))[1]
      path = join(self.package_directory, sha) 
      with tarfile.open(tarball_path) as tar:
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(tar, self.package_directory)
    else:
      raise Exception("store_tarball not passed .tar.gz file")

  def flush(self):
    print ("Deleting local cache first")
    print ("\tDeleting {0}".format(self.package_directory))
   
    if os.path.exists(self.package_directory):
        shutil.rmtree(self.package_directory)
    
    print ("Deleting all upstream caches")
    for server in self.package_servers:
        server.flush()
    
  def create_new_package(self, new_package_directory, package_type):

    Package.create_new_package(new_package_directory, 
                               package_type,
                               self.configuration)
  
  def store_package(self, package, descriptor):
    descriptor_for_hashing = descriptor.copy()
  
    #TODO
    # Think whether htis is a hack.
    # When you build a package, you don't want to have to 
    # enumerate it's dependencies, but you want to know what 
    # they are when linking to abvoid multiple definitions
    if 'dependencies' in descriptor_for_hashing:
      del descriptor_for_hashing['dependencies']
    path  = join(self.package_directory, stable_sha(descriptor_for_hashing))

    if os.path.exists(path):
      print ("Overwriting existing package!")

    # Copy from archive_dir to path
    #print "Copying {0} -> {1}".format(package.get_archive_dir(), path)
    copy_tree(package.get_archive_dir(), path)



  def get_package_by_descriptor(self, descriptor, clean = False):
    """
    Given a python dictionary describing a package, retrieve 
    it using whatever techniques are necessary.

    This may require building the package, and recursively 
    retrieving all the dependencies

    """
    self.build_trace.append(descriptor['name'])
    
    hash = stable_sha(descriptor)
    all_dependencies = []
    # packages are stored in root/.packages/


    package_paths = [d for d in os.listdir(self.package_directory)]
    name = descriptor['name']

    if descriptor['version'] == 'local':
      pass

    elif hash not in package_paths:
      hash = stable_sha(descriptor)  
      if hash not in package_paths:
        for server in self.package_servers:
          package_tarball_path = server.get_package_tarball_by_descriptor(descriptor)
          if package_tarball_path:
              self.store_tarball(package_tarball_path)
              break
        if package_tarball_path is None:
          for server in self.package_servers:
            descriptor['form'] = 'source'
            package_tarball_path = server.get_package_tarball_by_descriptor(descriptor)
            if package_tarball_path:
                self.store_tarball(package_tarball_path)
                break
          if package_tarball_path is None:
            raise Exception("Failed to find package {0} anywhere".format(name))
      else:
        print(("Found {0} sources locally".format(name + '-' +
                                                 descriptor['version'])))

    else:
      pass

    # If the binary package didn't exist, the descriptor might be changed.
    # Rebuild the sha

    if descriptor['version'] == 'local':
      package_path = descriptor['local-path']
      descriptor['form'] = 'source'
    else:
      hash = stable_sha(descriptor)  
      package_path = join(self.package_directory, hash)

    package = Package(package_path, descriptor['form'], descriptor['traits'],
                      self.root_package)

    if self.root_package is None:
      self.root_package = package

    if clean:
        package.clean()
        return
    if package:
      form = descriptor['form']
        
      if form == 'source':
        # Make a copy of the parent descriptor
        parent_descriptor = descriptor.copy()
        dependencies = self.get_package_dependencies(package, parent_descriptor) 
        for d in dependencies:
          if not self.dep_satisfied(d):
            self.u.edge(str(package), str(d), label = str(self.counter))
            self.counter += 1
            d.copy_artifacts(self.root_package.get_dependency_dir(), False)
            self.all_deps.add(d)
          else:
            package.ignore_dependency_by_name(d.name)
            pass
            #e = self.u.edge(str(package), str(d), color="orange", label =
            #               str(self.counter))
            #self.counter +=1
            #print ("Already have {0}. Copying headers only".format(d.name))
            #d.copy_artifacts(package.get_dependency_dir(), True)
        
        print(("Building {0}-{1}".format(package.config['name'],
                                       package.config['version'])))
        package.copy_artifacts(self.root_package.get_dependency_dir(), True)
        package.build()
        descriptor['form'] = package.get_form()
        descriptor['dependencies'] = package.get_dependency_configurations()
        package.create_archive(descriptor)
        self.store_package(package, descriptor)

      elif form =='binary':
        print(("Package {0}-{1} already built".format(descriptor['name'],
                                                      descriptor['version'])))

        package.copy_artifacts(self.root_package.get_dependency_dir(), True)

        if 'dependencies' in package.config:
          for name, options in package.config['dependencies'].items():
            d = EmptyPackage(name, options['version'])
            if not self.dep_satisfied(d):
              self.all_deps.add(d)
              e = self.u.edge(str(package), str(d), color="red", label =
                              str(self.counter))
              self.counter += 1
            else:
              e = self.u.edge(str(package), str(d), color="orange", label = str(self.counter))


      self.build_trace.pop()
      return package
         
    else:
      print ("Failed to retrieve package")

  def get_package_dependencies(self, package, parent_descriptor):
    """
    Look through dependencies, and construct package 
    description needed to retrieve each package. Then go ahead
    and get those packages, potentially causing some more recursion
    
    """
    packages = []
    parent_descriptor['requires'] = package.get_dependency_configurations()
    for dep_name, dep_config in package.get_dependency_configurations().items():
      
      descriptor = self.make_package_descriptor(package, parent_descriptor,
                                                dep_name)

      package = self.get_package_by_descriptor(descriptor)
      packages.append(package)
    return packages

  def make_package_descriptor(self, package, parent_descriptor, dep_name):

    traits = package.get_traits()
    if 'variant' in traits:
        del traits['variant']
    descriptor = {
      'name'          : dep_name,
      'version'       : parent_descriptor['requires'][dep_name]['version'],
      'form'          : 'binary',
      'traits'        : traits
    }

    if descriptor['version'] == 'local':
      try:
        local_path = parent_descriptor['requires'][dep_name]['local-path']
      except KeyError as k:
        raise Exception("Please add a local-path option for all local dependencies")
      #local_path = realpath(join(package.get_path(), local_path))
      descriptor['local-path'] = local_path
    descriptor['traits']['cflags'] = parent_descriptor['traits']['cflags']
    #print("pt", parent_descriptor)
    # Copy all the elements from the dep_config
    # into the descriptor (name, version, local-path, base-version)
    return descriptor


  def dep_satisfied(self, new_dep):
    if new_dep in self.all_deps:
      return True
    return False

  def build_package_by_description(self, descriptor):
    pass


  def build_package(self, package):
    pass


