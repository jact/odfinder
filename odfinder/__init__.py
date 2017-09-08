# -*- coding: utf-8 -*-

# Copyright (c) 2017 Jose Antonio Chavarría <jachavar@gmail.com>
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

import locale
import gettext
import __builtin__
__builtin__._ = gettext.gettext

LOCALE_PATH = '/usr/share/locale'
DOMAIN = 'odfinder'

gettext.install(DOMAIN, LOCALE_PATH, unicode=1)

gettext.bindtextdomain(DOMAIN, LOCALE_PATH)
if hasattr(gettext, 'bind_textdomain_codeset'):
    gettext.bind_textdomain_codeset(DOMAIN, 'UTF-8')
gettext.textdomain(DOMAIN)

locale.bindtextdomain(DOMAIN, LOCALE_PATH)
if hasattr(locale, 'bind_textdomain_codeset'):
    locale.bind_textdomain_codeset(DOMAIN, 'UTF-8')
locale.textdomain(DOMAIN)

# http://www.ianbicking.org/illusive-setdefaultencoding.html
# begin unicode hack
import sys

if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')
    # now default enconding is 'utf-8' ;)
# end unicode hack
