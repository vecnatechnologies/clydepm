from setuptools import setup, find_packages

def readme():
    with open('README.rst') as f:
        return f.read()

options = {
    'name'                          :   'clydepm',
    'description'                   :   'Clyde C/C++ Package Manager',
    'long_description'              :   readme(),
    'url'                           :   'https://git.crl.vecna.com/#/admin/projects/firmware/tools/python/clydepm',
    'author'                        :   'Isaac Gutekunst',
    'author_email'                  :   'isaac.gutekunst@vecna.com',
    'license'                       :   'Property of Vecna Technologies, Inc.',
    'packages'                      :   find_packages(),
    'install_requires'              :   ['gitpython', 
                                         'pyyaml', 
                                         'colorama', 
                                         'termcolor', 
                                         'configparser',
                                         'unidecode',
                                         'graphviz',
                                         'pygerrit',
                                         'pygments',
                                         'semantic_version',
                                         'Jinja2',
                                         'ninja'
                                        ],
    'zip_safe'                      :   True,
    'package_data'                  :   {'clydepm': ['templates/*.*'] },
    'version'                       :   '0.2.38',
    'test_suite'                    :   'nose.collector',
    'tests_require'                 :   ['nose'],
    'entry_points'                  :   {
        'console_scripts'           :   [ 
            'clyde=clydepm.command_line:main',
            'clyde2=clyde2.command_line:main'
        ]
    }
}

setup(**options)
