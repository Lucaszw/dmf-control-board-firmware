from pprint import pprint

from paver.easy import task, needs, path, sh, cmdopts, options
from paver.setuputils import setup

import os
import sys

# add the current directory as the first listing on the python path
# so that we import the correct version.py
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import version

DEFAULT_ARDUINO_BOARDS = ['mega2560']

setup(name='wheeler.dmf-control-board-firmware',
      version=version.getVersion(),
      description='Arduino-based DMF control board firmware and Python API.',
      author='Ryan Fobel and Christian Fobel',
      author_email='ryan@fobel.net and christian@fobel.net',
      url='https://github.com/wheeler-microfluidics/dmf-control-board-firmware',
      license='GPLv2',
      packages=['dmf_control_board_firmware'],
      include_package_data=True,
      install_requires=['arduino_helpers>=0.3.post10', 'arduino-scons',
                        'decorator', 'functools32', 'matplotlib',
                        'microdrop-utility', 'scipy', 'serial_device>=0.3',
                        'svg-model>=0.5.post20', 'sympy', 'tables',
                        'wheeler.base-node>=0.3.post2', 'pandas>=0.17',
                        'arrow'],
      extras_require={'build': ['arduino-scons>=v0.1.post11', 'SCons>=2.4.1']})


@task
def create_config():
    sketch_directory = path('dmf_control_board_firmware').joinpath('src',
                                                          'dmf_control_board')
    sketch_directory.joinpath('Config.h.skeleton').copy(sketch_directory
                                                        .joinpath('Config.h'))


@task
def nosetests():
    nose_options = '-v'
    sh('nosetests %s' % nose_options)


@task
@needs('create_config')
@cmdopts([('sconsflags=', 'f', 'Flags to pass to SCons.'),
          ('boards=', '', 'Comma-separated list of board names to compile '
           'for (e.g., `mega2560`).')])
def build_firmware():
    scons_flags = getattr(options, 'sconsflags', '')
    boards = [b.strip() for b in getattr(options, 'boards', '').split(',')
              if b.strip()]
    if not boards:
        boards = DEFAULT_ARDUINO_BOARDS
    for board in boards:
        # Compile firmware once for each specified board.
        sh('scons %s ARDUINO_BOARD="%s"' % (scons_flags, board))


@task
@needs('generate_setup', 'minilib', 'build_firmware', 'nosetests',
       'setuptools.command.sdist')
def sdist():
    """Overrides sdist to make sure that our setup.py is generated."""
    pass


@task
@needs('generate_setup', 'minilib', 'build_firmware', 'nosetests',
       'setuptools.command.bdist_wheel')
def bdist_wheel():
    """Overrides bdist_wheel to make sure that our setup.py is generated."""
    pass
