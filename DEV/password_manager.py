#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import secrets
import string
import base64
import hashlib
import time
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

DATA_FILE = Path.home() / ".devtools_passwords.enc"
SALT_FILE = Path.home() / ".devtools_salt"

# -------------------------------------------------------------------
# КРИПТОГРАФИЯ
# -------------------------------------------------------------------
def generate_salt() -> bytes:
    return os.urandom(16)

def get_salt() -> bytes:
    if SALT_FILE.exists():
        return SALT_FILE.read_bytes()
    else:
        salt = generate_salt()
        SALT_FILE.write_bytes(salt)
        return salt

def derive_key_from_password(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = kdf.derive(password.encode('utf-8'))
    return base64.urlsafe_b64encode(key)

def get_cipher(password: str) -> Fernet:
    salt = get_salt()
    key = derive_key_from_password(password, salt)
    return Fernet(key)

def load_data(password: str) -> dict | None:
    if not DATA_FILE.exists():
        return {}
    try:
        cipher = get_cipher(password)
        with open(DATA_FILE, 'rb') as f:
            encrypted = f.read()
        decrypted = cipher.decrypt(encrypted)
        return json.loads(decrypted.decode('utf-8'))
    except (InvalidToken, Exception):
        return None

def save_data(data: dict, password: str):
    cipher = get_cipher(password)
    json_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
    encrypted = cipher.encrypt(json_bytes)
    with open(DATA_FILE, 'wb') as f:
        f.write(encrypted)

def is_first_run() -> bool:
    return not DATA_FILE.exists()

def verify_master_password(password: str) -> bool:
    if not DATA_FILE.exists():
        return False
    data = load_data(password)
    return data is not None

# -------------------------------------------------------------------
# ГЕНЕРАТОР ПАРОЛЕЙ
# -------------------------------------------------------------------
def generate_password(length=16, use_digits=True, use_special=True, use_upper=True):
    alphabet = string.ascii_lowercase
    if use_upper:
        alphabet += string.ascii_uppercase
    if use_digits:
        alphabet += string.digits
    if use_special:
        alphabet += "!@#$%^&*()_+-=[]{}|;:,.<>?"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def loading_animation(message="Загрузка", duration=1.0):
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(f"[cyan]{message}...", total=100)
        for _ in range(100):
            time.sleep(duration / 100)
            progress.update(task, advance=1)

# -------------------------------------------------------------------
# ИНТЕРФЕЙС МЕНЕДЖЕРА ПАРОЛЕЙ
# -------------------------------------------------------------------
def view_passwords(master_password: str):
    console.clear()
    console.print("[bold]🔍 ПРОСМОТР ПАРОЛЕЙ[/]\n")
    data = load_data(master_password)
    if not data:
        console.print("[dim]Нет сохранённых паролей.[/]")
        return

    table = Table(title="Сохранённые пароли", border_style="bright_blue")
    table.add_column("Название", style="cyan")
    table.add_column("Пароль", style="green")
    for name, pwd in data.items():
        table.add_row(name, pwd)
    console.print(table)

def generate_and_save(master_password: str):
    console.clear()
    console.print("[bold]🔐 ГЕНЕРАТОР ПАРОЛЕЙ[/]\n")

    length = int(Prompt.ask("Длина пароля", default="16"))
    use_digits = Confirm.ask("Использовать цифры?", default=True)
    use_special = Confirm.ask("Использовать спецсимволы?", default=True)
    use_upper = Confirm.ask("Использовать заглавные буквы?", default=True)

    while True:
        password = generate_password(length, use_digits, use_special, use_upper)
        console.print(f"\n[bold green]Сгенерирован пароль:[/] [bold white on black]{password}[/]\n")

        choice = Prompt.ask("Что делаем?", choices=["сохранить", "пересоздать", "выйти"])
        if choice == "сохранить":
            name = Prompt.ask("Введите название (например, 'Gmail')")
            data = load_data(master_password)
            data[name] = password
            save_data(data, master_password)
            console.print(f"[green]✅ Пароль '{name}' сохранён.[/]")
            break
        elif choice == "пересоздать":
            continue
        else:
            break

def password_manager(master_password: str):
    console.clear()
    console.print("[bold]🔐 PASSWORD MANAGER[/]\n")

    while True:
        console.print("[1] 🔍 Просмотреть сохранённые пароли")
        console.print("[2] 🔑 Сгенерировать новый пароль")
        console.print("[0] 🚪 Выход в главное меню")

        choice = Prompt.ask("Выберите действие", choices=["0", "1", "2"])

        if choice == "1":
            loading_animation("Расшифровка базы", 0.8)
            view_passwords(master_password)
        elif choice == "2":
            generate_and_save(master_password)
        elif choice == "0":
            break

        if choice in ("1", "2"):
            input("\n[dim]Нажмите Enter для продолжения...[/]")
            console.clear()
            console.print("[bold]🔐 PASSWORD MANAGER[/]\n")

# -------------------------------------------------------------------
# ПРЯМОЙ ЗАПУСК
# -------------------------------------------------------------------
if __name__ == "__main__":
    console.print("[bold]🔐 PASSWORD MANAGER (standalone)[/]\n")
    if is_first_run():
        console.print("[red]Сначала запустите devtools.py для инициализации мастер-пароля.[/]")
        sys.exit(1)
    pwd = Prompt.ask("Введите мастер-пароль", password=True)
    if verify_master_password(pwd):
        password_manager(pwd)
    else:
        console.print("[red]Неверный пароль![/]")
        sys.exit(1)