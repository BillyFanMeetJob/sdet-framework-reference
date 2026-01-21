"""
直接使用 80x80 debug 截圖作為參考圖片
"""
from PIL import Image
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

# 直接使用 80x80 截圖
debug_80_before = Image.open("debug_checkbox_1768405084.png")  # 點擊前
debug_80_after = Image.open("debug_checkbox_1768405085.png")   # 點擊後

print(f"點擊前 80x80: {debug_80_before.size}")
print(f"點擊後 80x80: {debug_80_after.size}")

# 這些 80x80 截圖已經是以點擊座標為中心的
# 我們需要裁剪出左上角的 checkbox 部分（第一個 checkbox）

# 從 80x80 截圖中裁剪左上角 50x40 區域（包含第一個 checkbox）
width = 50
height = 40

checked_crop = debug_80_before.crop((0, 0, width, height))
unchecked_crop = debug_80_after.crop((0, 0, width, height))

checked_path = os.path.join("res", "desktop_settings", "checkbox_checked.png")
unchecked_path = os.path.join("res", "desktop_settings", "checkbox_unchecked.png")

checked_crop.save(checked_path)
unchecked_crop.save(unchecked_path)

print(f"\n已更新已勾選: {checked_path}, 尺寸: {checked_crop.size}")
print(f"已更新未勾選: {unchecked_path}, 尺寸: {unchecked_crop.size}")

# 驗證差異
checked_pixels = list(checked_crop.convert('RGB').getdata())
unchecked_pixels = list(unchecked_crop.convert('RGB').getdata())
diff_count = sum(1 for c, u in zip(checked_pixels, unchecked_pixels) if c != u)
print(f"\n差異像素數: {diff_count}/{len(checked_pixels)}")
print(f"差異百分比: {diff_count / len(checked_pixels) * 100:.2f}%")

print("\n✅ 參考圖片已從 80x80 debug 截圖更新（50x40）")
