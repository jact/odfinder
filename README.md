# Open Document Finder (odfinder)

[![Python Version](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Format Support](https://img.shields.io/badge/Formats-ODF%20%7C%20OOo%20%7C%20MS%20Office-brightgreen.svg)](#-supported-formats)

**Open Document Finder** (`odfinder`) is a lightweight desktop utility and command-line tool for Linux systems (specifically GNOME/Unity desktops) that allows users to quickly search for text content inside OpenOffice/LibreOffice and Microsoft Office documents.

It is inspired by the [Loook project](http://mechtilde.de/Loook/).

---

## 🚀 Features

* **Dual Interface**: Run the application in a graphical user interface (GUI) or run search queries directly from your terminal.
* **Smart Search Modes**:
  * **Or**: Finds documents containing at least one of the search terms.
  * **And**: Finds documents containing all of the search terms.
  * **Phrase**: Finds documents containing the exact phrase.
* **Fast and Non-blocking**: Search runs asynchronously in a background scheduler worker thread so the GUI remains responsive.
* **Auto-Launch**: Double-clicking on search results automatically opens the document with the system's default handler.

---

## 📂 Supported Formats

The application recursively walks through directories, opens zip-based office XML archives, and extracts text content from:

* **LibreOffice / OpenOffice (.odt, .ods, .odp, etc.)**:
  * Writer: `.odt`, `.ott`, `.sxw`, `.stw`
  * Calc: `.ods`, `.ots`, `.sxc`, `.stc`
  * Impress: `.odp`, `.otp`, `.sxi`, `.sti`
  * Draw: `.odg`, `.otg`, `.sxd`, `.std`
  * Formula: `.odf`, `.sxm`
  * Master Documents: `.sxg`
* **Microsoft Office (2007 and later)**:
  * Word: `.docx`, `.dotx`
  * Excel: `.xlsx`, `.xltx`
  * PowerPoint: `.pptx`

---

## 📋 Requirements

* **Operating System**: Linux (Gnome, Unity, or any compatible X11/Wayland desktop).
* **Python**: `python >= 3.10`
* **Desktop bindings**: `PyGObject` (Gtk 4 bindings)

To install system dependencies on Debian/Ubuntu systems:

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gettext
```

---

## ⚙️ Installation

### 1. Build and Install as a Debian Package (Recommended)

This compiles localization files and registers the application launcher icon in your desktop environment:

```bash
# Install packaging dependencies
sudo apt install python3-stdeb python3-setuptools

# Build the DEB package
python3 setup.py --command-packages=stdeb.command bdist_deb

# Install the generated package
sudo dpkg -i deb_dist/*.deb
```

### 2. Standard Python Installation

You can install the package directly via `pip`:

```bash
pip install .
```

---

## 🖥️ Usage

### Graphical Interface (GUI)

Simply launch `odfinder` from your applications menu or run:

```bash
odfinder
```

Fill in the search path, input your query, select the matching mode, and click **Buscar** (Search).

### Command Line Interface (CLI)

You can trigger searches directly in the terminal by providing search terms:

```bash
# Search for the word 'invoice' inside documents under the home folder
odfinder -p ~/Documents -m or invoice

# Search using 'And' mode for multiple words
odfinder -p ~/Documents -m and project report 2026
```

#### CLI Options

* `-p, --path`: Specify target directory to search (default is `$HOME`).
* `-m, --mode`: Search matching mode: `or`, `and`, or `phrase` (default is `or`).

---

## 🛠️ Development

### 1. Setup the Environment

It is recommended to use a virtual environment. Install the package in editable mode with development dependencies:

```bash
# Clone the repository and install in editable mode
pip install -e .[dev]
```

### 2. Code Quality & Formatting

We use `ruff` to enforce formatting and linting rules:

* Line length limit: **120 characters**.
* Quotation style: Prefer **single quotes** (`'`).

To check code style:

```bash
ruff check .
ruff format --check .
```

### 3. Running Tests

Run the unit tests suite with `pytest`:

```bash
python3 -m pytest
```

### 4. Localization / Translations

If you modify or add translatable strings:

```bash
# Extract strings and update the translation catalogs (.po)
make -C i18n update-po

# Compile translation catalogs (.po -> .mo) for testing/run
python3 setup.py build
```

---

## 📄 License & Authors

* **License**: Released under the [GNU GPL v3 License](LICENSE).
* **Authors**: Jose Antonio Chavarría <jachavar@gmail.com> (See `AUTHORS` file).
* **Icon credit**: Made by [Freepik](http://www.freepik.com) from [www.flaticon.com](http://www.flaticon.com).
