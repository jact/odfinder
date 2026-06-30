# -*- coding: utf-8 -*-

import os
import shutil
import zipfile

import pytest

from odfinder.odfinder_app import ODFinderApp, parse_args

# ── Fixtures ────────────────────────────────────────────────────────

CONTENT_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"'
    ' xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">'
    '<office:body><office:text>'
    '<text:p>Migración exitosa a GTK4 con búsquedas avanzadas</text:p>'
    '</office:text></office:body></office:document-content>'
)

META_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<office:document-meta xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"'
    ' xmlns:dc="http://purl.org/dc/elements/1.1/">'
    '<office:meta><dc:title>Documento de prueba</dc:title></office:meta>'
    '</office:document-meta>'
)

DOCX_DOCUMENT_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    '<w:body><w:p><w:r><w:t>Informe de auditoría</w:t></w:r></w:p></w:body></w:document>'
)

DOCX_CORE_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"'
    ' xmlns:dc="http://purl.org/dc/elements/1.1/">'
    '<dc:title>Auditoría</dc:title></cp:coreProperties>'
)

PPTX_SLIDE_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
    ' xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
    '<p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r>'
    '<a:t>Diapositiva sobre rendimiento</a:t>'
    '</a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>'
)


@pytest.fixture()
def tmp_docs(tmp_path):
    """Create a temporary directory with mock document files."""
    docs_dir = tmp_path / 'docs'
    docs_dir.mkdir()
    return docs_dir


def _make_odt(path, content_xml=CONTENT_XML, meta_xml=META_XML):
    with zipfile.ZipFile(str(path), 'w') as zf:
        zf.writestr('content.xml', content_xml)
        zf.writestr('meta.xml', meta_xml)


def _make_docx(path, document_xml=DOCX_DOCUMENT_XML, core_xml=DOCX_CORE_XML):
    with zipfile.ZipFile(str(path), 'w') as zf:
        zf.writestr('word/document.xml', document_xml)
        zf.writestr('docProps/core.xml', core_xml)


def _make_pptx(path, slide_xml=PPTX_SLIDE_XML, core_xml=DOCX_CORE_XML):
    with zipfile.ZipFile(str(path), 'w') as zf:
        zf.writestr('ppt/slides/slide1.xml', slide_xml)
        zf.writestr('docProps/core.xml', core_xml)


def _make_app(content, mode='or', path='.'):
    return ODFinderApp({'content': content, 'mode': mode, 'path': path})


# ── Console mode detection ──────────────────────────────────────────


class TestConsoleMode:
    def test_console_mode_with_content(self):
        app = _make_app(['word'])
        assert app.console is True

    def test_gui_mode_without_content(self):
        app = _make_app([])
        assert app.console is False


# ── match() logic ───────────────────────────────────────────────────


class TestMatch:
    def test_or_mode_single_word_found(self):
        app = _make_app(['hello'])
        assert app.match('hello world') is True

    def test_or_mode_single_word_not_found(self):
        app = _make_app(['missing'])
        assert app.match('hello world') is False

    def test_or_mode_partial_match(self):
        app = _make_app(['hello', 'missing'])
        assert app.match('hello world') is True

    def test_and_mode_all_found(self):
        app = _make_app(['hello', 'world'], mode='and')
        assert app.match('hello world') is True

    def test_and_mode_partial_fails(self):
        app = _make_app(['hello', 'missing'], mode='and')
        assert app.match('hello world') is False

    def test_phrase_mode_exact_match(self):
        app = _make_app(['hello', 'world'], mode='phrase')
        assert app.match('say hello world today') is True

    def test_phrase_mode_wrong_order(self):
        app = _make_app(['world', 'hello'], mode='phrase')
        assert app.match('say hello world today') is False

    def test_case_insensitive(self):
        app = _make_app(['HELLO'])
        assert app.match('hello world') is True

    def test_empty_query_or_mode(self):
        app = _make_app([''])
        assert app.match('anything') is True

    def test_special_regex_chars_escaped(self):
        app = _make_app(['file.txt'])
        assert app.match('open file.txt now') is True
        assert app.match('open fileTtxt now') is False


# ── process_file() ──────────────────────────────────────────────────


class TestProcessFile:
    def test_odt_match(self, tmp_docs):
        odt = tmp_docs / 'test.odt'
        _make_odt(odt)
        app = _make_app(['migración'])
        assert app.process_file(str(odt)) is True
        assert app.ooo_count == 1

    def test_odt_no_match(self, tmp_docs):
        odt = tmp_docs / 'test.odt'
        _make_odt(odt)
        app = _make_app(['inexistente'])
        assert app.process_file(str(odt)) is False

    def test_docx_match(self, tmp_docs):
        docx = tmp_docs / 'report.docx'
        _make_docx(docx)
        app = _make_app(['auditoría'])
        assert app.process_file(str(docx)) is True
        assert app.ooo_count == 1

    def test_docx_no_match(self, tmp_docs):
        docx = tmp_docs / 'report.docx'
        _make_docx(docx)
        app = _make_app(['inexistente'])
        assert app.process_file(str(docx)) is False

    def test_pptx_match(self, tmp_docs):
        pptx = tmp_docs / 'slides.pptx'
        _make_pptx(pptx)
        app = _make_app(['rendimiento'])
        assert app.process_file(str(pptx)) is True
        assert app.ooo_count == 1

    def test_pptx_no_match(self, tmp_docs):
        pptx = tmp_docs / 'slides.pptx'
        _make_pptx(pptx)
        app = _make_app(['inexistente'])
        assert app.process_file(str(pptx)) is False

    def test_unsupported_extension_ignored(self, tmp_docs):
        txt = tmp_docs / 'readme.txt'
        txt.write_text('some text')
        app = _make_app(['text'])
        assert app.process_file(str(txt)) is False
        assert app.ooo_count == 0

    def test_missing_meta_xml_returns_none(self, tmp_docs):
        odt = tmp_docs / 'broken.odt'
        with zipfile.ZipFile(str(odt), 'w') as zf:
            zf.writestr('content.xml', CONTENT_XML)
            # meta.xml missing intentionally
        app = _make_app(['migración'])
        assert app.process_file(str(odt)) is None
        assert len(app.warnings) == 1
        assert "broken.odt" in app.warnings[0]
        assert "meta.xml" in app.warnings[0]

    def test_corrupt_zip_returns_false(self, tmp_docs, monkeypatch):
        odt = tmp_docs / 'corrupt.odt'
        _make_odt(odt)
        app = _make_app(['anything'])
        def mock_zipfile(*args, **kwargs):
            raise zipfile.BadZipfile("mocked corrupt zip")
        monkeypatch.setattr(zipfile, 'ZipFile', mock_zipfile)
        assert app.process_file(str(odt)) is False
        assert len(app.warnings) == 1
        assert "corrupt.odt" in app.warnings[0]
        assert "mocked corrupt zip" in app.warnings[0]

    def test_and_mode_across_content_and_meta(self, tmp_docs):
        odt = tmp_docs / 'test.odt'
        _make_odt(odt)
        app = _make_app(['migración', 'prueba'], mode='and')
        # 'migración' in content.xml, 'prueba' in meta.xml
        assert app.process_file(str(odt)) is True


# ── recursive_search() ──────────────────────────────────────────────


class TestRecursiveSearch:
    def test_finds_matching_files(self, tmp_docs, capsys):
        _make_odt(tmp_docs / 'a.odt')
        _make_odt(tmp_docs / 'b.odt')
        app = _make_app(['migración'], path=str(tmp_docs))
        app.recursive_search(None, None, str(tmp_docs))
        captured = capsys.readouterr()
        assert 'a.odt' in captured.out
        assert 'b.odt' in captured.out
        assert app.match_count == 2

    def test_skips_non_matching_files(self, tmp_docs, capsys):
        _make_odt(tmp_docs / 'a.odt')
        app = _make_app(['inexistente'], path=str(tmp_docs))
        app.recursive_search(None, None, str(tmp_docs))
        captured = capsys.readouterr()
        assert captured.out == ''
        assert app.match_count == 0

    def test_subdirectory_traversal(self, tmp_docs, capsys):
        subdir = tmp_docs / 'subdir'
        subdir.mkdir()
        _make_odt(subdir / 'deep.odt')
        app = _make_app(['migración'], path=str(tmp_docs))
        app.recursive_search(None, None, str(tmp_docs))
        captured = capsys.readouterr()
        assert 'deep.odt' in captured.out
        assert app.match_count == 1

    def test_cancellation(self, tmp_docs, capsys):
        _make_odt(tmp_docs / 'a.odt')
        app = _make_app(['migración'], path=str(tmp_docs))
        app.cancellable.cancel()
        app.recursive_search(None, None, str(tmp_docs))
        assert app.match_count == 0


# ── parse_args() ────────────────────────────────────────────────────


class TestParseArgs:
    def test_defaults(self, monkeypatch):
        monkeypatch.setattr('sys.argv', ['odfinder'])
        args = parse_args()
        assert args['mode'] == 'or'
        assert args['content'] == []
        assert args['path'] == os.getenv('HOME')

    def test_custom_args(self, monkeypatch):
        monkeypatch.setattr('sys.argv', ['odfinder', '-p', '/tmp', '-m', 'and', 'word1', 'word2'])
        args = parse_args()
        assert args['path'] == '/tmp'
        assert args['mode'] == 'and'
        assert args['content'] == ['word1', 'word2']

    def test_phrase_mode(self, monkeypatch):
        monkeypatch.setattr('sys.argv', ['odfinder', '-m', 'phrase', 'hello', 'world'])
        args = parse_args()
        assert args['mode'] == 'phrase'
        assert args['content'] == ['hello', 'world']

    def test_invalid_mode_exits(self, monkeypatch):
        monkeypatch.setattr('sys.argv', ['odfinder', '-m', 'invalid'])
        with pytest.raises(SystemExit):
            parse_args()
