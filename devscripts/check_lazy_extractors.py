#!/usr/bin/env python3

# Allow direct execution
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import glob
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description='Check if lazy_extractors.py is up to date with extractor files')
    parser.add_argument('--print-stale', action='store_true',
                        help='Print names of stale files')
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    lazy_extractors_path = repo_root / 'yt_dlp' / 'extractor' / 'lazy_extractors.py'

    if not lazy_extractors_path.exists():
        print('lazy_extractors.py does not exist. Please run "make lazy-extractors" or "python devscripts/make_lazy_extractors.py"')
        return 1

    lazy_extractors_mtime = lazy_extractors_path.stat().st_mtime

    # Find all extractor Python files except lazy_extractors.py
    extractor_pattern = str(repo_root / 'yt_dlp' / 'extractor' / '*.py')
    extractor_files = [
        path for path in glob.glob(extractor_pattern)
        if not path.endswith('lazy_extractors.py')
    ]

    stale_files = []
    for extractor_file in extractor_files:
        extractor_path = Path(extractor_file)
        if extractor_path.stat().st_mtime > lazy_extractors_mtime:
            stale_files.append(extractor_path.name)

    if stale_files:
        print(f'lazy_extractors.py is stale! {len(stale_files)} extractor file(s) are newer.')
        if args.print_stale:
            print('Stale files:')
            for file in sorted(stale_files):
                print(f'  {file}')
        print('\nPlease run: python devscripts/make_lazy_extractors.py')
        return 1

    print('lazy_extractors.py is up to date.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
