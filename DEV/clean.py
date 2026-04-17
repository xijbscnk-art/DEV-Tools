#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import fnmatch
import argparse
from pathlib import Path

TRASH_PATTERNS = [
    '__pycache__',
    '*.pyc',
    '*.pyo',
    '.pytest_cache',
    '.mypy_cache',
    '.ruff_cache',
    '.tox',
    '.eggs',
    '*.egg-info',
    'build',
    'dist',
    '*.log',
    '.DS_Store',
    'Thumbs.db',
]

def clean_directory(path='.', dry_run=False, include_venv=False):
    removed_dirs = []
    removed_files = []

    for root, dirs, files in os.walk(path, topdown=True):
        if not include_venv:
            if os.path.basename(root) in ['.venv', 'venv']:
                continue

        for pattern in TRASH_PATTERNS:
            if '*' not in pattern:
                if pattern in dirs:
                    full = os.path.join(root, pattern)
                    if dry_run:
                        print(f'[DIR]  {full}')
                    else:
                        try:
                            shutil.rmtree(full)
                            removed_dirs.append(full)
                        except Exception as e:
                            print(f'[ERROR] Не удалось удалить {full}: {e}')
                    dirs.remove(pattern)

        for pattern in TRASH_PATTERNS:
            if '*' in pattern:
                for filename in fnmatch.filter(files, pattern):
                    full = os.path.join(root, filename)
                    if dry_run:
                        print(f'[FILE] {full}')
                    else:
                        try:
                            os.remove(full)
                            removed_files.append(full)
                        except Exception as e:
                            print(f'[ERROR] Не удалось удалить {full}: {e}')

    return removed_dirs, removed_files

def main():
    parser = argparse.ArgumentParser(
        description='Удаление временных и мусорных файлов в проекте'
    )
    parser.add_argument('path', nargs='?', default='.',
                        help='Путь к папке (по умолчанию текущая)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Только показать, что будет удалено')
    parser.add_argument('--include-venv', action='store_true',
                        help='Удалять также папки .venv/venv (ОСТОРОЖНО!)')
    args = parser.parse_args()

    path = os.path.abspath(args.path)
    if not os.path.isdir(path):
        print(f'Ошибка: {path} не является папкой.')
        return

    print(f"Очистка папки: {path}")
    if args.dry_run:
        print("Режим DRY RUN — файлы не удаляются.\n")

    dirs, files = clean_directory(path, args.dry_run, args.include_venv)

    if args.dry_run:
        print(f"\nБудет удалено папок: {len(dirs)}, файлов: {len(files)}")
    else:
        print(f"\n✅ Удалено папок: {len(dirs)}, файлов: {len(files)}")

if __name__ == "__main__":
    main()