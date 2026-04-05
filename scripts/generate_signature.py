#!/usr/bin/env python3
import hashlib, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
SIG = ROOT / "SIGNATURE.sha256"
SKIP = {".git", "__pycache__", ".pytest_cache", ".DS_Store"}
def sha(p):
    h = hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
lines = []
for p in sorted(ROOT.rglob("*")):
    if p.is_dir() or any(s in p.parts for s in SKIP) or p.name == "SIGNATURE.sha256":
        continue
    lines.append(f"{sha(p)}  {p.relative_to(ROOT)}")
SIG.write_text("\n".join(lines) + "\n")
print(f"Signed {len(lines)} files -> SIGNATURE.sha256")
