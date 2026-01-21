"""
從當前測試的 debug 截圖更新參考圖片
"""
from PIL import Image
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

# 使用當前測試生成的最新截圖
# debug_checkbox_large_1768405084.png - 點擊前（已勾選狀態）
# debug_checkbox_large_1768405085.png - 點擊後（應該是未勾選）

large_before = Image.open("debug_checkbox_large_1768405084.png")
large_after = Image.open("debug_checkbox_large_1768405085.png")

print(f"點擊前大圖: {large_before.size}")
print(f"點擊後大圖: {large_after.size}")

# 這兩張都是 200x60，第一個 checkbox 在左側
# 裁剪位置：從 checkbox 開始，包含部分文字
left = 95
top = 15
width = 70
height = 30

# 點擊前（已勾選）
checked_crop = large_before.crop((left, top, left + width, top + height))
checked_path = os.path.join("res", "desktop_settings", "checkbox_checked.png")
checked_crop.save(checked_path)
print(f"\n已更新已勾選: {checked_path}, 尺寸: {checked_crop.size}")

# 點擊後（未勾選）
unchecked_crop = large_after.crop((left, top, left + width, top + height))
unchecked_path = os.path.join("res", "desktop_settings", "checkbox_unchecked.png")
unchecked_crop.save(unchecked_path)
print(f"已更新未勾選: {unchecked_path}, 尺寸: {unchecked_crop.size}")

# 驗證差異
checked_pixels = list(checked_crop.convert('RGB').getdata())
unchecked_pixels = list(unchecked_crop.convert('RGB').getdata())
diff_count = sum(1 for c, u in zip(checked_pixels, unchecked_pixels) if c != u)
print(f"\n差異像素數: {diff_count}/{len(checked_pixels)}")
print(f"差異百分比: {diff_count / len(checked_pixels) * 100:.2f}%")

print("\n✅ 參考圖片已從當前測試的截圖更新")
