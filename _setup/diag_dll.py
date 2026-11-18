"""Diagnose missing DLL dependencies for the PyTorch Windows build."""
import os
import sys
from pathlib import Path

import pefile

ROOT = Path(__file__).resolve().parent.parent
TORCH_LIB = ROOT / ".venv" / "Lib" / "site-packages" / "torch" / "lib"
PY_BASE = Path(r"C:\04 software\Python310")
VENV_SCRIPTS = ROOT / ".venv" / "Scripts"
SYSTEM32 = Path(r"C:\Windows\System32")

SEARCH = [TORCH_LIB, VENV_SCRIPTS, PY_BASE, SYSTEM32]


def locate(name):
    for d in SEARCH:
        candidate = d / name
        if candidate.is_file():
            return str(candidate)
    return None


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else str(TORCH_LIB / "fbgemm.dll")
    print("Analyzing:", target)
    pe = pefile.PE(target)
    imports = []
    for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
        imports.append(entry.dll.decode(errors="replace"))
    try:
        for entry in pe.DIRECTORY_ENTRY_DELAY_IMPORT:
            imports.append(entry.dll.decode(errors="replace") + " (delay)")
    except AttributeError:
        pass

    print("\nImported DLLs:")
    for name in sorted(set(imports)):
        clean = name.replace(" (delay)", "")
        loc = locate(clean)
        print(f"  {'OK     ' if loc else 'MISSING'} {name}")
        if loc:
            print(f"          -> {loc}")

    print("\nRecursive check of torch/lib DLLs:")
    missing = set()
    for dll in sorted(TORCH_LIB.glob("*.dll")):
        try:
            sub = pefile.PE(str(dll), fast_load=True)
            sub.parse_data_directories(
                directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]]
            )
            for entry in getattr(sub, "DIRECTORY_ENTRY_IMPORT", []):
                dep = entry.dll.decode(errors="replace")
                if not locate(dep):
                    missing.add((dll.name, dep))
        except Exception as exc:  # noqa: BLE001
            print("  parse error", dll.name, exc)
    if missing:
        for dll_name, dep in sorted(missing):
            print(f"  MISSING: {dll_name} -> {dep}")
    else:
        print("  All first-level imports resolvable.")


if __name__ == "__main__":
    main()
