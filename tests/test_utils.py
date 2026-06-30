# -*- coding: utf-8 -*-

import os

import pytest

from odfinder.utils import get_filename_ext, get_ui_resource, remove_xml_markup


# ── get_filename_ext ────────────────────────────────────────────────


class TestGetFilenameExt:
    def test_simple_extension(self):
        assert get_filename_ext('document.odt') == 'odt'

    def test_uppercase_returns_lowercase(self):
        assert get_filename_ext('REPORT.DOCX') == 'docx'

    def test_mixed_case(self):
        assert get_filename_ext('file.Xlsx') == 'xlsx'

    def test_no_extension(self):
        assert get_filename_ext('README') == ''

    def test_dotfile_no_extension(self):
        assert get_filename_ext('.gitignore') == ''

    def test_multiple_dots(self):
        assert get_filename_ext('archive.tar.gz') == 'gz'

    def test_empty_string(self):
        assert get_filename_ext('') == ''

    def test_path_with_directories(self):
        assert get_filename_ext('/home/user/docs/report.odt') == 'odt'


# ── remove_xml_markup ───────────────────────────────────────────────


class TestRemoveXmlMarkup:
    def test_simple_tags(self):
        assert remove_xml_markup('<p>hello</p>') == 'hello'

    def test_nested_tags(self):
        assert remove_xml_markup('<div><b>bold</b> text</div>') == 'bold text'

    def test_html_comments_removed(self):
        assert remove_xml_markup('<!-- comment -->visible') == 'visible'

    def test_multiline_comment(self):
        xml = '<!-- line1\nline2 --><p>text</p>'
        assert remove_xml_markup(xml) == 'text'

    def test_replace_with_space(self):
        result = remove_xml_markup('<p>hello</p>', replace_with_space=True)
        assert result == ' hello '

    def test_empty_string(self):
        assert remove_xml_markup('') == ''

    def test_no_markup(self):
        assert remove_xml_markup('plain text') == 'plain text'

    def test_self_closing_tags(self):
        assert remove_xml_markup('<br/>text<hr/>') == 'text'

    def test_attributes_in_tags(self):
        assert remove_xml_markup('<p class="intro">content</p>') == 'content'

    def test_real_odt_fragment(self):
        xml = (
            '<office:body><office:text>'
            '<text:p>Documento de prueba</text:p>'
            '</office:text></office:body>'
        )
        assert remove_xml_markup(xml) == 'Documento de prueba'


# ── get_ui_resource ─────────────────────────────────────────────────


class TestGetUiResource:
    def test_fallback_returns_absolute_path(self):
        path = get_ui_resource('odfinder.ui')
        assert os.path.isabs(path)

    def test_fallback_points_to_data_ui(self, monkeypatch):
        monkeypatch.setattr('sys.prefix', '/nonexistent')
        path = get_ui_resource('odfinder.ui')
        assert path.endswith(os.path.join('data', 'ui', 'odfinder.ui'))

    def test_fallback_file_exists(self):
        path = get_ui_resource('odfinder.ui')
        assert os.path.exists(path)

    def test_nonexistent_resource_returns_fallback(self):
        path = get_ui_resource('nonexistent_file.ui')
        assert os.path.isabs(path)
        assert not os.path.exists(path)
