"""
測試新的參考圖片能否正確匹配
"""
import pyautogui
from PIL import Image

# 讀取測試用的 haystack（實際截取的 80x80 區域）
checked_haystack = Image.open("debug_checkbox_1768405084.png")  # 已勾選的實際截圖
unchecked_haystack = Image.open("debug_checkbox_1768405085.png")  # 未勾選的實際截圖

# 儲存為臨時檔案供 pyautogui 使用
checked_haystack.save("test_haystack_checked.png")
unchecked_haystack.save("test_haystack_unchecked.png")

# 讀取參考圖片 (needle)
checked_ref = "res/desktop_settings/checkbox_checked.png"
unchecked_ref = "res/desktop_settings/checkbox_unchecked.png"

print("=== Test 1: Find in CHECKED screenshot ===")
print("\n1. Looking for checkbox_checked.png (should MATCH):")
try:
    result = pyautogui.locate(checked_ref, "test_haystack_checked.png", confidence=0.8)
    print(f"   Result: {result} - MATCH!")
except:
    print(f"   Result: None - NO MATCH")

print("\n2. Looking for checkbox_unchecked.png (should NOT match):")
try:
    result = pyautogui.locate(unchecked_ref, "test_haystack_checked.png", confidence=0.8)
    print(f"   Result: {result} - MATCH (WRONG!)")
except:
    print(f"   Result: None - NO MATCH (CORRECT!)")

print("\n" + "="*50)
print("=== Test 2: Find in UNCHECKED screenshot ===")
print("\n1. Looking for checkbox_checked.png (should NOT match):")
try:
    result = pyautogui.locate(checked_ref, "test_haystack_unchecked.png", confidence=0.8)
    print(f"   Result: {result} - MATCH (WRONG!)")
except:
    print(f"   Result: None - NO MATCH (CORRECT!)")

print("\n2. Looking for checkbox_unchecked.png (should MATCH):")
try:
    result = pyautogui.locate(unchecked_ref, "test_haystack_unchecked.png", confidence=0.8)
    print(f"   Result: {result} - MATCH!")
except:
    print(f"   Result: None - NO MATCH")

print("\n" + "="*50)
print("Test with lower confidence (0.75):")
print("\n=== In CHECKED screenshot ===")
try:
    result = pyautogui.locate(unchecked_ref, "test_haystack_checked.png", confidence=0.75)
    print(f"unchecked_ref: {result} (confidence 0.75)")
except Exception as e:
    print(f"unchecked_ref: None (GOOD!)")

print("\n=== In UNCHECKED screenshot ===")
try:
    result = pyautogui.locate(checked_ref, "test_haystack_unchecked.png", confidence=0.75)
    print(f"checked_ref: {result} (confidence 0.75)")
except Exception as e:
    print(f"checked_ref: None (GOOD!)")
