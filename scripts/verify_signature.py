#!/usr/bin/env python3
import hashlib, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
SIG = ROOT / "SIGNATURE.sha256"
if not SIG.exists(): print("SIGNATURE.sha256 not found"); sys.exit(1)
fail = 0
for line in SIG.read_text().splitlines():
    if not line.strip(): continue
    exp, rel = line.split("  ", 1)
    fp = ROOT / rel
    if not fp.exists(): print(f"MISSING  {rel}"); fail += 1; continue
    act = hashlib.sha256(fp.read_bytes()).hexdigest()
    if act != exp: print(f"FAIL     {rel}"); fail += 1
    else: print(f"OK       {rel}")
sys.exit(0 if fail == 0 else 1)
