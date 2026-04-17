#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для сбора информации о железе ПК под управлением Windows.
Использует: psutil, py-cpuinfo, wmi, а также nvidia-smi (если доступен).
"""

import platform
import socket
import sys
import os
import subprocess
from datetime import datetime

try:
    import psutil
except ImportError:
    print("Ошибка: требуется установить psutil. Выполните: pip install psutil")
    sys.exit(1)

try:
    import cpuinfo
except ImportError:
    print("Ошибка: требуется установить py-cpuinfo. Выполните: pip install py-cpuinfo")
    sys.exit(1)

try:
    import wmi
except ImportError:
    print("Ошибка: требуется установить wmi. Выполните: pip install wmi")
    sys.exit(1)


def get_os_info():
    """Возвращает информацию об ОС"""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "hostname": socket.gethostname(),
        "architecture": platform.machine(),
        "processor_arch": platform.processor() or "Unknown"
    }


def get_cpu_info():
    """Возвращает информацию о процессоре"""
    info = cpuinfo.get_cpu_info()
    cpu = {
        "brand": info.get("brand_raw", "Unknown"),
        "arch": info.get("arch", "Unknown"),
        "bits": info.get("bits", 0),
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "max_freq_mhz": psutil.cpu_freq().max if psutil.cpu_freq() else None,
        "current_freq_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None,
        "usage_percent": psutil.cpu_percent(interval=1)
    }
    return cpu


def get_ram_info():
    """Возвращает информацию об оперативной памяти"""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "total_gb": mem.total / (1024**3),
        "available_gb": mem.available / (1024**3),
        "used_gb": mem.used / (1024**3),
        "percent": mem.percent,
        "swap_total_gb": swap.total / (1024**3),
        "swap_used_gb": swap.used / (1024**3),
        "swap_percent": swap.percent
    }


def get_gpu_info():
    """Возвращает информацию о видеокартах (сначала через nvidia-smi, затем через WMI)"""
    gpu_list = []

    # Попытка через nvidia-smi
    try:
        output = subprocess.check_output(
            ['nvidia-smi', '--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu',
             '--format=csv,noheader,nounits'],
            encoding='utf-8'
        )
        lines = output.strip().split('\n')
        for line in lines:
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 6:
                gpu_list.append({
                    "name": parts[0],
                    "memory_total_mb": int(parts[1]),
                    "memory_used_mb": int(parts[2]),
                    "memory_free_mb": int(parts[3]),
                    "load_percent": int(parts[4]),
                    "temperature_celsius": int(parts[5])
                })
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Если nvidia-smi недоступен, пробуем через WMI
        try:
            c = wmi.WMI()
            for gpu in c.Win32_VideoController():
                memory = gpu.AdapterRAM
                memory_mb = memory // (1024**2) if memory else None
                gpu_list.append({
                    "name": gpu.Name,
                    "memory_total_mb": memory_mb,
                    "memory_used_mb": None,
                    "memory_free_mb": None,
                    "load_percent": None,
                    "temperature_celsius": None
                })
        except Exception:
            pass

    return gpu_list


def get_disk_info():
    """Возвращает информацию о дисках и разделах, включая модель и тип (SSD/HDD) через WMI"""
    disks = []
    # Получаем все физические диски через WMI
    c = wmi.WMI()
    physical_disks = {}
    try:
        for disk in c.Win32_DiskDrive():
            # Сопоставляем DeviceID (например, \\.\PHYSICALDRIVE0) с размером и моделью
            disk_id = disk.DeviceID.strip('\\').strip('.')
            physical_disks[disk_id] = {
                "model": disk.Model.strip() if disk.Model else "Unknown",
                "size_gb": int(disk.Size) / (1024**3) if disk.Size else 0,
                "type": "SSD" if "SSD" in disk.Model or "Solid State" in disk.Model else "HDD" if "HDD" in disk.Model else "Unknown"
            }
    except Exception:
        pass

    # Получаем информацию о разделах через psutil
    for part in psutil.disk_partitions():
        if 'cdrom' in part.opts or part.fstype == '':
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue

        disk = {
            "device": part.device,
            "mountpoint": part.mountpoint,
            "fstype": part.fstype,
            "total_gb": usage.total / (1024**3),
            "used_gb": usage.used / (1024**3),
            "free_gb": usage.free / (1024**3),
            "percent": usage.percent
        }

        # Попытка сопоставить раздел с физическим диском (упрощённо: ищем по букве диска)
        # На Windows device имеет вид "C:", ищем в строке диска
        for disk_id, info in physical_disks.items():
            # Примерное сопоставление: можно через Win32_LogicalDiskToPartition, но для простоты пропустим
            # Оставим только общую информацию о физических дисках отдельно
            pass

        disks.append(disk)

    # Добавляем отдельно список физических дисков с моделями
    if physical_disks:
        disks.append({"physical_disks": physical_disks})

    return disks


def get_motherboard_info():
    """Возвращает информацию о материнской плате через WMI"""
    try:
        c = wmi.WMI()
        board = c.Win32_BaseBoard()[0]
        bios = c.Win32_BIOS()[0]
        return {
            "manufacturer": board.Manufacturer.strip() if board.Manufacturer else "Unknown",
            "model": board.Product.strip() if board.Product else "Unknown",
            "version": board.Version.strip() if board.Version else "Unknown",
            "serial": board.SerialNumber.strip() if board.SerialNumber else "Unknown",
            "bios_version": bios.SMBIOSBIOSVersion.strip() if bios.SMBIOSBIOSVersion else "Unknown",
            "bios_date": bios.ReleaseDate.strip() if bios.ReleaseDate else "Unknown"
        }
    except Exception:
        return {}


def get_network_info():
    """Возвращает информацию о сетевых адаптерах"""
    networks = []
    for iface, addrs in psutil.net_if_addrs().items():
        ip = ipv6 = mac = None
        for addr in addrs:
            if addr.family == socket.AF_INET:
                ip = addr.address
            elif addr.family == socket.AF_INET6:
                ipv6 = addr.address
            elif addr.family == psutil.AF_LINK:
                mac = addr.address
        net = {"name": iface}
        if ip:
            net["ip"] = ip
        if ipv6:
            net["ipv6"] = ipv6
        if mac:
            net["mac"] = mac
        if net != {"name": iface}:  # если есть хоть какие-то адреса
            networks.append(net)
    return networks


def print_section(title, data):
    """Выводит секцию с данными в удобном формате"""
    print(f"\n{title}")
    print("-" * 50)
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, float):
                value = f"{value:.2f}"
            print(f"{key.replace('_', ' ').capitalize()}: {value}")
    elif isinstance(data, list):
        if not data:
            print("Нет данных")
        for i, item in enumerate(data):
            if isinstance(item, dict):
                # Специальная обработка для физических дисков
                if "physical_disks" in item:
                    print("\n  Физические диски:")
                    for disk_id, info in item["physical_disks"].items():
                        print(f"    {disk_id}: {info['model']} ({info['size_gb']:.1f} ГБ, {info['type']})")
                else:
                    print(f"\n  Элемент {i+1}:")
                    for k, v in item.items():
                        if isinstance(v, float):
                            v = f"{v:.2f}"
                        print(f"    {k.replace('_', ' ').capitalize()}: {v}")
            else:
                print(f"  {item}")
    else:
        print(data)


def main():
    print(f"Сбор информации о железе ПК ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print("=" * 50)

    print_section("ОПЕРАЦИОННАЯ СИСТЕМА", get_os_info())
    print_section("ПРОЦЕССОР", get_cpu_info())
    print_section("ОПЕРАТИВНАЯ ПАМЯТЬ", get_ram_info())
    print_section("ВИДЕОКАРТА", get_gpu_info())
    print_section("ДИСКИ И РАЗДЕЛЫ", get_disk_info())
    print_section("МАТЕРИНСКАЯ ПЛАТА", get_motherboard_info())
    print_section("СЕТЕВЫЕ АДАПТЕРЫ", get_network_info())

    print("\n" + "=" * 50)
    print("Сбор завершён.")


if __name__ == "__main__":
    main()