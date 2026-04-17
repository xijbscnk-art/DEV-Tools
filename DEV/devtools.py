#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import subprocess
from datetime import datetime

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    from rich.prompt import Prompt
    from pyfiglet import Figlet
except ImportError:
    print("Установи зависимости: pip install rich pyfiglet")
    sys.exit(1)

from scaffold import parse_structure, create_structure
from sysinfo import (
    get_os_info, get_cpu_info, get_ram_info,
    get_gpu_info, get_motherboard_info
)
from treeview import generate_tree
from clean import clean_directory
from password_manager import password_manager, verify_master_password, is_first_run, save_data

console = Console()
MASTER_PASSWORD = None

def show_banner():
    console.clear()
    f = Figlet(font='speed')
    ascii_art = f.renderText('D.E.V.')
    console.print(ascii_art, style="bold red")
    
    console.print(Panel.fit(
        "[bold yellow]DEBUG  EXPLORE  VANQUISH[/]\n"
    ))
    
    console.print("[dim]>> SysInfo | Scaffolder | TreeView | Clean | Password | Test <<[/]\n")

def fake_loading(duration=1.5):
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("[cyan]Инициализация протоколов...", total=100)
        for _ in range(100):
            time.sleep(duration / 100)
            progress.update(task, advance=1)

def show_system_snapshot():
    os_info = get_os_info()
    cpu_info = get_cpu_info()
    ram_info = get_ram_info()
    mb_info = get_motherboard_info()

    table = Table(title="[bold]СИСТЕМНАЯ СВОДКА[/]", border_style="bright_blue")
    table.add_column("Параметр", style="cyan", no_wrap=True)
    table.add_column("Значение", style="green")

    table.add_row("Хост", os_info['hostname'])
    table.add_row("ОС", f"{os_info['system']} {os_info['release']}")
    table.add_row("Процессор", cpu_info['brand'])
    table.add_row("Ядра", f"{cpu_info['physical_cores']} физ. / {cpu_info['logical_cores']} лог.")
    table.add_row("Частота", f"{cpu_info['max_freq_mhz']:.0f} МГц" if cpu_info['max_freq_mhz'] else "N/A")
    table.add_row("ОЗУ", f"{ram_info['total_gb']:.1f} ГБ (исп. {ram_info['percent']}%)")
    if mb_info:
        table.add_row("Материнка", f"{mb_info.get('manufacturer', '')} {mb_info.get('model', '')}")

    console.print(table)

def authenticate():
    global MASTER_PASSWORD
    console.clear()
    show_banner()
    
    if is_first_run():
        console.print("\n[bold yellow]🔐 Первый запуск DevTools.[/]")
        console.print("[dim]Придумайте мастер-пароль для доступа к защищённым функциям (менеджер паролей).[/]")
        console.print("[dim red]⚠️  Если забудете пароль, восстановить данные будет невозможно![/]\n")
        pwd = Prompt.ask("Придумайте мастер-пароль", password=True)
        pwd2 = Prompt.ask("Подтвердите мастер-пароль", password=True)
        if pwd != pwd2:
            console.print("[red]Пароли не совпадают![/]")
            return False
        save_data({}, pwd)
        console.print("[green]✅ Мастер-пароль установлен.[/]")
        MASTER_PASSWORD = pwd
        time.sleep(1.5)
        return True
    else:
        pwd = Prompt.ask("\n[bold]Введите мастер-пароль[/]", password=True)
        if verify_master_password(pwd):
            MASTER_PASSWORD = pwd
            return True
        else:
            console.print("[red]❌ Неверный мастер-пароль![/]")
            return False

def scaffold_tool():
    console.clear()
    show_banner()
    console.print("\n[bold]📁 SCAFFOLDER — создание структуры проекта[/]")
    console.print("Введите текстовое описание структуры (пустая строка — конец ввода):")
    lines = []
    while True:
        line = input()
        if line == '':
            break
        lines.append(line)

    if not lines:
        console.print("[red]Пустой ввод, отмена.[/]")
        return

    structure_text = '\n'.join(lines)
    root_dir, structure = parse_structure(structure_text)
    create_structure(root_dir, structure)
    console.print(f"[green]✅ Структура создана в папке: {root_dir}[/]")

def sysinfo_tool():
    console.clear()
    show_banner()
    console.print("\n[bold]💻 SYSINFO — полный отчёт о системе[/]")
    from sysinfo import main as sysinfo_main
    sysinfo_main()

def tree_tool():
    console.clear()
    show_banner()
    console.print("\n[bold]🌲 TREEVIEW — дерево файлов и папок[/]")
    path = console.input("[cyan]Введите путь к папке (Enter = текущая): [/]") or "."
    depth_str = console.input("[cyan]Максимальная глубина (Enter = без ограничений): [/]")
    depth = int(depth_str) if depth_str.strip() else None
    ignore_input = console.input("[cyan]Игнорировать папки через запятую (например: .git,node_modules): [/]")
    ignore_dirs = [d.strip() for d in ignore_input.split(',') if d.strip()] if ignore_input else []
    output_file = console.input("[cyan]Сохранить в файл (Enter = только на экран): [/]") or None

    lines = [os.path.abspath(path)]
    lines.extend(generate_tree(path, max_depth=depth, ignore_dirs=ignore_dirs))
    output = "\n".join(lines)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)
        console.print(f"[green]✅ Результат сохранён в {output_file}[/]")
    else:
        console.print(output)

def clean_tool():
    console.clear()
    show_banner()
    console.print("\n[bold]🧹 CLEAN — очистка мусорных файлов[/]")
    path = console.input("[cyan]Введите путь к папке (Enter = текущая): [/]") or "."
    dry_run = console.input("[cyan]Только показать (dry run)? (y/N): [/]").lower() == 'y'
    include_venv = console.input("[cyan]Удалять виртуальные окружения .venv/venv? (y/N): [/]").lower() == 'y'

    dirs, files = clean_directory(path, dry_run, include_venv)

    if dry_run:
        console.print(f"\n[bold]Будет удалено:[/] папок {len(dirs)}, файлов {len(files)}")
    else:
        console.print(f"\n[green]✅ Очистка завершена. Удалено папок: {len(dirs)}, файлов: {len(files)}[/]")

def password_tool():
    console.clear()
    show_banner()
    password_manager(MASTER_PASSWORD)

def run_tests():
    console.clear()
    show_banner()
    console.print("\n[bold]🧪 TEST RUNNER — запуск тестов проекта[/]\n")
    
    try:
        import pytest
    except ImportError:
        console.print("[yellow]pytest не установлен. Установить? (y/n)[/]")
        if console.input().lower() == 'y':
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest"])
            console.print("[green]pytest установлен.[/]")
        else:
            console.print("[red]Без pytest тесты не запустить.[/]")
            return
    
    console.print("[cyan]Запуск тестов...[/]\n")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "--color=yes"],
        capture_output=False,
        text=True
    )
    
    if result.returncode == 0:
        console.print("\n[green]✅ Все тесты пройдены успешно![/]")
    else:
        console.print("\n[red]❌ Некоторые тесты упали.[/]")


def main_menu():
    while True:
        console.print("\n" + "═" * 50)
        console.print("[bold yellow]ГЛАВНОЕ МЕНЮ[/]")
        console.print("[1] 📁 Scaffolder — создать структуру папок")
        console.print("[2] 💻 SysInfo — информация о системе")
        console.print("[3] 🌲 TreeView — дерево папок")
        console.print("[4] 🧹 Clean — очистка мусора")
        console.print("[5] 🔐 Password Manager — генератор и хранитель паролей")
        console.print("[6] 🧪 Test Runner — запустить тесты проекта")
        console.print("[0] 🚪 Выход")
        choice = console.input("[bold green]Выберите инструмент (0-6): [/]")

        if choice == "1":
            scaffold_tool()
        elif choice == "2":
            sysinfo_tool()
        elif choice == "3":
            tree_tool()
        elif choice == "4":
            clean_tool()
        elif choice == "5":
            password_tool()
        elif choice == "6":
            run_tests()
        elif choice == "0":
            console.clear()
            console.print("[bold red]Выход... До свидания![/]")
            time.sleep(1)
            console.clear()
            sys.exit(0)
        else:
            console.print("[red]Неверный выбор, попробуйте снова.[/]")
            time.sleep(1)
            console.clear()
            show_banner()
            continue

        input("\n[dim]Нажмите Enter для возврата в меню...[/]")
        console.clear()
        show_banner()

def main():
    console.clear()
    show_banner()
    fake_loading(1.5)
    console.clear()
    show_banner()
    show_system_snapshot()
    
    if not authenticate():
        console.print("[bold red]Доступ запрещён. Завершение работы.[/]")
        time.sleep(2)
        console.clear()
        sys.exit(1)
    
    console.clear()
    show_banner()
    main_menu()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.clear()
        console.print("\n[bold red]Прервано пользователем.[/]")
        time.sleep(1)
        console.clear()
        sys.exit(0)