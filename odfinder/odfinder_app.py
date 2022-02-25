# -*- coding: utf-8 -*-

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
import argparse
import re
import locale
import zipfile

from subprocess import Popen

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk, Gio, GLib

from .utils import get_ui_resource, remove_xml_markup, get_filename_ext

import gettext
_ = gettext.gettext

__author__ = ['Jose Antonio Chavarría <jachavar@gmail.com>']
__license__ = 'GPLv3'
__copyright__ = f'(C) 2017-2020 {", ".join(__author__)}'

version_file = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'VERSION'
)
if not os.path.exists(version_file):
    version_file = os.path.join(
        sys.prefix,
        'share',
        'doc',
        'odfinder',
        'VERSION'
    )

__version__ = open(version_file).read().strip()


def idle_add_decorator(func):
    def callback(*args):
        GLib.idle_add(func, *args)
    return callback


class ODFinderApp(object):
    APP_DIALOG_ID = 'odfinder'
    APP_NAME = _('Open Document Finder')
    APP_DESCRIPTION = _('Searchs content inside OpenOffice/LibreOffice documents')
    APP_ICON = 'odfinder'

    def __init__(self, options):
        self.stopped = False
        self.cancellable = Gio.Cancellable()
        self.ooo_count = 0
        self.match_count = 0

        self.options = options
        self.console = (self.options['content'] != [])
        if self.console:
            return

        self.builder = Gtk.Builder()
        self.builder.add_from_file(get_ui_resource(f'{self.APP_DIALOG_ID}.ui'))
        self.builder.connect_signals(self)

        self.builder.get_object('lbl_path').set_text(_('Path'))
        self.builder.get_object('lbl_content').set_text(_('Content'))
        self.builder.get_object('lbl_mode').set_text(_('Mode'))

        modes = Gtk.ListStore(str)
        modes.append([_('Or')])
        modes.append([_('And')])
        modes.append([_('Phrase')])
        cbb_mode = self.builder.get_object('cbb_mode')
        cbb_mode.set_model(modes)
        cbb_mode.set_active(0)

        self.matches = Gtk.ListStore(str)
        self.tree_matches = self.builder.get_object('tree_matches')
        self.tree_matches.set_model(self.matches)

        cell_renderer_text = Gtk.CellRendererText()
        tree_view_column = Gtk.TreeViewColumn(_('Matches'))
        self.tree_matches.append_column(tree_view_column)
        tree_view_column.pack_start(cell_renderer_text, True)
        tree_view_column.add_attribute(cell_renderer_text, 'text', 0)

        self.dialog = self.builder.get_object('window1')
        self.dialog.set_icon_name(self.APP_ICON)
        self.dialog.set_title(self.APP_NAME)
        self.dialog.set_position(Gtk.WindowPosition.CENTER)
        self.builder.get_object('btn_stop').set_sensitive(False)
        self.dialog.show_all()

        self.btn_search = self.builder.get_object('btn_search')
        self.btn_search.set_can_default(True)
        self.btn_search.grab_default()
        self.dialog.set_default(self.btn_search)
        self.btn_stop = self.builder.get_object('btn_stop')

        self.builder.get_object('txt_path').set_text(options['path'])
        self.builder.get_object('txt_content').grab_focus()

        self.builder.get_object('txt_path').set_activates_default(True)
        self.builder.get_object('txt_content').set_activates_default(True)

    def on_window1_delete_event(self, *args):
        Gtk.main_quit()

    def on_window1_key_press_event(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.on_window1_delete_event(self)

    def on_btn_exit_clicked(self, widget):
        Gtk.main_quit()

    def on_tree_matches_row_activated(self, tree_view, path, column):
        (model, iter_) = tree_view.get_selection().get_selected()
        Popen(['xdg-open', model[iter_][0]])

    @idle_add_decorator
    def on_btn_stop_clicked(self, widget):
        self.btn_stop.set_sensitive(False)
        self.btn_search.set_sensitive(True)

        self.stopped = True
        self.cancellable.cancel()

    @idle_add_decorator
    def on_btn_search_clicked(self, widget):
        self.ooo_count = 0
        self.match_count = 0

        self.matches.clear()
        path = self.builder.get_object('txt_path').get_text()
        if not os.path.exists(path):
            msg = _('Error: path %s does not exist') % path
            dialog = Gtk.MessageDialog(
                self.dialog, 0, Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK, msg
            )
            dialog.format_secondary_text(_("Ensure path is correct."))
            dialog.run()
            dialog.destroy()
        else:
            self.btn_search.set_sensitive(False)
            self.btn_stop.set_sensitive(True)

            status_bar = self.builder.get_object('sb')
            context = status_bar.get_context_id("example")

            status_bar.push(context, _("Searching in %s...") % path)
            GLib.idle_add(
                self.schedule_search,
                path
            )

    def schedule_search(self, *args):
        Gio.io_scheduler_push_job(
            self.recursive_search,
            args[0],  # path
            GLib.PRIORITY_DEFAULT_IDLE,
            self.cancellable
        )

    @idle_add_decorator
    def on_btn_about_clicked(self, widget):
        about = Gtk.AboutDialog(transient_for=self.dialog)

        about.set_destroy_with_parent(True)
        about.set_program_name(self.APP_NAME)
        about.set_comments(self.APP_DESCRIPTION)
        about.set_version(__version__)
        about.set_icon_name(self.APP_ICON)
        about.set_logo_icon_name(self.APP_ICON)
        about.set_name(__file__)
        about.set_copyright(__copyright__)
        about.set_authors(__author__)

        about.run()
        about.destroy()

    def on_btn_path_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            _("Please choose a folder"),
            self.dialog,
            Gtk.FileChooserAction.SELECT_FOLDER,
            (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                _("Select"),
                Gtk.ResponseType.OK
            )
        )
        dialog.set_default_size(800, 400)
        dialog.set_destroy_with_parent(True)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            txt_path = self.builder.get_object('txt_path')
            txt_path.set_text(dialog.get_filename())
        dialog.destroy()

        self.builder.get_object('txt_content').grab_focus()

    @idle_add_decorator
    def search_completed(self):
        status_bar = self.builder.get_object('sb')
        context = status_bar.get_context_id("example")
        msg = _("%d matches in %d files") % (self.match_count, self.ooo_count)
        status_bar.push(context, msg)

        self.btn_search.set_sensitive(True)
        self.btn_stop.set_sensitive(False)

    @idle_add_decorator
    def search_cancelled(self):
        status_bar = self.builder.get_object('sb')
        context = status_bar.get_context_id("example")
        msg = _("%d matches so far in %d files (search stopped)") % (
            self.match_count,
            self.ooo_count,
        )
        status_bar.push(context, msg)
        self.btn_search.set_sensitive(True)
        self.btn_stop.set_sensitive(False)

    def add_line_to_results(self, line):
        if self.console:
            print(line)
        else:
            self.matches.append([line])

    def match(self, text):
        mode = self.options['mode']
        query = ' '.join(self.options['content'])
        if not self.console:
            mode = self.builder.get_object('cbb_mode').get_active_text()
            query = self.builder.get_object('txt_content').get_text()

        if mode == _("Phrase") or mode == 'phrase':
            # match only documents that contain the phrase
            regex = re.compile(re.escape(query.lower()), re.DOTALL)
            if regex.search(text):
                return True
        else:
            parts = re.split(r"\s+", query.strip())
            if mode == _("And") or mode == 'and':
                # match only documents that contain all words
                for part in parts:
                    regex = re.compile(re.escape(part.lower()), re.DOTALL)
                    if not regex.search(text):
                        return False
                return True
            elif mode == _("Or") or mode == 'or':
                # match documents that contain at least one word
                for part in parts:
                    regex = re.compile(re.escape(part.lower()), re.DOTALL)
                    if regex.search(text):
                        return True
                return False
            else:
                print(_("Error: unknown search mode '%s'") % mode)

        return False

    def process_file(self, filename):
        ext = get_filename_ext(filename)
        try:
            # Handle OpenOffice.org files:
            if ext in (
                'sxw', 'stw',  # OOo   1.x swriter
                'sxc', 'stc',  # OOo   1.x scalc
                'sxi', 'sti',  # OOo   1.x simpress
                'sxg',         # OOo   1.x master document
                'sxm',         # OOo   1.x formula
                'sxd', 'std',  # OOo   1.x sdraw
                'odt', 'ott',  # OOo > 2.x swriter
                'odp', 'otp',  # OOo > 2.x simpress
                'odf',         # OOo > 2.x formula
                'odg', 'otg',  # OOo > 2.x sdraw
                'ods', 'ots',  # OOo > 2.x scalc
            ) and zipfile.is_zipfile(filename):
                zf = zipfile.ZipFile(filename)
                content = ''
                try:
                    archives = zf.namelist()
                    for item in archives:
                        if item.endswith("content.xml"):
                            content += zf.read(item).decode()

                        if item.endswith("document.xml"):
                            content += zf.read(item).decode()

                    content = remove_xml_markup(content)
                    doc_info = remove_xml_markup(zf.read("meta.xml").decode())
                    self.ooo_count += 1
                except KeyError as err:
                    print(_("Warning: %s not found in '%s'") % (err, filename))
                    return None

                return self.match(f'{content.lower()} {doc_info.lower()}')

            # Handle MS-Office (>= 2007) files:
            if ext in (
                'docx', 'dotx',  # MS-Word Documents >= 2007
                'xlsx', 'xltx',  # MS-Excel-Documents >= 2007
            ) and zipfile.is_zipfile(filename):
                zf = zipfile.ZipFile(filename)
                content = ''
                try:
                    archives = zf.namelist()
                    for item in archives:
                        if item.endswith("document.xml"):
                            content += zf.read(item).decode()

                        if item.endswith("sharedStrings.xml"):
                            content += zf.read(item).decode()

                    content = remove_xml_markup(content)
                    doc_info = remove_xml_markup(zf.read("docProps/core.xml").decode())
                    self.ooo_count += 1
                except KeyError as err:
                    print(_("Warning: %s not found in '%s'") % (err, filename))
                    return None

                return self.match(f'{content.lower()} {doc_info.lower()}')

            # Handle MS-Office (>= 2007) MS-PowerPoint files:
            if ext in (
                'pptx',  # MS-PowerPoint-Documents >= 2007
            ) and zipfile.is_zipfile(filename):
                zf = zipfile.ZipFile(filename)
                try:
                    archives = zf.namelist()
                    slides = []
                    for item in archives:
                        if item[4:12] == "slides/s":
                            slides.append(item)

                    content = ''
                    for item in slides:
                        content += zf.read(item).decode()

                    content = remove_xml_markup(content)
                    doc_info = remove_xml_markup(zf.read("docProps/core.xml").decode())
                    self.ooo_count += 1
                except KeyError as err:
                    print(_("Warning: %s not found in '%s'") % (err, filename))
                    return None

                return self.match(f'{content.lower()} {doc_info.lower()}')

        except zipfile.BadZipfile as err:
            print(_("Warning: Supposed ZIP file %s could not be opened: %s") % (filename, str(err)))
        except IOError as err:
            print(_("Warning: File %s could not be opened: %s") % (filename, str(err)))

        return False

    def recursive_search(self, job, cancellable, directory):
        for root, _, files in os.walk(directory):
            for file_ in files:
                if self.cancellable.is_cancelled():
                    self.cancellable.reset()
                    if not self.console:
                        self.search_cancelled()

                    return
                filename = os.path.join(root, file_)
                if self.process_file(filename):
                    self.add_line_to_results(filename)
                    self.match_count += 1

        if not self.console:
            self.search_completed()

    def run(self):
        if self.console:
            self.recursive_search(None, None, self.options['path'])
        else:
            Gtk.main()


def parse_args():
    parser = argparse.ArgumentParser(
        description=ODFinderApp.APP_DESCRIPTION,
    )

    parser.add_argument(
        '-p', '--path',
        action='store',
        help=_('path to search (home by default)'),
        default=os.getenv('HOME'),
    )

    parser.add_argument(
        '-m', '--mode',
        action='store',
        choices=['or', 'and', 'phrase'],
        default='or',
        help=_('search mode (or by default)'),
    )

    parser.add_argument(
        'content',
        nargs='*',  # optional
        action='store',
        help=_('content to search'),
    )

    return vars(parser.parse_args())


def main():
    locale.setlocale(locale.LC_ALL, '.'.join(locale.getdefaultlocale()))
    ODFinderApp(parse_args()).run()


if __name__ == '__main__':
    main()
