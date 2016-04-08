class CompilerException(Exception):
  pass

class Tools(object):
  COMPILER  = 0
  LINKER    = 1
  ARCHIVER  = 2

class Compilers:
  GCC = 0

class Compiler(object):

  def __init__(self, 
               compiler = '', 
               build_dir = None,
               compiler_type = Compilers.GCC):
    if compiler.endswith('gcc'):
      self.compiler_type = Compilers.GCC
      self.prefix = compiler.split('gcc')
      self.source_files = []
    else:
      raise CompilerException("We only support gcc at this point")


  def add_source_file(self, file):
    self.source_files.append(file)

  def add_include_path(self, path):
    pass

  def add_flags(self, flags):
    pass

  def add_static_library(self, path):
    pass

  def build_executable(self):
    pass
  
  def build_static_library(self):
    pass

if __name__ == '__main__':
  c = Compiler('arm-rtems4.11-gcc')
