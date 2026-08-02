import os
import re
import shutil
import zipfile
from collections import Counter
from pathlib import Path

from .base import Agent

FORBIDDEN = ("\\windows", "system32", "program files", "/etc", "/usr", "/bin")
GROUPS = {
    "Images": [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".md", ".xlsx", ".pptx", ".csv"],
    "Code": [".py", ".js", ".html", ".css", ".json", ".c", ".cpp", ".java", ".bat"],
    "Media": [".mp3", ".mp4", ".mkv", ".wav", ".mov"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
}


class FileAgent(Agent):
    name = "files"
    description = "Create, read, move, copy, rename, delete, search, organize, zip files and folders"
    keywords = ["file", "folder", "create a", "delete", "rename", "move", "copy", "organize",
                "zip", "compress", "extract", "unzip", "find file", "search files", "directory",
                "list", "downloads", "desktop", "documents"]

    def _safe(self, raw):
        p = Path(raw).expanduser().resolve()
        low = str(p).lower()
        if any(f in low for f in FORBIDDEN):
            raise PermissionError(f"security policy blocks system paths: {p}")
        return p

    def _paths(self, task):
        quoted = re.findall(r"[\"']([^\"']+)[\"']", task)
        if quoted:
            return [self._safe(q) for q in quoted]
        raw = re.findall(r"[A-Za-z]:[\\/][^\s]+|(?:[~/])?[^\s]+\.[a-z0-9]{1,5}", task, re.I)
        return [self._safe(r) for r in raw[:3]] if raw else []

    async def run(self, task, context=""):
        t = task.lower()
        home = Path.home()
        try:
            paths = self._paths(task)
        except PermissionError as e:
            return self.done(str(e))
        try:
            if "organize" in t:
                return self._organize(paths[0] if paths else home / "Downloads")
            if ("zip" in t or "compress" in t) and "extract" not in t and "unzip" not in t:
                target = paths[0] if paths else home / "Downloads"
                if target.is_dir():
                    shutil.make_archive(str(target), "zip", str(target))
                    out = target.with_suffix(".zip")
                else:
                    out = target.with_suffix(".zip")
                    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
                        z.write(target, target.name)
                return self.done(f"Compressed to {out.name}, boss.", str(out), [str(out)])
            if "extract" in t or "unzip" in t:
                if not paths:
                    return self.done("Which archive, boss?")
                dest = paths[0].with_suffix("")
                shutil.unpack_archive(paths[0], dest)
                return self.done(f"Extracted to {dest}.", str(dest), [str(dest)])
            if "rename" in t and len(paths) >= 2:
                paths[0].rename(paths[1])
                return self.done(f"Renamed {paths[0].name} to {paths[1].name}.")
            if "move" in t and len(paths) >= 2:
                shutil.move(str(paths[0]), str(paths[1]))
                return self.done(f"Moved {paths[0].name} to {paths[1]}.")
            if "copy" in t and len(paths) >= 2:
                if paths[0].is_dir():
                    shutil.copytree(paths[0], paths[1], dirs_exist_ok=True)
                else:
                    shutil.copy2(paths[0], paths[1])
                return self.done(f"Copied {paths[0].name}, boss.")
            if "delete" in t and paths:
                p = paths[0]
                if p.is_dir():
                    shutil.rmtree(p)
                else:
                    p.unlink()
                self.ctx.db.audit("delete", str(p))
                return self.done(f"Deleted {p.name}, boss.")
            if ("read" in t or "what" in t) and paths and paths[0].is_file():
                txt = paths[0].read_text(encoding="utf-8", errors="ignore")[:3000]
                return self.done(f"{paths[0].name}: showing {len(txt)} characters.", txt, [str(paths[0])])
            if "find" in t or "search" in t:
                m = re.search(r"(?:find|search for|search)\s+(?:files? )?(?:named |called )?[\"']?(.+?)[\"']?$",
                              task, re.I)
                needle = (m.group(1) if m else task).lower().strip(" .")
                return self._search(paths[0] if paths else home, needle)
            if "create" in t or "make" in t or "new" in t:
                m = re.search(r"(?:called|named)\s+[\"']?([^\"']+)[\"']?", task, re.I)
                name = m.group(1).strip() if m else (paths[0].name if paths else "new_file.txt")
                target = paths[0] if paths else (home / "Desktop" / name)
                if "folder" in t or "directory" in t:
                    target.mkdir(parents=True, exist_ok=True)
                    return self.done(f"Folder created: {target}")
                if not target.suffix:
                    target = target.with_suffix(".txt")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(context or "", encoding="utf-8")
                return self.done(f"File created: {target}", str(target), [str(target)])
            if "list" in t or "what's in" in t or "whats in" in t:
                base = paths[0] if paths else home / "Desktop"
                if not base.is_dir():
                    return self.done(f"{base} isn't a folder, boss.")
                entries = sorted(base.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))[:40]
                lines = [f"{'[DIR]' if e.is_dir() else '     '} {e.name}" +
                         (f"  ({e.stat().st_size // 1024} KB)" if e.is_file() else "") for e in entries]
                return self.done(f"{len(entries)} items in {base.name}.", "\n".join(lines))
            return self.done("Tell me the operation and a path, boss — create, read, move, copy, rename, delete, search, organize, zip.")
        except FileNotFoundError as e:
            return self.done(f"Couldn't find it, boss: {e}")
        except Exception as e:
            return self.done(f"File operation failed: {e}")

    def _organize(self, folder):
        if not folder.is_dir():
            return self.done(f"{folder} isn't a folder.")
        moved = 0
        for f in folder.iterdir():
            if not f.is_file():
                continue
            for group, exts in GROUPS.items():
                if f.suffix.lower() in exts:
                    dest = folder / group
                    dest.mkdir(exist_ok=True)
                    shutil.move(str(f), str(dest / f.name))
                    moved += 1
                    break
        return self.done(f"Organized {folder.name}: {moved} files sorted into groups.")

    def _search(self, base, needle, cap=15000):
        hits, seen = [], 0
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in ("$Recycle.Bin", "AppData", "node_modules", ".git", "venv")]
            for name in files:
                seen += 1
                if seen > cap:
                    return self.done(f"Search capped at {cap} files.", "\n".join(hits))
                if needle in name.lower():
                    hits.append(os.path.join(root, name))
                    if len(hits) >= 25:
                        break
            if len(hits) >= 25:
                break
        if not hits:
            return self.done(f"No files matching '{needle}' under {base}.")
        return self.done(f"Found {len(hits)} match(es) for '{needle}'.", "\n".join(hits))


AGENT = FileAgent