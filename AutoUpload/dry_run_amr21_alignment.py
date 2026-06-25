import importlib.util
import os
import sys


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_SCRIPT = os.path.join(SCRIPT_DIR, "Super-Uploader_BACKUP.py")


def load_backup_module():
    spec = importlib.util.spec_from_file_location("super_uploader_backup", BACKUP_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    device = None
    if "--device" in sys.argv:
        device_index = sys.argv.index("--device") + 1
        if device_index < len(sys.argv):
            device = sys.argv[device_index]
    backup = load_backup_module()
    backup.run_amr21_alignment_dry_run(device=device)
