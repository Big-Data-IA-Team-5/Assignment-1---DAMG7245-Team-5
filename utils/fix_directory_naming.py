#!/usr/bin/env python3
"""
Directory Consolidation Fix for LANTERN Pipeline

This script fixes the directory naming inconsistency where different labs
create outputs in different directory names for the same document.

Usage: Run automatically after pipeline or manually:
    python fix_directory_naming.py data/parsed
"""

import shutil
import sys
from pathlib import Path


def consolidate_output_directories(output_base):
    """
    Consolidate split output directories into single document directories.

    Moves contents from doc_id format (e.g., goog_2024) to filename format
    (e.g., goog-10-k-2024) to keep all outputs for one document together.
    """
    output_base = Path(output_base)

    if not output_base.exists():
        print(f"❌ Output directory {output_base} does not exist")
        return False

    consolidated = 0

    # Find all directories in the output base
    directories = [
        d for d in output_base.iterdir() if d.is_dir() and not d.name.startswith(".")
    ]

    # Group directories by potential document matches
    filename_dirs = {}  # e.g., "goog-10-k-2024" -> Path
    docid_dirs = {}  # e.g., "goog_2024" -> Path

    for directory in directories:
        name = directory.name
        if "_" in name and not "-" in name:
            # Likely doc_id format (underscore, no hyphens)
            docid_dirs[name] = directory
        elif "-" in name:
            # Likely filename format (hyphens)
            filename_dirs[name] = directory

    # Try to match and consolidate
    for docid_name, docid_path in docid_dirs.items():
        # Look for corresponding filename directory
        # Convert goog_2024 -> look for goog-*-2024 pattern
        parts = docid_name.split("_")
        if len(parts) >= 2:
            prefix = parts[0]
            year = parts[-1]

            # Find matching filename directory
            matching_filename = None
            for filename_name, filename_path in filename_dirs.items():
                if filename_name.startswith(prefix) and year in filename_name:
                    matching_filename = filename_path
                    break

            if matching_filename:
                print(f"🔄 Consolidating {docid_name} -> {matching_filename.name}")

                # Move all contents from docid directory to filename directory
                for item in docid_path.iterdir():
                    dest = matching_filename / item.name
                    if dest.exists():
                        print(f"   ⚠️  Merging {item.name} (destination exists)")
                        if item.is_dir():
                            shutil.copytree(item, dest, dirs_exist_ok=True)
                        else:
                            # For files, keep the newer one
                            if item.stat().st_mtime > dest.stat().st_mtime:
                                shutil.copy2(item, dest)
                    else:
                        shutil.move(str(item), str(dest))

                # Remove empty docid directory
                try:
                    docid_path.rmdir()
                    print(f"   ✅ Removed empty directory {docid_name}")
                    consolidated += 1
                except OSError:
                    print(f"   ⚠️  Could not remove {docid_name} (not empty)")
            else:
                print(f"   ℹ️  No matching filename directory found for {docid_name}")

    if consolidated > 0:
        print(f"\n✅ Successfully consolidated {consolidated} directory pairs")
    else:
        print("\nℹ️  No directories needed consolidation")

    return True


def main():
    if len(sys.argv) != 2:
        print("Usage: python fix_directory_naming.py <output_directory>")
        print("Example: python fix_directory_naming.py data/parsed")
        sys.exit(1)

    output_dir = sys.argv[1]
    success = consolidate_output_directories(output_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
