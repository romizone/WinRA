"""Archive operations: extract, compress, and convert ZIP/RAR files."""

import os
import zipfile
import shutil
import subprocess
import tempfile
from pathlib import Path


def extract_zip(src: str, dest: str, progress_cb=None) -> list[str]:
    """Extract a ZIP file to destination folder. Returns list of extracted files."""
    extracted = []
    with zipfile.ZipFile(src, 'r') as zf:
        members = zf.namelist()
        total = len(members)
        for i, member in enumerate(members):
            zf.extract(member, dest)
            extracted.append(member)
            if progress_cb:
                progress_cb(i + 1, total, member)
    return extracted


def extract_rar(src: str, dest: str, progress_cb=None) -> list[str]:
    """Extract a RAR file using unar command. Returns list of extracted files."""
    unar_path = _find_tool("unar")
    if not unar_path:
        raise FileNotFoundError(
            "unar tidak ditemukan. Install dengan: brew install unar"
        )

    # List files first for progress tracking
    lsar_path = _find_tool("lsar")
    file_list = []
    if lsar_path:
        result = subprocess.run(
            [lsar_path, "-j", src],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            import json
            try:
                data = json.loads(result.stdout)
                file_list = [
                    e.get("XADFileName", "")
                    for e in data.get("lsarContents", [])
                ]
            except (json.JSONDecodeError, KeyError):
                pass

    if progress_cb and file_list:
        progress_cb(0, len(file_list), "Memulai ekstraksi...")

    # Snapshot existing files BEFORE extraction to avoid counting pre-existing files
    existing_files = set()
    if os.path.isdir(dest):
        for root, dirs, files in os.walk(dest):
            for f in files:
                existing_files.add(os.path.relpath(os.path.join(root, f), dest))

    result = subprocess.run(
        [unar_path, "-o", dest, "-f", src],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Gagal ekstrak RAR: {result.stderr}")

    # Collect only newly extracted files
    extracted = []
    for root, dirs, files in os.walk(dest):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), dest)
            if rel not in existing_files:
                extracted.append(rel)

    if progress_cb:
        total = max(len(extracted), 1)
        progress_cb(total, total, "Selesai!")

    return extracted


def compress_to_zip(paths: list[str], output: str, progress_cb=None) -> str:
    """Compress files/folders into a ZIP archive. Returns output path."""
    file_list = []  # [(absolute_path, arcname)]

    for p in paths:
        if os.path.isdir(p):
            # For directories: preserve folder structure relative to parent
            parent = os.path.dirname(p)
            for root, dirs, files in os.walk(p):
                for f in files:
                    full = os.path.join(root, f)
                    arcname = os.path.relpath(full, parent)
                    file_list.append((full, arcname))
        else:
            # For individual files: just use the filename
            file_list.append((p, os.path.basename(p)))

    total_files = len(file_list)
    if total_files == 0:
        raise ValueError("No files to compress.")

    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i, (filepath, arcname) in enumerate(file_list):
            zf.write(filepath, arcname)
            if progress_cb:
                progress_cb(i + 1, total_files, os.path.basename(filepath))

    return output


def convert_rar_to_zip(rar_path: str, zip_output: str, progress_cb=None) -> str:
    """Convert RAR to ZIP by extracting and re-compressing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        if progress_cb:
            progress_cb(0, 100, "Mengekstrak RAR...")

        extract_rar(rar_path, tmpdir)

        if progress_cb:
            progress_cb(50, 100, "Mengompres ke ZIP...")

        # Find the extracted content
        items = os.listdir(tmpdir)
        paths = [os.path.join(tmpdir, item) for item in items]

        # Build ZIP from extracted content
        file_list = []
        for p in paths:
            if os.path.isdir(p):
                for root, dirs, files in os.walk(p):
                    for f in files:
                        full = os.path.join(root, f)
                        arc = os.path.relpath(full, tmpdir)
                        file_list.append((full, arc))
            else:
                file_list.append((p, os.path.relpath(p, tmpdir)))

        with zipfile.ZipFile(zip_output, 'w', zipfile.ZIP_DEFLATED) as zf:
            total = len(file_list)
            for i, (full, arc) in enumerate(file_list):
                zf.write(full, arc)
                if progress_cb and total > 0:
                    pct = 50 + int((i + 1) / total * 50)
                    progress_cb(pct, 100, os.path.basename(arc))

    return zip_output


def convert_zip_to_rar(zip_path: str, rar_output: str, progress_cb=None) -> str:
    """Convert ZIP to RAR. Requires 'rar' command-line tool."""
    rar_tool = _find_tool("rar")
    if not rar_tool:
        raise FileNotFoundError(
            "Tool 'rar' tidak ditemukan. Pembuatan file RAR memerlukan "
            "WinRAR CLI. Sebagai alternatif, gunakan format ZIP."
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        if progress_cb:
            progress_cb(0, 100, "Mengekstrak ZIP...")

        extract_zip(zip_path, tmpdir)

        if progress_cb:
            progress_cb(50, 100, "Mengompres ke RAR...")

        result = subprocess.run(
            [rar_tool, "a", "-r", rar_output] + os.listdir(tmpdir),
            cwd=tmpdir,
            capture_output=True, text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"Gagal membuat RAR: {result.stderr}")

        if progress_cb:
            progress_cb(100, 100, "Selesai!")

    return rar_output


def get_archive_info(filepath: str) -> dict:
    """Get information about an archive file."""
    ext = Path(filepath).suffix.lower()
    info = {
        "path": filepath,
        "name": os.path.basename(filepath),
        "size": os.path.getsize(filepath),
        "type": ext.lstrip("."),
        "files": [],
        "total_files": 0,
        "total_size": 0,
    }

    if ext == ".zip":
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                for zi in zf.infolist():
                    info["files"].append({
                        "name": zi.filename,
                        "size": zi.file_size,
                        "compressed": zi.compress_size,
                        "is_dir": zi.is_dir(),
                    })
                info["total_files"] = len([f for f in info["files"] if not f["is_dir"]])
                info["total_size"] = sum(f["size"] for f in info["files"])
        except zipfile.BadZipFile:
            info["error"] = "File ZIP rusak atau tidak valid"

    elif ext == ".rar":
        lsar_path = _find_tool("lsar")
        if lsar_path:
            result = subprocess.run(
                [lsar_path, "-j", filepath],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                import json
                try:
                    data = json.loads(result.stdout)
                    for entry in data.get("lsarContents", []):
                        info["files"].append({
                            "name": entry.get("XADFileName", ""),
                            "size": entry.get("XADFileSize", 0),
                            "compressed": entry.get("XADCompressedSize", 0),
                            "is_dir": entry.get("XADIsDirectory", False),
                        })
                    info["total_files"] = len([f for f in info["files"] if not f["is_dir"]])
                    info["total_size"] = sum(f["size"] for f in info["files"])
                except (json.JSONDecodeError, KeyError):
                    info["error"] = "Gagal membaca info RAR"
        else:
            info["error"] = "unar/lsar tidak terinstall"

    return info


def format_size(size_bytes: int) -> str:
    """Format byte size to human readable string."""
    if size_bytes == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            if unit == 'B':
                return f"{int(size_bytes)} B"
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def _find_tool(name: str) -> str | None:
    """Find a command-line tool in PATH or common locations."""
    result = shutil.which(name)
    if result:
        return result

    common_paths = [
        f"/opt/homebrew/bin/{name}",
        f"/usr/local/bin/{name}",
        f"/usr/bin/{name}",
    ]
    for p in common_paths:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p

    return None
