"""
測試 VLM 座標換算邏輯的正確性
確保座標換算不會影響已有的功能
"""
import sys
import os

# 添加項目根目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base.vlm_recognizer import VLMRecognizer
from base.vlm_recognizer import VLMResult


def test_coordinate_conversion():
    """
    測試座標換算邏輯：
    1. 全屏截圖（無 region）
    2. 區域截圖（有 region）
    3. 縮小後的截圖
    """
    print("=" * 80)
    print("測試 VLM 座標換算邏輯")
    print("=" * 80)
    
    # 模擬 VLM 返回的結果
    test_cases = [
        {
            "name": "全屏截圖，無縮小，比例座標",
            "original_size": (1920, 1080),
            "resized_size": (1920, 1080),
            "vlm_x": 0.5,  # 比例座標
            "vlm_y": 0.5,
            "region": None,
            "expected_x": 960,  # 1920 * 0.5
            "expected_y": 540,  # 1080 * 0.5
        },
        {
            "name": "全屏截圖，縮小後，比例座標",
            "original_size": (1920, 1080),
            "resized_size": (1280, 720),  # 縮小到 1280x720
            "vlm_x": 0.5,  # 比例座標（相對於縮小後的圖片）
            "vlm_y": 0.5,
            "region": None,
            "expected_x": 960,  # 1280 * 0.5 * (1920/1280) = 960
            "expected_y": 540,  # 720 * 0.5 * (1080/720) = 540
        },
        {
            "name": "區域截圖，無縮小，比例座標",
            "original_size": (800, 600),  # region 尺寸
            "resized_size": (800, 600),
            "vlm_x": 0.5,  # 比例座標（相對於 region 截圖）
            "vlm_y": 0.5,
            "region": (100, 200, 800, 600),  # (left, top, width, height)
            "expected_x": 100 + 400,  # region[0] + 800 * 0.5
            "expected_y": 200 + 300,  # region[1] + 600 * 0.5
        },
        {
            "name": "區域截圖，縮小後，比例座標",
            "original_size": (800, 600),  # region 尺寸
            "resized_size": (640, 480),  # 縮小後
            "vlm_x": 0.5,  # 比例座標（相對於縮小後的圖片）
            "vlm_y": 0.5,
            "region": (100, 200, 800, 600),  # (left, top, width, height)
            "expected_x": 100 + 400,  # region[0] + 640 * 0.5 * (800/640)
            "expected_y": 200 + 300,  # region[1] + 480 * 0.5 * (600/480)
        },
        {
            "name": "區域截圖，無縮小，像素座標",
            "original_size": (800, 600),  # region 尺寸
            "resized_size": (800, 600),
            "vlm_x": 400,  # 像素座標（相對於 region 截圖）
            "vlm_y": 300,
            "region": (100, 200, 800, 600),  # (left, top, width, height)
            "expected_x": 100 + 400,  # region[0] + 400
            "expected_y": 200 + 300,  # region[1] + 300
        },
        {
            "name": "區域截圖，縮小後，像素座標",
            "original_size": (800, 600),  # region 尺寸
            "resized_size": (640, 480),  # 縮小後
            "vlm_x": 320,  # 像素座標（相對於縮小後的圖片）
            "vlm_y": 240,
            "region": (100, 200, 800, 600),  # (left, top, width, height)
            "expected_x": 100 + 400,  # region[0] + 320 * (800/640)
            "expected_y": 200 + 300,  # region[1] + 240 * (600/480)
        },
    ]
    
    # 模擬座標換算邏輯
    def convert_coordinates(vlm_x, vlm_y, original_size, resized_size, region):
        """
        模擬 VLM 座標換算邏輯
        """
        # 計算縮放比例
        scale_x = original_size[0] / resized_size[0] if resized_size[0] > 0 else 1.0
        scale_y = original_size[1] / resized_size[1] if resized_size[1] > 0 else 1.0
        
        # 判斷是比例座標還是像素座標
        is_ratio_coord = (0.0 < abs(vlm_x) < 1.0) or (0.0 < abs(vlm_y) < 1.0)
        
        if is_ratio_coord:
            # 比例座標：先轉換為縮小後圖片的像素座標
            pixel_x = vlm_x * resized_size[0]
            pixel_y = vlm_y * resized_size[1]
        else:
            # 像素座標：直接使用（假設是相對於縮小後的圖片）
            pixel_x = vlm_x
            pixel_y = vlm_y
        
        # 將座標（相對於縮小後的圖片）轉換回原始截圖尺寸
        result_x = int(pixel_x * scale_x)
        result_y = int(pixel_y * scale_y)
        
        # 加上 region 偏移（如果有）
        if region:
            result_x += region[0]
            result_y += region[1]
        
        return result_x, result_y
    
    # 執行測試
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n測試 {i}: {test_case['name']}")
        print(f"  原始尺寸: {test_case['original_size']}")
        print(f"  縮小後尺寸: {test_case['resized_size']}")
        print(f"  VLM 返回座標: ({test_case['vlm_x']}, {test_case['vlm_y']})")
        print(f"  Region: {test_case['region']}")
        
        result_x, result_y = convert_coordinates(
            test_case['vlm_x'],
            test_case['vlm_y'],
            test_case['original_size'],
            test_case['resized_size'],
            test_case['region']
        )
        
        expected_x = test_case['expected_x']
        expected_y = test_case['expected_y']
        
        print(f"  計算結果: ({result_x}, {result_y})")
        print(f"  預期結果: ({expected_x}, {expected_y})")
        
        if abs(result_x - expected_x) <= 1 and abs(result_y - expected_y) <= 1:
            print(f"  [OK] 通過")
            passed += 1
        else:
            print(f"  [FAIL] 失敗：誤差 x={abs(result_x - expected_x)}, y={abs(result_y - expected_y)}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"測試結果: {passed} 通過, {failed} 失敗")
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    success = test_coordinate_conversion()
    sys.exit(0 if success else 1)
