"""
座標提取工具
自動從測試日誌中提取成功辨識的元件座標，並生成座標庫文檔
"""

import re
import sys
from pathlib import Path
from collections import defaultdict

def extract_coordinates_from_log(log_file_path):
    """
    從日誌文件中提取座標資訊
    返回格式: [(image_path, x_ratio, y_ratio, window_size, abs_coords), ...]
    """
    coordinates = []
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 匹配圖片辨識成功的記錄
        # 範例：
        # >>> 📸 圖片辨識成功並點擊: desktop_login/server_tile.png
        # >>> 📊 [座標庫] 比例座標: x_ratio=0.5234, y_ratio=0.3891 | 視窗尺寸: 1280x720 | 絕對座標: (640, 280)
        pattern_img = r'📸 圖片辨識成功並點擊: (.*?)\n.*?\[座標庫\] 比例座標: x_ratio=([\d.]+), y_ratio=([\d.]+) \| 視窗尺寸: (\d+x\d+) \| 絕對座標: \((\d+), (\d+)\)'
        
        for match in re.finditer(pattern_img, content):
            image_path = match.group(1).strip()
            x_ratio = float(match.group(2))
            y_ratio = float(match.group(3))
            window_size = match.group(4)
            abs_x = int(match.group(5))
            abs_y = int(match.group(6))
            
            coordinates.append({
                'type': 'image',
                'identifier': image_path,
                'x_ratio': x_ratio,
                'y_ratio': y_ratio,
                'window_size': window_size,
                'abs_coords': (abs_x, abs_y)
            })
        
        # 匹配 OCR 辨識成功的記錄
        # 範例：
        # >>> 📝 OCR 文字辨識成功並點擊: 繁體中文
        # >>> 📊 [座標庫] 比例座標: x_ratio=0.4562, y_ratio=0.5123 | 視窗尺寸: 1280x720 | 絕對座標: (584, 369)
        pattern_ocr = r'📝 OCR 文字辨識成功並點擊: (.*?)\n.*?\[座標庫\] 比例座標: x_ratio=([\d.]+), y_ratio=([\d.]+) \| 視窗尺寸: (\d+x\d+) \| 絕對座標: \((\d+), (\d+)\)'
        
        for match in re.finditer(pattern_ocr, content):
            text = match.group(1).strip()
            x_ratio = float(match.group(2))
            y_ratio = float(match.group(3))
            window_size = match.group(4)
            abs_x = int(match.group(5))
            abs_y = int(match.group(6))
            
            coordinates.append({
                'type': 'ocr',
                'identifier': text,
                'x_ratio': x_ratio,
                'y_ratio': y_ratio,
                'window_size': window_size,
                'abs_coords': (abs_x, abs_y)
            })
        
        return coordinates
        
    except FileNotFoundError:
        print(f"❌ 找不到日誌文件: {log_file_path}")
        return []
    except Exception as e:
        print(f"❌ 解析日誌時發生錯誤: {e}")
        return []

def categorize_by_page(coordinates):
    """
    根據圖片路徑將座標分類到不同頁面
    """
    categorized = defaultdict(list)
    
    for coord in coordinates:
        if coord['type'] == 'image':
            # 從路徑中提取頁面名稱
            # 例如: desktop_login/server_tile.png -> desktop_login
            path = coord['identifier']
            page_name = path.split('/')[0] if '/' in path else 'unknown'
            categorized[page_name].append(coord)
        else:
            # OCR 辨識的暫時放在 'ocr' 分類
            categorized['ocr'].append(coord)
    
    return categorized

def generate_markdown_table(categorized_coords):
    """
    生成 Markdown 格式的座標庫表格
    """
    # 頁面名稱映射（中文）
    page_names = {
        'desktop_login': '🔐 登入頁面',
        'desktop_main': '🏠 主頁面',
        'desktop_settings': '⚙️ 設置頁面',
        'ocr': '📝 OCR 辨識元件'
    }
    
    markdown = "# 🎯 UI 元件座標庫\n\n"
    markdown += "> 本文件由 `scripts/extract_coordinates.py` 自動生成\n"
    markdown += "> 最後更新: 自動化測試運行時\n\n"
    markdown += "---\n\n"
    
    for page_key, coords in sorted(categorized_coords.items()):
        page_title = page_names.get(page_key, f'📄 {page_key}')
        markdown += f"## {page_title}\n\n"
        
        # 表格標題
        markdown += "| 元件識別 | 類型 | x_ratio | y_ratio | 測試視窗 | 絕對座標 |\n"
        markdown += "|---------|------|---------|---------|---------|----------|\n"
        
        # 表格內容
        for coord in coords:
            identifier = coord['identifier']
            coord_type = '🖼️ 圖片' if coord['type'] == 'image' else '📝 OCR'
            x_ratio = f"{coord['x_ratio']:.4f}"
            y_ratio = f"{coord['y_ratio']:.4f}"
            window_size = coord['window_size']
            abs_coords = f"({coord['abs_coords'][0]}, {coord['abs_coords'][1]})"
            
            # 簡化圖片路徑顯示
            if coord['type'] == 'image':
                display_name = identifier.split('/')[-1].replace('.png', '')
            else:
                display_name = identifier
            
            markdown += f"| {display_name} | {coord_type} | {x_ratio} | {y_ratio} | {window_size} | {abs_coords} |\n"
        
        markdown += "\n"
    
    return markdown

def generate_python_dict(categorized_coords):
    """
    生成 Python 字典格式的座標庫
    """
    python_code = "# UI 元件座標字典\n"
    python_code += "# 可直接 import 使用\n\n"
    python_code += "COORD_LIBRARY = {\n"
    
    for page_key, coords in sorted(categorized_coords.items()):
        python_code += f"    '{page_key}': {{\n"
        
        for coord in coords:
            identifier = coord['identifier']
            # 生成友好的 key 名稱
            if coord['type'] == 'image':
                key_name = identifier.split('/')[-1].replace('.png', '').replace('-', '_')
            else:
                key_name = identifier.replace(' ', '_')
            
            python_code += f"        '{key_name}': {{\n"
            python_code += f"            'x_ratio': {coord['x_ratio']:.4f},\n"
            python_code += f"            'y_ratio': {coord['y_ratio']:.4f},\n"
            python_code += f"            'window_size': '{coord['window_size']}',\n"
            python_code += f"            'type': '{coord['type']}'\n"
            python_code += f"        }},\n"
        
        python_code += "    },\n"
    
    python_code += "}\n"
    
    return python_code

def main():
    """主函數"""
    print("🎯 座標提取工具啟動\n")
    
    # 檢查命令行參數
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        # 預設使用最新的日誌文件
        log_file = Path(__file__).parent.parent / "logs" / "automation.log"
    
    print(f"📂 讀取日誌文件: {log_file}\n")
    
    # 提取座標
    coordinates = extract_coordinates_from_log(log_file)
    
    if not coordinates:
        print("⚠️ 未找到任何座標記錄")
        print("💡 請確保:")
        print("   1. 已執行測試並生成日誌")
        print("   2. 日誌中包含 📊 [座標庫] 標記")
        print("   3. 使用了優化後的 DesktopApp.smart_click()")
        return
    
    print(f"✅ 成功提取 {len(coordinates)} 個座標記錄\n")
    
    # 按頁面分類
    categorized = categorize_by_page(coordinates)
    
    print("📊 座標分類統計:")
    for page, coords in categorized.items():
        print(f"   - {page}: {len(coords)} 個元件")
    print()
    
    # 生成 Markdown 文檔
    markdown_output = generate_markdown_table(categorized)
    output_md_file = Path(__file__).parent.parent / "座標庫.md"
    with open(output_md_file, 'w', encoding='utf-8') as f:
        f.write(markdown_output)
    print(f"✅ 已生成 Markdown 座標庫: {output_md_file}\n")
    
    # 生成 Python 字典
    python_output = generate_python_dict(categorized)
    output_py_file = Path(__file__).parent.parent / "coord_library.py"
    with open(output_py_file, 'w', encoding='utf-8') as f:
        f.write(python_output)
    print(f"✅ 已生成 Python 座標庫: {output_py_file}\n")
    
    # 顯示示例用法
    print("📖 使用示例:\n")
    print("```python")
    print("from coord_library import COORD_LIBRARY")
    print()
    print("# 使用座標庫中的值")
    print("coord = COORD_LIBRARY['desktop_login']['server_tile']")
    print("x_ratio = coord['x_ratio']")
    print("y_ratio = coord['y_ratio']")
    print()
    print("self.app.smart_click(")
    print("    x_ratio=x_ratio,")
    print("    y_ratio=y_ratio,")
    print("    image_path='desktop_login/server_tile.png'")
    print(")")
    print("```")
    print()
    print("🎉 完成！")

if __name__ == "__main__":
    main()
