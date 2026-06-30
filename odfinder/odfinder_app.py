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

import argparse
import locale
import os
import re
import sys
import zipfile
from subprocess import Popen

import gi

gi.require_version('Gdk', '4.0')
gi.require_version('Gtk', '4.0')

import gettext  # noqa: E402

from gi.repository import Gdk, Gio, GLib, Gtk  # noqa: E402

from .utils import get_filename_ext, get_ui_resource, remove_xml_markup  # noqa: E402

_ = gettext.gettext

__author__ = ['Jose Antonio Chavarría <jachavar@gmail.com>']
__license__ = 'GPLv3'
__copyright__ = f'(C) 2017-2026 {", ".join(__author__)}'

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

with open(version_file, encoding='utf_8') as f:
    __version__ = f.read().strip()


def idle_add_decorator(func):
    def callback(*args):
        def wrapper(*wargs):
            func(*wargs)
            return False
        GLib.idle_add(wrapper, *args)
    return callback


class ODFinderApp(Gtk.Application):
    APP_DIALOG_ID = 'odfinder'
    APP_NAME = _('Open Document Finder')
    APP_DESCRIPTION = _('Searchs content inside OpenOffice/LibreOffice documents')
    APP_ICON = 'odfinder'

    def __init__(self, options):
        super().__init__(application_id='org.gnome.odfinder')
        self.stopped = False
        self.cancellable = Gio.Cancellable()
        self.ooo_count = 0
        self.match_count = 0
        self.warnings = []

        self.options = options
        self.console = (self.options['content'] != [])

    def do_activate(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(get_ui_resource(f'{self.APP_DIALOG_ID}.ui'))

        self.builder.get_object('lbl_path').set_text_with_mnemonic(_('_Path'))
        self.builder.get_object('lbl_content').set_text_with_mnemonic(_('C_ontent'))
        self.builder.get_object('lbl_mode').set_text_with_mnemonic(_('_Mode'))

        cbb_mode = self.builder.get_object('cbb_mode')
        cbb_mode.append_text(_('Or'))
        cbb_mode.append_text(_('And'))
        cbb_mode.append_text(_('Phrase'))
        cbb_mode.set_active(0)

        self.matches = Gtk.ListStore(str)
        self.tree_matches = self.builder.get_object('tree_matches')
        self.tree_matches.set_model(self.matches)

        cell_renderer_text = Gtk.CellRendererText()
        tree_view_column = Gtk.TreeViewColumn(title=_('Matches'))
        self.tree_matches.append_column(tree_view_column)
        tree_view_column.pack_start(cell_renderer_text, True)
        tree_view_column.add_attribute(cell_renderer_text, 'text', 0)

        self.dialog = self.builder.get_object('window1')
        self.dialog.set_title(self.APP_NAME)
        self.dialog.set_icon_name(self.APP_ICON)
        self.add_window(self.dialog)

        self.btn_search = self.builder.get_object('btn_search')
        self.btn_stop = self.builder.get_object('btn_stop')
        self.btn_stop.set_sensitive(False)

        # Connect signals manually for GTK 4 compatibility
        self.dialog.connect('close-request', self.on_window1_close_request)
        self.btn_search.connect('clicked', self.on_btn_search_clicked)
        self.btn_stop.connect('clicked', self.on_btn_stop_clicked)
        self.builder.get_object('btn_about').connect('clicked', self.on_btn_about_clicked)
        self.builder.get_object('btn_exit').connect('clicked', self.on_btn_exit_clicked)
        self.builder.get_object('btn_path').connect('clicked', self.on_btn_path_clicked)
        self.tree_matches.connect('row-activated', self.on_tree_matches_row_activated)

        self.btn_warnings = self.builder.get_object('btn_warnings')
        self.btn_warnings.connect('clicked', self.on_btn_warnings_clicked)

        # Event controller for keyboard events (Escape to quit)
        evk = Gtk.EventControllerKey.new()
        evk.connect('key-pressed', self.on_window1_key_pressed)
        self.dialog.add_controller(evk)

        self.dialog.set_default_widget(self.btn_search)

        self.builder.get_object('txt_path').set_text(self.options['path'])
        self.builder.get_object('txt_content').grab_focus()

        self.builder.get_object('txt_path').set_activates_default(True)
        self.builder.get_object('txt_content').set_activates_default(True)

        self.dialog.present()

    def on_window1_close_request(self, window):
        self.quit()
        return True

    def on_window1_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self.quit()
            return True
        return False

    def on_btn_exit_clicked(self, widget):
        self.quit()

    def on_tree_matches_row_activated(self, tree_view, path, column):
        (model, iter_) = tree_view.get_selection().get_selected()
        if iter_:
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
        self.warnings.clear()
        self.btn_warnings.set_visible(False)

        self.matches.clear()
        path = self.builder.get_object('txt_path').get_text()
        if not os.path.exists(path):
            msg = _('Error: path %s does not exist') % path
            dialog = Gtk.MessageDialog(
                transient_for=self.dialog,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=msg
            )
            dialog.format_secondary_text(_('Ensure path is correct.'))
            dialog.connect('response', lambda d, r: d.destroy())
            dialog.present()
        else:
            self.btn_search.set_sensitive(False)
            self.btn_stop.set_sensitive(True)

            lbl_status = self.builder.get_object('lbl_status')
            lbl_status.set_text(_('Searching in %s...') % path)
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
        return False

    @idle_add_decorator
    def on_btn_about_clicked(self, widget):
        about = Gtk.AboutDialog(transient_for=self.dialog)
        about.set_program_name(self.APP_NAME)
        about.set_comments(self.APP_DESCRIPTION)
        about.set_version(__version__)
        about.set_logo_icon_name(self.APP_ICON)
        about.set_copyright(__copyright__)
        about.set_authors(__author__)
        about.present()

    def on_btn_path_clicked(self, widget):
        dialog = Gtk.FileDialog.new()
        dialog.set_title(_('Please choose a folder'))

        initial_path = self.builder.get_object('txt_path').get_text()
        if os.path.exists(initial_path):
            dialog.set_initial_folder(Gio.File.new_for_path(initial_path))

        dialog.select_folder(self.dialog, None, self.on_folder_selected)

    def on_folder_selected(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
            if folder:
                txt_path = self.builder.get_object('txt_path')
                txt_path.set_text(folder.get_path())
        except Exception:
            pass
        self.builder.get_object('txt_content').grab_focus()

    @idle_add_decorator
    def search_completed(self):
        lbl_status = self.builder.get_object('lbl_status')
        msg = _('%d matches in %d files') % (self.match_count, self.ooo_count)
        lbl_status.set_text(msg)

        self.btn_search.set_sensitive(True)
        self.btn_stop.set_sensitive(False)

        if self.warnings:
            self.btn_warnings.set_visible(True)
            self.btn_warnings.set_label(_("Warnings (%d)") % len(self.warnings))
        else:
            self.btn_warnings.set_visible(False)

    @idle_add_decorator
    def search_cancelled(self):
        lbl_status = self.builder.get_object('lbl_status')
        msg = _('%d matches so far in %d files (search stopped)') % (
            self.match_count,
            self.ooo_count,
        )
        lbl_status.set_text(msg)
        self.btn_search.set_sensitive(True)
        self.btn_stop.set_sensitive(False)

        if self.warnings:
            self.btn_warnings.set_visible(True)
            self.btn_warnings.set_label(_("Warnings (%d)") % len(self.warnings))
        else:
            self.btn_warnings.set_visible(False)

    @idle_add_decorator
    def on_btn_warnings_clicked(self, widget):
        dialog = Gtk.MessageDialog(
            transient_for=self.dialog,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK,
            text=_('Warnings Log')
        )
        log_content = "\n".join(self.warnings[:30])
        if len(self.warnings) > 30:
            log_content += "\n..." + _("and %d more warnings") % (len(self.warnings) - 30)
        dialog.format_secondary_text(log_content)
        dialog.connect('response', lambda d, r: d.destroy())
        dialog.present()

    def add_line_to_results(self, line):
        if self.console:
            print(line)
        else:
            GLib.idle_add(self._append_to_matches, line)

    def _append_to_matches(self, line):
        self.matches.append([line])
        return False

    def match(self, text):
        mode = self.options['mode']
        query = ' '.join(self.options['content'])
        if not self.console:
            mode = self.builder.get_object('cbb_mode').get_active_text()
            query = self.builder.get_object('txt_content').get_text()

        if mode == _('Phrase') or mode == 'phrase':
            regex = re.compile(re.escape(query.lower()), re.DOTALL)
            if regex.search(text):
                return True
        else:
            parts = re.split(r'\s+', query.strip())
            if mode == _('And') or mode == 'and':
                for part in parts:
                    regex = re.compile(re.escape(part.lower()), re.DOTALL)
                    if not regex.search(text):
                        return False
                return True
            elif mode == _('Or') or mode == 'or':
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
                'sxw', 'stw',
                'sxc', 'stc',
                'sxi', 'sti',
                'sxg',
                'sxm',
                'sxd', 'std',
                'odt', 'ott',
                'odp', 'otp',
                'odf',
                'odg', 'otg',
                'ods', 'ots',
            ) and zipfile.is_zipfile(filename):
                with zipfile.ZipFile(filename) as zf:
                    content = ''
                    try:
                        archives = zf.namelist()
                        for item in archives:
                            if item.endswith('content.xml'):
                                content += zf.read(item).decode()

                            if item.endswith('document.xml'):
                                content += zf.read(item).decode()

                        content = remove_xml_markup(content)
                        doc_info = remove_xml_markup(zf.read('meta.xml').decode())
                        self.ooo_count += 1
                    except KeyError as err:
                        msg = _("Warning: %s not found in '%s'") % (err, filename)
                        print(msg)
                        self.warnings.append(msg)
                        return None

                    return self.match(f'{content.lower()} {doc_info.lower()}')

            # Handle MS-Office (>= 2007) files:
            if ext in (
                'docx', 'dotx',
                'xlsx', 'xltx',
            ) and zipfile.is_zipfile(filename):
                with zipfile.ZipFile(filename) as zf:
                    content = ''
                    try:
                        archives = zf.namelist()
                        for item in archives:
                            if item.endswith('document.xml'):
                                content += zf.read(item).decode()

                            if item.endswith('sharedStrings.xml'):
                                content += zf.read(item).decode()

                        content = remove_xml_markup(content)
                        doc_info = remove_xml_markup(zf.read('docProps/core.xml').decode())
                        self.ooo_count += 1
                    except KeyError as err:
                        msg = _("Warning: %s not found in '%s'") % (err, filename)
                        print(msg)
                        self.warnings.append(msg)
                        return None

                    return self.match(f'{content.lower()} {doc_info.lower()}')

            # Handle MS-Office (>= 2007) MS-PowerPoint files:
            if ext in (
                'pptx',
            ) and zipfile.is_zipfile(filename):
                with zipfile.ZipFile(filename) as zf:
                    try:
                        archives = zf.namelist()
                        slides = []
                        for item in archives:
                            if len(item) >= 12 and item[4:12] == 'slides/s':
                                slides.append(item)

                        content = ''
                        for item in slides:
                            content += zf.read(item).decode()

                        content = remove_xml_markup(content)
                        doc_info = remove_xml_markup(zf.read('docProps/core.xml').decode())
                        self.ooo_count += 1
                    except KeyError as err:
                        msg = _("Warning: %s not found in '%s'") % (err, filename)
                        print(msg)
                        self.warnings.append(msg)
                        return None

                    return self.match(f'{content.lower()} {doc_info.lower()}')

        except zipfile.BadZipfile as err:
            msg = _('Warning: Supposed ZIP file %s could not be opened: %s') % (filename, str(err))
            print(msg)
            self.warnings.append(msg)
        except IOError as err:
            msg = _('Warning: File %s could not be opened: %s') % (filename, str(err))
            print(msg)
            self.warnings.append(msg)

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
            super().run([sys.argv[0]])


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
    locale.setlocale(locale.LC_ALL, '')
    ODFinderApp(parse_args()).run()


if __name__ == '__main__':
    main()
