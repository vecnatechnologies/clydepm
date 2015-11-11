Clyde Package Manager
=====================


Clyde is a simple package manager and build system for C and C++ projects.


Key Concepts
------------

Package Descriptors
~~~~~~~~~~~~~~~~~~~

Every package can be described by a handful of key attributes.The set of attributes fully describe the package as a potential dependency. The package builder can be asked to produce a package given a descriptor, and will try to provide this package drawing from a list of package servers, compiling the package if necessary.

Here is an example descriptor, notated in yaml::

    form: binary
    name: cpputest
    traits: {cflags: ' -O2', compiler: gcc, compiler-version: 4.8.4}
    version: v3.7.1

The describes a package that has been compiled by gcc 4.8.4 with the flags -O2, version v3.71.

These attributes uniquely identify this package so it can be saved, and later retrieved using these parameters.

We can ask the Package Builder for a package matching this descriptor, and assuming it can, it will generate a 'package', which is simply a directory with a certain structure, with the properties described in the descriptor.


Tutorial
--------

Basic Hello World
~~~~~~~~~~~~~~~~~

1. Create a new directory to hold your new clyde package and change into it::

    mkdir my-application
    cd my-package
2. Initialize a new clyde application project::

    clyde init application
3. Notice the created directory structure. There is now a src, include, private_include and config.yaml

4. Make a new c file src/hello.c, for example::

    src/hello.c
    #include <stdio.h>
     
    int main(int argc, char * argv[]) {
        printf("Hello World\n");
        return 0;
    }

5. Build it with the default gcc compiler::

    clyde make

    Try running it
    clyde run
    # You can also manually run the file 
    ./output/my-application/my-application-0.0.1.out (Exact name may vary) 


Adding Dependencies
~~~~~~~~~~~~~~~~~~~

Let's discuss directory structure for a second. Let's say you put the previous example in ~ (HOME). Let's make a clyde package directory to store many clyde packages for the next few tutorials

1. Make a new directory for clyde packages. Copy the previous example (my-application) into it. Your directory structure should look like::

    clyde-packages / my-application

2. Change into your clyde packages folder and make a new directory for a dependency::

    cd clyde-packages
    mkdir my-library

3. Initialize a new clyde library project in this directory::

    cd my-dependency
    clyde init library

4. Create a library function e.g.::

    //include/my-library.h
    #ifndef MY_LIBRARY_H
    #define MY_LIBRARY_H
     
    const char * MyLibrary_getHelloText(void);
    #endif
     
    //src/my-library.c
    #include <my-library.h>
     
    const char * MyLibrary_getHelloText(void) {
        return "Hello from my-library\n";
    }

5. Try compiling it::

    clyde make


6. Let's set this up as a dependency for my-application. Edit config.yaml to include a dependency. It should look something like this::
    
        author: Isaac Gutekunst
        author-email: isaac.gutekunst@vecna.com
        cflags: {gcc: --std=c99} desc: |
            This package demonstrates the basic features of the clyde package manager.
            It now supports printing text generated from a static library that is
            automatically linked
        name: my-application
        type: application
        url: http://wiki.vecna.com
        version: 0.0.1
        dependencies:
            a:
                version: local
                local-path: ../my-library

7. Try building my-application again::

    clyde build
    # It might not do anything, so clean
    clyde clean
    clyde make

8. Now edit your main application to use the dependent application ::

    #include <stdio.h>
    #include <my-library/my-library.h>
     
    int main(int argc, char * argv[]) {
        printf("Hello World\n");
        printf("%s", MyLibrary_getHelloText());
        return 0;
    }
9.  Rebuild again with clyde make


Advanced Concepts
-----------------

Package Repositories
~~~~~~~~~~~~~~~~~~~~

Clyde has a cascading method for retrieving packages. It will first look in a local cache (defaults to ~/.clyde/packages), and then in a local git package manager (~/.clyde/git).


A local repository contains a cache of compiled pacakges, as well as a cache of specific source distributions.
You should not every worry about how it works, and it's  directory structure will change.
If you ever feel you need to delete the cache, it contains a .packages directory with many tarballs. Delete all of these to get rid of your local cache of packages.

A local git repository (this is slightly misleading) is a folder containing git repositories.
It contains a *git* and a *packages* directory. The git directory should contain get repositories named indentically to the packages they provide. For example, if you have a package matrix-math hosted on github or gerrit, you should perform a git clone in the git directory so as to have a matrix-math directory inside of the git directory.::

   tree $GIT_DIRECTORY -L 2
    .
    |-- git
    |   |-- package-a
    |   |-- package-b
    |   `-- matrix-math
    `-- packages
        |-- 025664ab75adbfca818ca4ce21602d8bcb1325a9.tar.gz
        .
        .
        .
        |-- f62322d7cca9d8c4ec4939312ece038d0bc64ad8.tar.gz
        `-- f7a55f2369e7c45cc62df98dbab4c4b163ebdc2b.tar.gz


Configuration
-------------

Clyde has a very basic configuration system. It searches for configuration in the following order
    
    * Internal defaults
    * /etc/clyde/config
    * ~/.clyde/config
    * $PWD/.clyde/config

Later config files override earlier ones, so you can have a system wide, per user, and per package configuration.

**Example Config File**::
    
   [General]
   package-root=/other/firmware/server-root/
   git-root=/other/firmware/server-root/git-server/
   user.name=Isaac Gutekunst
   user.email=isaac.gutekunst@vecna.com

**Available Options**
    +------------------+----------------------------------------------+
    | *package-root*   | Location for local package server files      |
    +------------------+----------------------------------------------+
    | *git-root*       | Location for git package server files        |
    +------------------+----------------------------------------------+
    | *user.name*      | Default user name when creating new packages |
    +------------------+----------------------------------------------+
    | *user.email*     | Default email when creating new package      |
    +------------------+----------------------------------------------+

 




