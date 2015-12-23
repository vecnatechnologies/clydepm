from .common import stable_sha, temp_cwd
from os.path import splitext, join, realpath
import os
import tarfile
from git import Repo
from .package import Package
from subprocess import Popen, PIPE
import getpass
from termcolor import colored

class PackageServer(object):
  """
  Base class for package servers.

  Package servers are responsible for furnishing tar.gz files
  given a package descriptor.

  They can do so using any technique.

  If a PackageServer has a build step, in the case of
  the current iteration of LocalForeignPackageServer, it is 
  expected that the server maintains a cache of the build artifacts, though not 
  required.

  After a build has completed, it is acceptable for a PackageServer to flush 
  it's cache.
  
  """
  def __init__(self, root_directory):
    if root_directory is None:
      self.root_directory = os.getcwd()
    else:
      self.root_directory = root_directory
    self.git_directory     = realpath(join(self.root_directory, 'git'))
    self.package_directory = realpath(join(self.root_directory, 'packages'))

    to_create = [self.git_directory, self.package_directory]

    for d in to_create:
        if not os.path.exists(d):
            print(("Creating {0}".format(d)))
            os.makedirs(d)


  def make_tarfile(self, output_filename, source_dir, base='./'):
    """
    Helper function that creates a tarball named output_filename
    from a directory named source_dir.

    The contents of source_dir will be placed inside a directory
    called base inside of the tarball.
    """

    with tarfile.open(output_filename, "w:gz") as tar:
      for f in os.listdir(source_dir):
        if f != '.git':
          path = join(source_dir, f)
          tar.add(path, arcname=join(base, f) )

class LocalGitPackageServer(PackageServer):
  """
  a LocalGitPackgeServer exports tarballs 
  from a directory of git projects.

  It looks for git projects in 

  {git_directory}

  It places tarball exports in 

  {package_directory}

  """

  def __init__(self, root_directory):
    PackageServer.__init__(self, root_directory)


  def checkout_tag(self, repo, spec):
    
    commit = repo.commit(spec)
    if commit:
      repo.head.reference = commit
      repo.head.reset(index = True, working_tree=True)
    else:
      raise Exception("Tag {0} not found".format(tag))

  def checkout_remote_repo(self, repo_path):
    name = os.path.split(repo_path)[1]
    with temp_cwd(self.git_directory):
      args = ['git','clone', repo_path]
      git = Popen(args, stdout=PIPE, stderr=PIPE)
      stdout, stderr = git.communicate()
      if git.returncode == 0:
        return True
      return False

  def checkout_remote_project(self, project_name):
    username = getpass.getuser()
    base_url = 'ssh://{0}@git.crl.vecna.com:29418/clyde/packages/{1}'.format(username,
                                                                  project_name)
    print((colored('Checking out {0}'.format(base_url),'green')))
    return self.checkout_remote_repo(base_url)

  def get_package_tarball_by_descriptor(self, descriptor):
    """
    Given a python dictionary describing a package, attempt to
    retrieve it from the local git cache. This is accomplished
    by looking in {git_directory} and 
    attempting to checkout the GIT_REFSPEC

    This method only supports source packages

    """
    if descriptor['form'] != 'source':
        return None
    hash = stable_sha(descriptor)
    package_paths = [d for d in os.listdir(self.git_directory) ]
    name = descriptor['name']

    package_tar_name = join(self.package_directory, hash + '.tar.gz')
    package_version =  descriptor['version']

    if name in package_paths:
      pass
    else:
      if not self.checkout_remote_project(name):
        raise Exception("failed to checkout")


    # TODO make this export from a git repo
    path = join(self.git_directory, name)
    repo = Repo(path)
    self.checkout_tag(repo, package_version)
    # There is a potential race condition if multiple builds
    # Require different versions of git dependency and try to get 
    # it simultaneously
    self.make_tarfile(package_tar_name, path, hash)
    return package_tar_name




class LocalForeignPackagerServer(PackageServer):

  def __init__(self, root_directory):
    PackageServer.__init__(self, root_directory)
    
    self.foreign_package_directory = self.package_directory
    self.package_directory = join(self.root_directory, 'compiled-packages') 

  def foreign_build(self, path, descriptor):
    package = Package(path, form = 'source', traits = descriptor['traits']) 
    package.build()
    descriptor['form'] = 'binary'
    package.create_archive(descriptor)
    return package

  def get_package_tarball_by_descriptor(self, descriptor):
    """
    Given a python dictionary describing a package, attempt to
    retrieve it from the local foreign package cache
    
    It only supports binary form for now, as it runs a the 
    build.sh which is responsible for checking out and building 
    the package

    TODO/Thoughts

    It might make sense to support source form as well. In this case,
    there would be some process for retrieving the source, and furnishing
    a build.sh that can be used to build a foreign package.

    If we restrict ourselves to git, we can checkout/clone the correct 
    version of the foreign source, and then copy the build.sh from the 
    package.

    In this case, a foreign package would consist of a config.yaml, 
    specifying the remote git URL, + instructions to build once a 
    version had been checked out. However, we now get into the fun
    game of supporting slightly different build.sh files for new versions
    of a package. 

    RTEMS Source builder supports this by having a package descriptor, and a 
    per-version package descriptor that has customized build instructions.

    We can also re-package packages in clyde form if necessary, but that could
    get ugly though.

    """
    if descriptor['form'] != 'binary':
        return None
    hash = stable_sha(descriptor)
    if not os.path.exists(self.foreign_package_directory):
        return None
    package_paths = [d for d in os.listdir(self.foreign_package_directory) ]
    name = descriptor['name']

    package_tar_name = join(self.package_directory, hash + '.tar.gz')
    package_version =  descriptor['version']

    if os.path.exists(package_tar_name):
        return package_tar_name

    if name in package_paths:
      # TODO make this export from a git repo
      path = join(self.foreign_package_directory, name)
      package = self.foreign_build(path, descriptor)
      hash = stable_sha(descriptor)
      self.make_tarfile(package_tar_name, package.get_archive_dir(), hash)
      return package_tar_name


