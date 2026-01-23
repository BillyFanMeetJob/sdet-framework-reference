import os

# 設定您要掃描的專案資料夾路徑 ('.' 代表當前目錄)
root_dir = '.' 
output_file = 'all_code.txt'

# 設定要忽略的資料夾 (避免檔案過大)
ignore_dirs = {'.git', '__pycache__', 'node_modules', 'venv', 'bin', 'obj', 'target'}
# 設定要讀取的副檔名 (根據您的專案修改)
extensions = {'.py', '.js', '.html', '.css', '.java', '.cs', '.cpp', '.h', '.md'}

with open(output_file, 'w', encoding='utf-8') as outfile:
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # 移除忽略的資料夾
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
        
        for filename in filenames:
            if any(filename.endswith(ext) for ext in extensions):
                filepath = os.path.join(dirpath, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as infile:
                        outfile.write(f"\n\n{'='*20}\nFILE: {filepath}\n{'='*20}\n\n")
                        outfile.write(infile.read())
                except Exception as e:
                    print(f"Skipping {filename}: {e}")

print(f"完成！請上傳 {output_file}")