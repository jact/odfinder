# -*- coding: utf-8 -*-

# Copyright (c) 2017-2026 Jose Antonio Chavarría <jachavar@gmail.com>
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
import re
import sys

_RE_COMMENTS = re.compile('<!--.*?-->', re.DOTALL)
_RE_TAGS = re.compile('<[^>]*>', re.DOTALL)

_PKG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_ui_resource(name):
    installed = os.path.join(sys.prefix, 'share', 'odfinder', 'ui', name)
    if os.path.exists(installed):
        return installed

    return os.path.join(_PKG_DIR, 'data', 'ui', name)


def remove_xml_markup(s, replace_with_space=False):
    s = _RE_COMMENTS.sub('', s)
    s = _RE_TAGS.sub(' ' if replace_with_space else '', s)
    return s


def get_filename_ext(filename):
    _, ext = os.path.splitext(filename)
    return ext.lstrip('.').lower()
