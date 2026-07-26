import struct
import sys
import pymem
import pymem.process
import pymem.ptypes

# Process list
CANDIDATE_PROCESSES = [
    "ProjectXPlayerBeta.exe",
    "2017L.exe",
    "2018L.exe",
    "2020L.exe",
    "2021M.exe",
    "PekoraPlayer.exe",
    "ProjectXPlayer.exe",
]

TARGET_FPS = 999
TARGET_INTERVAL = (1.0 / TARGET_FPS) if TARGET_FPS > 0 else 0.0
DEFAULT_60FPS_INTERVAL = 1.0 / 60.0  # ~0.016666666666666666


def safe_patch_fps():
    pm = None
    proc_name = None

    for candidate in CANDIDATE_PROCESSES:
        try:
            pm = pymem.Pymem(candidate)
            proc_name = candidate
            print(f"attached to: {proc_name} (PID: {pm.process_id})")
            break
        except pymem.exception.ProcessNotFound:
            continue

    if not pm:
        print("Could not find running game process!")
        return

    old_bytes = struct.pack("<d", DEFAULT_60FPS_INTERVAL)
    new_bytes = struct.pack("<d", TARGET_INTERVAL)

    print("unlocking fps yippee")

    patched_count = 0

    # Iterate through process memory regions manually to filter write permission
    try:
        matches = pm.pattern_scan_all(old_bytes, return_multiple=True)
        if isinstance(matches, int):
            matches = [matches]
    except Exception as e:
        print(f"Scan error: {e}")
        return

    if not matches:
        print("could not find frame timing value in memory :(")
        return

    print(f"found candidate addresses. filtering memory pages...")

    for addr in matches:
        try:
            # Query memory page info to ensure it is writeable data (PAGE_READWRITE = 0x04)
            mbi = pymem.memory.virtual_query(pm.process_handle, addr)
            if mbi.Protect == 0x04:  # PAGE_READWRITE
                pm.write_bytes(addr, new_bytes, len(new_bytes))
                patched_count += 1
                print(f" -> Safely patched address: 0x{addr:X}")
        except Exception:
            continue

    print(f"\ndone! patched {patched_count} memory locations.")


if __name__ == "__main__":
    safe_patch_fps()