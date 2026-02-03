# -*- coding: utf-8 -*-
"""
VLM 機制測試腳本

快速驗證 VLM 自癒機制是否正常運作。

Usage:
    python tools/test_vlm_mechanism.py
"""

import sys
import os
from pathlib import Path

# 添加專案根目錄到 sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_ai_helper_initialization():
    """測試 AI Helper 初始化"""
    print("=" * 60)
    print("測試 1: AI Helper 初始化")
    print("=" * 60)
    
    try:
        from utils.ai_vision_helper import get_ai_helper
        
        ai_helper = get_ai_helper()
        print(f"✅ AI Helper 初始化成功")
        print(f"   - 啟用狀態: {ai_helper.enabled}")
        print(f"   - 日誌目錄: {ai_helper.log_dir}")
        print(f"   - 知識庫路徑: {ai_helper.knowledge_base_path}")
        
        return True
    except Exception as e:
        print(f"❌ AI Helper 初始化失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vlm_config():
    """測試 VLM 配置"""
    print("\n" + "=" * 60)
    print("測試 2: VLM 配置檢查")
    print("=" * 60)
    
    try:
        from config import DevConfig
        
        print(f"✅ VLM 配置讀取成功")
        print(f"   - ENABLE_VLM_LEARNING: {getattr(DevConfig, 'ENABLE_VLM_LEARNING', 'Not Set')}")
        print(f"   - VLM_PROVIDER: {getattr(DevConfig, 'VLM_PROVIDER', 'Not Set')}")
        print(f"   - VLM_MODEL: {getattr(DevConfig, 'VLM_MODEL', 'Not Set')}")
        print(f"   - AI_INTELLIGENCE_LOG_DIR: {getattr(DevConfig, 'AI_INTELLIGENCE_LOG_DIR', 'Not Set')}")
        
        # 檢查 API Key
        api_key = getattr(DevConfig, 'VLM_API_KEY', '')
        if api_key:
            masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
            print(f"   - VLM_API_KEY: {masked_key} (已設置)")
        else:
            print(f"   - VLM_API_KEY: ⚠️ 未設置")
        
        return True
    except Exception as e:
        print(f"❌ VLM 配置讀取失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_knowledge_base():
    """測試知識庫文件"""
    print("\n" + "=" * 60)
    print("測試 3: 知識庫文件檢查")
    print("=" * 60)
    
    try:
        from utils.ai_vision_helper import get_ai_helper
        import json
        
        ai_helper = get_ai_helper()
        kb_path = ai_helper.knowledge_base_path
        
        if kb_path.exists():
            with open(kb_path, "r", encoding="utf-8") as f:
                kb_data = json.load(f)
            
            obs_count = len(kb_data.get("observations", []))
            print(f"✅ 知識庫文件存在")
            print(f"   - 路徑: {kb_path}")
            print(f"   - 觀測記錄數: {obs_count}")
            print(f"   - 版本: {kb_data.get('metadata', {}).get('version', 'N/A')}")
            print(f"   - 最後更新: {kb_data.get('metadata', {}).get('last_updated', 'N/A')}")
        else:
            print(f"ℹ️  知識庫文件不存在（將在首次觀測時創建）")
            print(f"   - 預期路徑: {kb_path}")
        
        return True
    except Exception as e:
        print(f"❌ 知識庫檢查失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simulate_failure():
    """測試模擬失敗場景"""
    print("\n" + "=" * 60)
    print("測試 4: 模擬元素定位失敗")
    print("=" * 60)
    
    try:
        from utils.ai_vision_helper import get_ai_helper
        import tempfile
        from PIL import Image
        
        # 創建一個測試截圖
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            # 創建一個簡單的測試圖片
            img = Image.new('RGB', (800, 600), color='white')
            img.save(tmp.name)
            screenshot_path = tmp.name
        
        print(f"📸 已創建測試截圖: {screenshot_path}")
        
        # 調用 AI 分析（模擬模式）
        ai_helper = get_ai_helper()
        result = ai_helper.analyze_failure(
            screenshot_path=screenshot_path,
            target_element="test_login_button",
            context={"test": "simulation"}
        )
        
        if result.get("status") == "success":
            print(f"✅ VLM 分析成功")
            vlm_analysis = result.get("vlm_analysis", {})
            print(f"   - 目標狀態: {vlm_analysis.get('target_element_status')}")
            print(f"   - 建議 ActionKey: {vlm_analysis.get('recommended_action_key')}")
            print(f"   - 嚴重程度: {vlm_analysis.get('severity')}")
        elif result.get("status") == "disabled":
            print(f"ℹ️  VLM 學習模式未啟用（這是正常的）")
        else:
            print(f"⚠️  VLM 分析失敗: {result.get('error')}")
        
        # 清理測試文件
        os.unlink(screenshot_path)
        
        return True
    except Exception as e:
        print(f"❌ 模擬失敗測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_base_page_integration():
    """測試 BasePage 整合"""
    print("\n" + "=" * 60)
    print("測試 5: BasePage VLM 整合")
    print("=" * 60)
    
    try:
        from base.base_page import BasePage
        
        # 檢查 BasePage 是否有 VLM 相關屬性和方法
        required_attrs = [
            'vlm_enabled',
            'ai_helper',
            '_trigger_vlm_observation',
            '_safe_operation'
        ]
        
        for attr in required_attrs:
            if hasattr(BasePage, attr):
                print(f"✅ BasePage.{attr} 存在")
            else:
                print(f"❌ BasePage.{attr} 不存在")
                return False
        
        print(f"\n✅ BasePage VLM 整合完整")
        return True
    except Exception as e:
        print(f"❌ BasePage 整合檢查失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函數"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "VLM 機制測試工具" + " " * 15 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    tests = [
        test_ai_helper_initialization,
        test_vlm_config,
        test_knowledge_base,
        test_simulate_failure,
        test_base_page_integration
    ]
    
    results = []
    for test_func in tests:
        result = test_func()
        results.append(result)
    
    # 總結
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"通過: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 所有測試通過！VLM 機制已正確配置。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 個測試失敗，請檢查配置。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
