# Script para corregir los pandas.append deprecados en AWSocr.py
import re

def fix_pandas_append():
    file_path = r"c:\Users\maikel\Documents\GitHub\bnp-main\apirest\AWSocr.py"
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Reemplazar todas las instancias de .append con pd.concat
    # Patrón para encontrar df2.append(avgconf, ignore_index=True)
    pattern1 = r'df2 = df2\.append\(avgconf, ignore_index=True\)'
    replacement1 = 'df2 = pd.concat([df2, pd.DataFrame([avgconf])], ignore_index=True)'
    
    # Patrón para encontrar df.append(nuevo_registro, ignore_index=True)
    pattern2 = r'df = df\.append\(nuevo_registro, ignore_index=True\)'
    replacement2 = 'df = pd.concat([df, pd.DataFrame([nuevo_registro])], ignore_index=True)'
    
    # Aplicar reemplazos
    content = re.sub(pattern1, replacement1, content)
    content = re.sub(pattern2, replacement2, content)
    
    # También reemplazar df.append(comparar, ignore_index=True) si existe
    pattern3 = r'df = df\.append\(comparar, ignore_index=True\)'
    replacement3 = 'df = pd.concat([df, pd.DataFrame([comparar])], ignore_index=True)'
    content = re.sub(pattern3, replacement3, content)
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print("✅ Archivo AWSocr.py corregido")

if __name__ == "__main__":
    fix_pandas_append()
