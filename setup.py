# -*- coding: UTF-8 -*-

# Copyright (c) 2017-2022 Jose Antonio Chavarría <jachavar@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import glob
import subprocess

from setuptools import setup, find_packages
from distutils.command.build import build
from distutils.command.install_data import install_data
from distutils.log import info, error
from distutils.dep_util import newer

PATH = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(PATH, 'README.md'), encoding='utf_8') as f:
    README = f.read()
with open(os.path.join(PATH, 'VERSION'), encoding='utf_8') as f:
    VERSION = f.read().strip()

APP_NAME = 'odfinder'
PO_DIR = 'i18n'
MO_DIR = os.path.join('build', 'mo')

if not hasattr(sys, 'version_info') or sys.version_info < (3, 6, 0, 'final'):
    raise SystemExit(f'{APP_NAME} requires Python 3.6 or later.')


class BuildData(build):
    def run(self):
        build.run(self)

        for po in glob.glob(os.path.join(PO_DIR, '*.po')):
            lang = os.path.basename(po[:-3])
            mo = os.path.join(MO_DIR, lang, f'{APP_NAME}.mo')

            directory = os.path.dirname(mo)
            if not os.path.exists(directory):
                info(f'creating {directory}')
                os.makedirs(directory)

            if newer(po, mo):
                info(f'compiling {po} -> {mo}')
                try:
                    rc = subprocess.call(['msgfmt', '-o', mo, po])
                    if rc != 0:
                        raise Warning(f'msgfmt returned {rc}')
                except Exception as e:
                    error("Building gettext files failed.  Try setup.py \
                        --without-gettext [build|install]")
                    error(f'Error: {e}')
                    sys.exit(1)


class InstallData(install_data):
    @staticmethod
    def _find_mo_files():
        data_files = []

        for mo in glob.glob(os.path.join(MO_DIR, '*', f'{APP_NAME}.mo')):
            lang = os.path.basename(os.path.dirname(mo))
            target = os.path.join('share', 'locale', lang, 'LC_MESSAGES')
            data_files.append((target, [mo]))

        return data_files

    def run(self):
        self.data_files.extend(self._find_mo_files())
        install_data.run(self)


setup(
    name=APP_NAME,
    version=VERSION,
    packages=find_packages(),
    data_files=[
        ('share/odfinder/ui', [
            'data/ui/odfinder.ui',
        ]),
        ('share/doc/odfinder', [
            'AUTHORS',
            'INSTALL',
            'LICENSE',
            'README.md',
            'VERSION',
        ]),
        ('share/applications', ['data/odfinder.desktop']),
        ('share/icons/hicolor/scalable/apps', ['data/img/odfinder.svg']),
    ],
    cmdclass={
        'build': BuildData,
        'install_data': InstallData,
    },
    author='Jose Antonio Chavarría',
    author_email='jachavar@gmail.com',
    license='GPLv3',
    url='https://github.com/jact/odfinder',
    platforms=['Linux'],
    description='Searchs content inside OpenOffice/LibreOffice documents',
    long_description=README,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: X11 Applications :: Gnome',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Utilities',
        'Topic :: Desktop Environment :: Gnome',
        'Topic :: Office/Business :: Office Suites',
    ],
    entry_points={
        'console_scripts': [
            'odfinder=odfinder.command_line:main'
        ],
    },
)
