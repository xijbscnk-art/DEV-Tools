import os
import sys
import argparse
from pathlib import Path

def generate_tree(path, prefix="", level=0, max_depth=None, ignore_dirs=None):
    """
    Рекурсивно генерирует строки древовидной структуры.

    Аргументы:
        path: путь к директории
        prefix: префикс для текущего уровня (для отступов)
        level: текущая глубина
        max_depth: максимальная глубина (None - без ограничений)
        ignore_dirs: список имён папок, которые нужно игнорировать
    """
    if max_depth is not None and level >= max_depth:
        return

    # Получаем список элементов в директории
    try:
        items = os.listdir(path)
    except PermissionError:
        yield f"{prefix}[Нет доступа]"
        return
    except OSError as e:
        yield f"{prefix}[Ошибка: {e}]"
        return

    # Фильтруем игнорируемые папки
    if ignore_dirs:
        items = [i for i in items if not (os.path.isdir(os.path.join(path, i)) and i in ignore_dirs)]

    # Сортируем по имени (регистронезависимо для удобства)
    items.sort(key=str.lower)

    # Разделяем на файлы и папки (необязательно, можно просто отсортировать)
    # В классическом tree папки и файлы перемешаны, оставим так.

    for idx, item in enumerate(items):
        item_path = os.path.join(path, item)
        is_last = (idx == len(items) - 1)

        # Определяем символы для текущего элемента
        if is_last:
            current_prefix = "└── "
            next_prefix = "    "
        else:
            current_prefix = "├── "
            next_prefix = "│   "

        # Выводим элемент
        yield f"{prefix}{current_prefix}{item}"

        # Если это папка, рекурсивно обходим её
        if os.path.isdir(item_path):
            yield from generate_tree(
                item_path,
                prefix + next_prefix,
                level + 1,
                max_depth,
                ignore_dirs
            )

def main():
    parser = argparse.ArgumentParser(
        description="Вывод древовидной структуры папки",
        add_help=False
    )
    parser.add_argument("path", nargs="?", default=".",
                        help="Путь к папке (по умолчанию текущая)")
    parser.add_argument("-o", "--output", help="Файл для записи результата")
    parser.add_argument("-d", "--depth", type=int, help="Максимальная глубина")
    parser.add_argument("-i", "--ignore", action="append", default=[],
                        help="Игнорировать указанную папку (можно несколько раз)")
    parser.add_argument("-h", "--help", action="help", help="Показать это сообщение")

    args = parser.parse_args()

    root_path = os.path.abspath(args.path)
    if not os.path.exists(root_path):
        print(f"Ошибка: путь '{root_path}' не существует.", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(root_path):
        print(f"Ошибка: '{root_path}' не является папкой.", file=sys.stderr)
        sys.exit(1)

    # Генерируем дерево
    lines = []
    lines.append(root_path)  # корневая папка
    lines.extend(generate_tree(root_path, max_depth=args.depth, ignore_dirs=args.ignore))

    # Выводим результат
    output = "\n".join(lines)
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
        except Exception as e:
            print(f"Ошибка записи в файл: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(output)

if __name__ == "__main__":
    main()
