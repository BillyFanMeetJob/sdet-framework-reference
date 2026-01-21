"""
測試 checkbox 圖片匹配
"""
import pyautogui
from PIL import Image
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

# 讀取最新的 debug 截圖（80x80）
debug_80 = Image.open("debug_checkbox_1768405084.png")
print(f"Debug 80x80 截圖: {debug_80.size}")

# 讀取參考圖片
checked_ref = Image.open("res/desktop_settings/checkbox_checked.png")
unchecked_ref = Image.open("res/desktop_settings/checkbox_unchecked.png")
print(f"已勾選參考圖: {checked_ref.size}")
print(f"未勾選參考圖: {unchecked_ref.size}")

# 保存 debug 80x80 供視覺檢查
debug_80.save("test_haystack.png")
checked_ref.save("test_needle_checked.png")
unchecked_ref.save("test_needle_unchecked.png")

print("\n嘗試在 80x80 截圖中匹配參考圖片...")

# 嘗試使用 pyautogui 匹配（模擬實際代碼的行為）
try:
    # 先保存 80x80 截圖為臨時文件
    temp_haystack = "temp_haystack.png"
    debug_80.save(temp_haystack)
    
    # 嘗試匹配已勾選
    try:
        # 注意：pyautogui.locate 需要兩個文件路徑，不能直接用 Image 對象
        # 所以我們需要手動實現匹配邏輯
        from PIL import ImageChops
        
        # 方法 1：完全匹配（需要尺寸和內容完全一致）
        print("\n=== 方法 1：完全像素匹配 ===")
        
        # 檢查尺寸
        if checked_ref.size[0] <= debug_80.size[0] and checked_ref.size[1] <= debug_80.size[1]:
            print(f"尺寸檢查通過：參考圖 {checked_ref.size} <= 截圖 {debug_80.size}")
            
            # 嘗試在不同位置匹配
            best_match_score = float('inf')
            best_position = None
            
            for y in range(debug_80.size[1] - checked_ref.size[1] + 1):
                for x in range(debug_80.size[0] - checked_ref.size[0] + 1):
                    # 裁剪出候選區域
                    candidate = debug_80.crop((x, y, x + checked_ref.size[0], y + checked_ref.size[1]))
                    
                    # 計算差異
                    diff = ImageChops.difference(candidate.convert('RGB'), checked_ref.convert('RGB'))
                    diff_sum = sum(sum(pixel) for pixel in list(diff.getdata()))
                    
                    if diff_sum < best_match_score:
                        best_match_score = diff_sum
                        best_position = (x, y)
                    
                    # 如果差異很小，認為匹配成功
                    if diff_sum < 1000:  # 閾值
                        print(f"找到匹配位置: ({x}, {y}), 差異分數: {diff_sum}")
                        break
                else:
                    continue
                break
            
            print(f"\n最佳匹配位置: {best_position}, 差異分數: {best_match_score}")
            
            if best_match_score < 10000:  # 寬鬆閾值
                print("✅ 可能可以匹配（但實際 pyautogui 可能更嚴格）")
            else:
                print("❌ 差異太大，無法匹配")
        else:
            print(f"❌ 尺寸檢查失敗：參考圖 {checked_ref.size} > 截圖 {debug_80.size}")
    
    except Exception as e:
        print(f"匹配失敗: {e}")
    
finally:
    # 清理臨時文件
    if os.path.exists(temp_haystack):
        os.remove(temp_haystack)

print("\n提示：請查看以下文件進行視覺比較：")
print("  - test_haystack.png (80x80 截圖)")
print("  - test_needle_checked.png (已勾選參考圖)")
print("  - test_needle_unchecked.png (未勾選參考圖)")
