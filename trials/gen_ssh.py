import subprocess
import os

key_file = "vps_key"
if os.path.exists(key_file):
    os.remove(key_file)
if os.path.exists(key_file + ".pub"):
    os.remove(key_file + ".pub")

subprocess.run(["ssh-keygen", "-t", "ed25519", "-f", key_file, "-N", "", "-q"], check=True)
with open(key_file + ".pub", "r") as f:
    print(f.read())
