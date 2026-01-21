"""
診斷腳本：檢查雙擊 Server 項目的問題
"""
import pygetwindow as gw
import pyautogui
import time
import sys

# 設置輸出編碼
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 60)
print("診斷：雙擊 Server 項目問題")
print("=" * 60)

# 1. 獲取 NX 視窗
wins = [w for w in gw.getWindowsWithTitle("Nx Witness Client") if w.visible and w.width > 1000]
if not wins:
    print("❌ 找不到 NX 視窗")
    exit(1)

win = wins[0]
print(f"\n✅ 找到視窗: {win.title}")
print(f"   尺寸: {win.width} x {win.height}")
print(f"   位置: ({win.left}, {win.top})")

# 2. 計算左側面板 Server 項目的座標
server_x_ratio = 0.10
server_y_ratio = 0.14

server_x = win.left + int(win.width * server_x_ratio)
server_y = win.top + int(win.height * server_y_ratio)

print(f"\n📍 Server 項目保底座標:")
print(f"   比例: ({server_x_ratio}, {server_y_ratio})")
print(f"   絕對座標: ({server_x}, {server_y})")

# 3. 計算右鍵時用的座標（左上角小圖示）
rightclick_x = win.left + int(win.width * 0.08)
rightclick_y = win.top + int(win.height * 0.08)

print(f"\n📍 右鍵點擊座標（左上角小圖示）:")
print(f"   比例: (0.08, 0.08)")
print(f"   絕對座標: ({rightclick_x}, {rightclick_y})")

print(f"\n🔍 兩個座標的距離:")
print(f"   X 軸差距: {abs(server_x - rightclick_x)} 像素")
print(f"   Y 軸差距: {abs(server_y - rightclick_y)} 像素")

# 4. 截取全螢幕
print(f"\n📸 正在截取全螢幕...")
screenshot = pyautogui.screenshot()
screenshot.save("debug_fullscreen.png")
print(f"✅ 已儲存: debug_fullscreen.png")

# 5. 標記兩個位置
from PIL import Image, ImageDraw, ImageFont

img = Image.open("debug_fullscreen.png")
draw = ImageDraw.Draw(img)

# 標記右鍵點擊位置（紅色）
draw.ellipse(
    [rightclick_x - 10, rightclick_y - 10, rightclick_x + 10, rightclick_y + 10],
    outline="red",
    width=3
)
draw.text((rightclick_x + 15, rightclick_y), "右鍵位置", fill="red")

# 標記雙擊位置（藍色）
draw.ellipse(
    [server_x - 10, server_y - 10, server_x + 10, server_y + 10],
    outline="blue",
    width=3
)
draw.text((server_x + 15, server_y), "雙擊位置", fill="blue")

img.save("debug_marked.png")
print(f"✅ 已儲存標記圖片: debug_marked.png")

print(f"\n" + "=" * 60)
print("診斷完成！請檢查:")
print("1. debug_fullscreen.png - 全螢幕截圖")
print("2. debug_marked.png - 標記了兩個點擊位置")
print("=" * 60)

# 6. 等待 3 秒後，實際移動滑鼠到雙擊位置（不點擊）
print(f"\n⏳ 3 秒後將移動滑鼠到雙擊位置（不點擊）...")
time.sleep(3)
pyautogui.moveTo(server_x, server_y)
print(f"✅ 滑鼠已移動到: ({server_x}, {server_y})")
print(f"   請檢查滑鼠是否在正確的 Server 項目上")
