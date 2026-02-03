# -*- coding: utf-8 -*-
"""
特徵自進化功能單元測試

測試特徵進化、樣式變化檢測、全局掃描等功能。

Author: SDET Team
Date: 2026-01-27
"""

import pytest
import json
import os
from unittest.mock import Mock, patch
from pathlib import Path

from toolkit.vlm_engine import UnifiedVLM, VLMResult
from toolkit.types import Area


class TestFeatureEvolution:
    """特徵進化測試類"""
    
    @pytest.fixture
    def vlm_engine(self):
        """創建測試用 VLM 引擎（啟用特徵進化）"""
        return UnifiedVLM(threshold=15.0, enable_feature_evolution=True)
    
    def test_vlm_result_dataclass(self):
        """測試 VLMResult 數據類"""
        result = VLMResult(
            coordinate=(100, 200),
            description="綠色按鈕",
            provider="ollama",
            style_change=True,
            extracted_features=["綠色", "按鈕"]
        )
        
        assert result.coordinate == (100, 200)
        assert result.description == "綠色按鈕"
        assert result.style_change is True
        assert result.extracted_features == ["綠色", "按鈕"]
    
    def test_extract_features_list(self, vlm_engine):
        """測試特徵列表提取"""
        description = "這是一個綠色的圓形按鈕，中間有白色的「確認」文字"
        
        features = vlm_engine._extract_features_list(description)
        
        # 特徵提取會匹配單字（如 "綠" 而非 "綠色"）
        assert "綠" in features or "green" in features
        assert "圓" in features or "circle" in features or "round" in features
        assert "按鈕" in features or "button" in features
        assert len(features) > 0  # 確保有提取到特徵
    
    def test_extract_key_features(self, vlm_engine):
        """測試關鍵特徵提取"""
        features = ["綠色", "圓形", "按鈕", "確認", "白色文字"]
        
        key_features = vlm_engine._extract_key_features(features)
        
        # 關鍵特徵應包含形狀和功能，不包含顏色
        assert "圓形" in key_features or "按鈕" in key_features or "確認" in key_features
    
    def test_extract_secondary_features(self, vlm_engine):
        """測試次要特徵提取"""
        features = ["綠色", "圓形", "按鈕", "確認", "白色文字"]
        
        secondary_features = vlm_engine._extract_secondary_features(features)
        
        # 次要特徵應包含顏色
        assert "綠色" in secondary_features or len(secondary_features) > 0
    
    def test_style_change_detection(self, vlm_engine):
        """測試樣式變化檢測"""
        # 模擬 VLM 響應（包含 [STYLE_CHANGE] 標記）
        response = '''
        {
            "description": "[STYLE_CHANGE] 這是一個藍色的圓形按鈕",
            "coordinate": {"x": 100, "y": 200},
            "features": ["藍色", "圓形", "按鈕"]
        }
        '''
        
        result = vlm_engine._parse_vlm_response(response, "ollama")
        
        assert result is not None
        assert result.style_change is True
        assert result.coordinate == (100, 200)
    
    def test_parse_vlm_response_with_features(self, vlm_engine):
        """測試解析 VLM 響應（包含特徵列表）"""
        response = '''
        {
            "description": "綠色按鈕",
            "coordinate": {"x": 100, "y": 200},
            "features": ["綠色", "圓形", "按鈕"]
        }
        '''
        
        result = vlm_engine._parse_vlm_response(response, "ollama")
        
        assert result is not None
        assert result.coordinate == (100, 200)
        assert result.extracted_features == ["綠色", "圓形", "按鈕"]
    
    def test_update_coordinate_library_with_features(self, vlm_engine, tmp_path):
        """測試更新座標庫（包含特徵）"""
        temp_library = tmp_path / "test_library.json"
        vlm_engine.COORDINATE_LIBRARY_PATH = str(temp_library)
        
        # 創建空座標庫
        with open(temp_library, 'w', encoding='utf-8') as f:
            json.dump({"metadata": {}, "elements": {}}, f)
        
        # 創建 VLMResult
        vlm_result = VLMResult(
            coordinate=(100, 200),
            description="綠色圓形按鈕",
            extracted_features=["綠色", "圓形", "按鈕"]
        )
        
        # 更新座標庫
        vlm_engine._update_coordinate_library(
            element_name="測試按鈕",
            coord=(100, 200),
            resolution=(1920, 1080),
            description="綠色圓形按鈕",
            vlm_result=vlm_result
        )
        
        # 驗證
        with open(temp_library, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "測試按鈕" in data["elements"]
        element = data["elements"]["測試按鈕"]
        assert "observed_features" in element
        assert "綠色" in element["observed_features"]
        assert "圓形" in element["observed_features"]
    
    def test_feature_deduplication(self, vlm_engine, tmp_path):
        """測試特徵去重"""
        temp_library = tmp_path / "test_library.json"
        vlm_engine.COORDINATE_LIBRARY_PATH = str(temp_library)
        
        # 創建含有歷史特徵的座標庫
        with open(temp_library, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {},
                "elements": {
                    "測試按鈕": {
                        "avg_coord": [100, 200],
                        "resolution": [1920, 1080],
                        "count": 1,
                        "observed_features": ["綠色", "圓形", "按鈕"]
                    }
                }
            }, f)
        
        # 添加重複特徵
        vlm_result = VLMResult(
            coordinate=(100, 200),
            description="綠色圓形按鈕",
            extracted_features=["綠色", "圓形", "按鈕", "確認"]  # "綠色"、"圓形"、"按鈕" 重複
        )
        
        vlm_engine._update_coordinate_library(
            element_name="測試按鈕",
            coord=(100, 200),
            resolution=(1920, 1080),
            description="綠色圓形按鈕",
            vlm_result=vlm_result
        )
        
        # 驗證去重
        with open(temp_library, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        observed = data["elements"]["測試按鈕"]["observed_features"]
        # 應該只有 4 個特徵（去重後）
        assert len(observed) == 4
        assert "確認" in observed
    
    def test_feature_evolution_disabled(self):
        """測試禁用特徵進化"""
        vlm = UnifiedVLM(enable_feature_evolution=False)
        
        assert vlm.enable_feature_evolution is False
    
    def test_style_change_threshold(self, vlm_engine):
        """測試樣式變化閾值"""
        assert vlm_engine.STYLE_CHANGE_THRESHOLD == 5.0
        assert vlm_engine.MAJOR_CHANGE_THRESHOLD == 50.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
