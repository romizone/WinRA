<p align="center">
  <img src="https://img.shields.io/badge/WinRA-Archive%20Manager-007AFF?style=for-the-badge&logo=apple&logoColor=white" alt="WinRA"/>
</p>

<h1 align="center">
  WinRA
</h1>

<p align="center">
  <strong>A Modern Archive Manager for macOS</strong><br/>
  Extract, Compress & Convert ZIP/RAR files with a beautiful native interface
</p>

<p align="center">
  <a href="https://github.com/romizone/WinRA/releases/latest"><img src="https://img.shields.io/github/v/release/romizone/WinRA?style=flat-square&color=007AFF&label=Latest%20Release" alt="Release"/></a>
  <img src="https://img.shields.io/badge/platform-macOS-lightgrey?style=flat-square&logo=apple" alt="Platform"/>
  <img src="https://img.shields.io/badge/python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License"/>
  <img src="https://img.shields.io/github/repo-size/romizone/WinRA?style=flat-square&color=orange" alt="Repo Size"/>
  <img src="https://img.shields.io/github/last-commit/romizone/WinRA?style=flat-square&color=blue" alt="Last Commit"/>
</p>

<p align="center">
  <a href="#-features">Features</a> &bull;
  <a href="#-installation">Installation</a> &bull;
  <a href="#-screenshots">Screenshots</a> &bull;
  <a href="#%EF%B8%8F-build-from-source">Build</a> &bull;
  <a href="#-contributing">Contributing</a> &bull;
  <a href="#-license">License</a>
</p>

---

## Overview

**WinRA** is a lightweight, native-feeling archive manager designed exclusively for macOS. Built with Python and CustomTkinter, it brings the familiar functionality of WinRAR to the Mac ecosystem with a clean, modern UI that follows Apple's Human Interface Guidelines.

---

## Features

| Feature | Description |
|---------|-------------|
| **Extract** | Unpack ZIP and RAR archives with full progress tracking |
| **Compress** | Create ZIP archives from files and folders |
| **Convert** | Seamlessly convert between RAR and ZIP formats |
| **Dark Mode** | Automatic system theme detection with manual toggle |
| **Native UI** | macOS-native look and feel with SF Pro typography |
| **Progress** | Real-time progress bar with file-level tracking |
| **Finder Integration** | "Show in Finder" for quick access to output files |

### Archive Support

| Format | Extract | Create | Convert To | Convert From |
|--------|---------|--------|------------|--------------|
| **ZIP** | Yes | Yes | Yes | Yes |
| **RAR** | Yes | -- | Yes | Yes |

---

## Installation

### Download (Recommended)

Download the latest release from the [Releases](https://github.com/romizone/WinRA/releases/latest) page:

| Package | Description |
|---------|-------------|
| `WinRA.dmg` | Drag & drop installer |
| `WinRA.pkg` | macOS package installer |

### Prerequisites

For RAR support, install `unar` via Homebrew:

```bash
brew install unar
```

### Run from Source

```bash
# Clone the repository
git clone https://github.com/romizone/WinRA.git
cd WinRA

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

---

## Build from Source

### Build .app + .dmg + .pkg

```bash
chmod +x build.sh
./build.sh
```

This produces:

| Output | Path |
|--------|------|
| Application | `dist/WinRA.app` |
| DMG Installer | `WinRA.dmg` |
| PKG Installer | `WinRA.pkg` |

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Language** | Python 3.13+ |
| **GUI Framework** | CustomTkinter |
| **Archive Handling** | zipfile (stdlib) + unar/lsar (RAR) |
| **Build Tool** | PyInstaller |
| **Installer** | hdiutil (DMG) + pkgbuild (PKG) |
| **Platform** | macOS (Apple Silicon & Intel) |

---

## Project Structure

```
WinRA/
  main.py              # Application entry point
  requirements.txt     # Python dependencies
  build.sh             # Build script (.app, .dmg, .pkg)
  build_pkg.sh         # PKG installer builder
  app/
    __init__.py
    gui.py             # Main GUI (CustomTkinter)
    archive_ops.py     # Archive operations (extract, compress, convert)
    utils.py           # Utility functions
  installer/
    distribution.xml   # PKG distribution config
    resources/         # Installer HTML resources
```

---

## Requirements

| Requirement | Version |
|-------------|---------|
| macOS | 12.0 Monterey or later |
| Python | 3.13+ (for development) |
| unar | Latest (for RAR support) |

---

## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgements

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern UI framework
- [unar](https://theunarchiver.com/command-line) - RAR extraction support
- [PyInstaller](https://pyinstaller.org/) - Application bundling

---

<p align="center">
  Made with <img src="https://img.shields.io/badge/--FF3B30?style=flat-square&label=%E2%9D%A4" alt="love"/> on macOS
</p>
