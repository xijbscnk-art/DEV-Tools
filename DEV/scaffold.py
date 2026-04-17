import os
import re

def parse_structure(structure_text):
    lines = structure_text.strip().split('\n')
    root_dir = lines[0].split('/')[0].strip()
    structure = []
    
    for line in lines[1:]:
        if not line.strip():
            continue
            
        # Определяем уровень вложенности по отступам
        indent_match = re.match(r'^[│├└\s]*', line)
        indent_level = len(indent_match.group()) // 4 if indent_match.group() else 0
        
        # Извлекаем имя файла/папки
        name_match = re.search(r'[├└]──\s*([^#]+)', line)
        if name_match:
            name = name_match.group(1).split('#')[0].strip()
            structure.append((indent_level, name))
    
    return root_dir, structure

def create_structure(root_dir, structure):
    if not os.path.exists(root_dir):
        os.makedirs(root_dir)
    
    current_path = [root_dir]
    
    for indent_level, name in structure:
        # Возвращаемся на нужный уровень вложенности
        while len(current_path) > indent_level + 1:
            current_path.pop()
        
        full_path = os.path.join(*current_path, name)
        
        if name.endswith('/') or '.' not in os.path.basename(name):
            # Это папка
            os.makedirs(full_path, exist_ok=True)
            current_path.append(name)
        else:
            # Это файл
            dir_path = os.path.dirname(full_path)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            open(full_path, 'a').close()

def main():
    print("Введите структуру файлов (завершите ввод пустой строкой):")
    lines = []
    while True:
        line = input()
        if line == '':
            break
        lines.append(line)
    
    structure_text = '\n'.join(lines)
    root_dir, structure = parse_structure(structure_text)
    
    create_structure(root_dir, structure)
    print(f"Структура создана в папке: {root_dir}")

if __name__ == "__main__":
    main()
