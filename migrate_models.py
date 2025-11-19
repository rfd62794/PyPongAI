import os
import shutil

src = "models"
dst = os.path.join("data", "models")

if not os.path.exists(src):
    print(f"Source {src} does not exist. Skipping.")
    exit()

for root, dirs, files in os.walk(src):
    # Compute destination path
    rel_path = os.path.relpath(root, src)
    target_dir = os.path.join(dst, rel_path)
    
    os.makedirs(target_dir, exist_ok=True)
    
    for file in files:
        src_file = os.path.join(root, file)
        dst_file = os.path.join(target_dir, file)
        
        if not os.path.exists(dst_file):
            shutil.move(src_file, dst_file)
            print(f"Moved {file} to {target_dir}")
        else:
            print(f"Skipped {file} (already exists)")

# Cleanup empty dirs
for root, dirs, files in os.walk(src, topdown=False):
    for name in dirs:
        try:
            os.rmdir(os.path.join(root, name))
        except OSError:
            pass
try:
    os.rmdir(src)
    print("Removed empty models/ directory.")
except OSError:
    print("models/ directory not empty, kept.")
