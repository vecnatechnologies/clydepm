from ninja.ninja_syntax import Writer
import StringIO
from sys import stdout
from os.path import join, splitext, relpath, split
import os
from clyde2.common import is_c, is_cpp
from clyde2.common import pprint_color, dict_contains

from clyde2.rtems import *

def generate_toolset(writer, 
                     prefix = '', 
                     toolchain = None, 
                     rtems_makefile_path = None):
  cflags = ' -DSTM32F7_DISCOVERY'
  if rtems_makefile_path:
    flags = get_flags_dict(rtems_makefile_path)
    flags['cflags'] += cflags
    toolchain = {
      'cc'      : prefix + 'gcc -MMD -MF $out.d ' + \
                  '{cflags} {cpu_cflags} $cflags -c $in -o $out {link_libs}'.format(**flags),

      'cpp'     : prefix + 'g++ -MMD -MF $out.d ' +\
                  '{cflags} {cpu_cflags} $cflags -c $in -o $out {link_libs}'.format(**flags),

      'main'    : prefix + 'g++ -MMD -MF $out.d ' +\
                  '{bsp_specs} $cflags {cflags} {cpu_cflags} $in -o $out {link_libs}'.format(**flags),
      'as'      : prefix + 'as',
      'ar'      : prefix + 'ar',
      'ranlib'  : prefix + 'ranlib',
      'ld'      : prefix + 'ld',
      'link'    : prefix + 'ld $ldflags -r -o $out $in'
    }
  if not toolchain:

    toolchain = {
      'cc'      : prefix + 'gcc -MMD -MF $out.d {0} $cflags -c $in -o $out'.format(cflags),
      'cpp'     : prefix + 'g++ -MMD -MF $out.d {0} $cflags -c $in -o $out'.format(cflags),
      'main'    : prefix + 'g++ -MMD -MF $out.d $cflags $in -o $out',
      'as'      : prefix + 'as',
      'ar'      : prefix + 'ar',
      'ranlib'  : prefix + 'ranlib',
      'ld'      : prefix + 'ld',
      'link'    : prefix + 'ld $ldflags -r -o $out $in'
    }

  if rtems_makefile_path and False:
    final_link_flags = get_rtems_link_flags(rtems_makefile_path)
    final_link_libs =  get_rtems_link_libs(rtems_makefile_path)
    toolchain['main'] = \
      prefix + 'g++ $ldflags {0} -r -o $out $in {1}'.format(final_link_flags,
                                                            final_link_libs)


  writer.comment("Tool Definitions")
  for name, command in toolchain.iteritems():
    writer.rule(name, 
                command, 
                depfile = '$out.d')
                
    writer.newline()
  # Symlink magic
  writer.rule('symlink', 'ln -s ../../$in $out')

def local(path, root = None):
  if not root:
    root = os.getcwd()
  return relpath(path, root)

def newext(file, ext):
  if not ext.startswith('.'):
    ext = '.' + ext
  return splitext(file)[0] + ext

def build_location(file, root):
  name = split(split(local(file, root))[0])[1]
  name = join('prefix', 'include', name)
  return name

def make_cflags(name, info, root):
  out = []
  for include in info['include']:
    #out.append('-I' + build_location(include, root))
    out.append('-I' + include) 

  out.append(info['cflags'])
  out.append('-I' + join('deps', name, 'include'))
  return " ".join(out)


generated = set()
linked = set()


def generate_library_entries(w, node, info, root, top = False):
  if info['name'] in generated:
    return
  else:
    generated.add(info['name'])
  
  w.newline()
  w.comment("Library {0} sources".format(node))
  # Handle all the source files in this package
  objects = []
  if len(info['sources']) == 0:
      raise Exception("You don't have any source files in src")
  for source in info['sources']:
    source = local(source, root)
    object = join('build', newext(source, '.o'))
    objects.append(object)
    
    vars = {
      'cflags': make_cflags(node, info, root)
    }

    if top:
      vars['cflags'] += ' -Iinclude'

    if is_c(source):
      w.build(object, 'cc', source, variables = vars)
    elif is_cpp(source):
      w.build(object, 'cpp', source, variables = vars)
    else:
      raise Exception("Weird source file got through")


  w.newline()
  w.comment("Create the {0} library".format(node))

  libs = []
  for library in info['libraries'].keys():
    libname = library + '.a'

    if libname not in linked:
      libs.append(libname)
      linked.add(libname)

  if info['type'] == 'library':
    tool = 'link'
  elif info['type'] == 'application':
    tool = 'main'
  else:
    raise Exception("Error in clyde config: type is not library or application")

  w.build(outputs = 'prefix/lib/' + node + '.a', 
          rule = tool, variables = vars,
          inputs = ['prefix/lib/' + l for l in libs] + objects
         )

  if not top:
    if False:
        w.build(outputs = 'prefix/include/' + node,
                rule = 'symlink',
                inputs = 'deps/' + node + '/include')

  for library, contents in info['libraries'].iteritems():
    generate_library_entries(w, library, contents, root, top = False)




def generate_file(tree, prefix = '', 
                  toolchain = None, 
                  root = None, 
                  cflags = None,
                  rtems_makefile_path = None):
  output = StringIO.StringIO()
  w = Writer(output)

  generate_toolset(w, prefix = prefix, 
                   toolchain = toolchain,
                   rtems_makefile_path = rtems_makefile_path)
  w.newline( )
  w.comment("Global flags")

  for node, info in tree.iteritems():
    
    generate_library_entries(w, node, info, root, top = True)
    
      


  return output.getvalue(), tree



#TODO 
# Fix problem where symlinks are not required by any other target
