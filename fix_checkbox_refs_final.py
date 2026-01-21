"""
從最新的 debug 截圖重新裁剪參考圖片
確保參考圖片準確反映已勾選/未勾選狀態
"""
from PIL import Image
import numpy as np

# 讀取最新的 debug 截圖 (80x80)
checked_debug = Image.open("debug_checkbox_1768405084.png")  # 已勾選
unchecked_debug = Image.open("debug_checkbox_1768405085.png")  # 未勾選

print("Checked debug size:", checked_debug.size)
print("Unchecked debug size:", unchecked_debug.size)

# 裁剪策略：
# 80x80 截圖中，checkbox 應該在左上角附近
# 我們裁剪左上角 40x40 區域（包含完整的 checkbox）
crop_box = (0, 0, 40, 40)

checked_ref = checked_debug.crop(crop_box)
unchecked_ref = unchecked_debug.crop(crop_box)

print("\nCropped size:", checked_ref.size)

# 儲存
checked_ref.save("res/desktop_settings/checkbox_checked.png")
unchecked_ref.save("res/desktop_settings/checkbox_unchecked.png")

print("\nReference images updated!")
print("  - checkbox_checked.png: 40x40")
print("  - checkbox_unchecked.png: 40x40")

# 像素差異分析
checked_arr = np.array(checked_ref)
unchecked_arr = np.array(unchecked_ref)

diff = np.abs(checked_arr.astype(int) - unchecked_arr.astype(int))
diff_percent = (diff > 10).sum() / diff.size * 100

print(f"\nPixel difference: {diff_percent:.2f}%")
