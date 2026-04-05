# Blockchain / Signature Note

This repository does not ship an on-chain smart contract.

Instead, it fixes release snapshots with `SIGNATURE.sha256`.

- Generate: `python3 scripts/generate_signature.py`
- Verify: `python3 scripts/verify_signature.py`
- Package identity: `python3 scripts/verify_package_identity.py`
- Release gate: `python3 scripts/release_check.py`

Purpose:
- confirm the current tree matches the signed snapshot
- keep docs, code, and tests aligned
- preserve release hygiene for public distribution
