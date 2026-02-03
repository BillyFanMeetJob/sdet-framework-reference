# -*- coding: utf-8 -*-
"""
UnifiedVLM 單元測試

測試 VLM 引擎的核心功能，包括座標縮放、驗證機制等。

Author: SDET Team
Date: 2026-01-27
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from toolkit.vlm_engine import UnifiedVLM
from toolkit.types import Area, Toolkit


class TestUnifiedVLM:
    """UnifiedVLM 測試類"""
    
    @pytest.fixture
    def vlm_engine(self):
        """創建測試用 VLM 引擎"""
        return UnifiedVLM(threshold=15.0)
    
    @pytest.fixture
    def mock_logger(self):
        """創建 Mock Logger"""
        return Mock()
    
    def test_initialization(self, vlm_engine):
        """測試初始化"""
        assert vlm_engine.threshold == 15.0
        assert vlm_engine.ollama_model == "llama3.2-vision"
        assert vlm_engine.logger is not None
    
    def test_normalize_coords_same_resolution(self, vlm_engine):
        """測試座標縮放 - 相同解析度"""
        historical_data = {
            "avg_coord": [960, 540],
            "resolution": [1920, 1080]
        }
        current_resolution = (1920, 1080)
        
        result = vlm_engine._normalize_coords(historical_data, current_resolution)
        
        assert result == (960, 540)
    
    def test_normalize_coords_different_resolution(self, vlm_engine):
        """測試座標縮放 - 不同解析度"""
        historical_data = {
            "avg_coord": [960, 540],
            "resolution": [1920, 1080]
        }
        current_resolution = (2560, 1440)
        
        result = vlm_engine._normalize_coords(historical_data, current_resolution)
        
        # 預期結果: (960 * 2560/1920, 540 * 1440/1080) = (1280, 720)
        assert result == (1280, 720)
    
    def test_normalize_coords_half_resolution(self, vlm_engine):
        """測試座標縮放 - 一半解析度"""
        historical_data = {
            "avg_coord": [1920, 1080],
            "resolution": [3840, 2160]
        }
        current_resolution = (1920, 1080)
        
        result = vlm_engine._normalize_coords(historical_data, current_resolution)
        
        # 預期結果: (1920 * 0.5, 1080 * 0.5) = (960, 540)
        assert result == (960, 540)
    
    def test_normalize_coords_missing_data(self, vlm_engine):
        """測試座標縮放 - 數據缺失"""
        historical_data = {
            "avg_coord": [960, 540]
            # 缺少 resolution
        }
        current_resolution = (1920, 1080)
        
        result = vlm_engine._normalize_coords(historical_data, current_resolution)
        
        assert result is None
    
    def test_parse_coordinate_response_pure_json(self, vlm_engine):
        """測試解析座標 - 純 JSON 格式"""
        response = '{"x": 100, "y": 200}'
        
        result = vlm_engine._parse_coordinate_response(response)
        
        assert result == (100, 200)
    
    def test_parse_coordinate_response_with_markdown(self, vlm_engine):
        """測試解析座標 - Markdown 包裹"""
        response = '```json\n{"x": 150, "y": 250}\n```'
        
        result = vlm_engine._parse_coordinate_response(response)
        
        assert result == (150, 250)
    
    def test_parse_coordinate_response_with_text(self, vlm_engine):
        """測試解析座標 - 文字混合"""
        response = '座標是 {"x": 200, "y": 300} 這裡'
        
        result = vlm_engine._parse_coordinate_response(response)
        
        assert result == (200, 300)
    
    def test_parse_coordinate_response_invalid(self, vlm_engine):
        """測試解析座標 - 無效格式"""
        response = '這是無效的響應'
        
        result = vlm_engine._parse_coordinate_response(response)
        
        assert result is None
    
    def test_generate_prompt_without_history(self, vlm_engine):
        """測試 Prompt 生成 - 無歷史數據"""
        prompt = vlm_engine._generate_prompt(
            element_name="確認按鈕",
            normalized_coord=None,
            historical_data=None
        )
        
        assert "確認按鈕" in prompt
        assert "JSON" in prompt
        assert "參考資訊" not in prompt
    
    def test_generate_prompt_with_history(self, vlm_engine):
        """測試 Prompt 生成 - 有歷史數據"""
        prompt = vlm_engine._generate_prompt(
            element_name="確認按鈕",
            normalized_coord=(960, 540),
            historical_data={
                "neighbors": ["取消按鈕在右側 50px"]
            }
        )
        
        assert "確認按鈕" in prompt
        assert "(960, 540)" in prompt
        assert "取消按鈕在右側 50px" in prompt
    
    def test_confidence_check_pass(self, vlm_engine):
        """測試信心校驗 - 通過"""
        result = vlm_engine._confidence_check(
            element_name="按鈕",
            vlm_coord=(100, 100),
            expected_coord=(110, 110)
        )
        
        # 距離 14.14px < 50px，應該通過
        assert result is True
    
    def test_confidence_check_fail(self, vlm_engine):
        """測試信心校驗 - 失敗"""
        result = vlm_engine._confidence_check(
            element_name="按鈕",
            vlm_coord=(100, 100),
            expected_coord=(200, 200)
        )
        
        # 距離 141.42px > 50px，應該失敗
        assert result is False
    
    def test_coordinate_library_creation(self, vlm_engine, tmp_path):
        """測試座標庫創建"""
        # 使用臨時路徑
        temp_library = tmp_path / "test_library.json"
        vlm_engine.COORDINATE_LIBRARY_PATH = str(temp_library)
        
        vlm_engine._ensure_coordinate_library()
        
        assert temp_library.exists()
        
        # 驗證內容
        with open(temp_library, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "elements" in data
    
    def test_update_coordinate_library_new_element(self, vlm_engine, tmp_path):
        """測試更新座標庫 - 新元素"""
        temp_library = tmp_path / "test_library.json"
        vlm_engine.COORDINATE_LIBRARY_PATH = str(temp_library)
        
        # 創建空座標庫
        with open(temp_library, 'w', encoding='utf-8') as f:
            json.dump({"metadata": {}, "elements": {}}, f)
        
        # 更新座標庫
        vlm_engine._update_coordinate_library(
            element_name="測試按鈕",
            coord=(100, 200),
            resolution=(1920, 1080)
        )
        
        # 驗證
        with open(temp_library, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "測試按鈕" in data["elements"]
        assert data["elements"]["測試按鈕"]["avg_coord"] == [100, 200]
        assert data["elements"]["測試按鈕"]["count"] == 1
    
    def test_update_coordinate_library_existing_element(self, vlm_engine, tmp_path):
        """測試更新座標庫 - 已存在元素（加權平均）"""
        temp_library = tmp_path / "test_library.json"
        vlm_engine.COORDINATE_LIBRARY_PATH = str(temp_library)
        
        # 創建含有歷史數據的座標庫
        with open(temp_library, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {},
                "elements": {
                    "測試按鈕": {
                        "avg_coord": [100, 200],
                        "resolution": [1920, 1080],
                        "count": 1,
                        "neighbors": []
                    }
                }
            }, f)
        
        # 更新座標庫（新座標 120, 220）
        vlm_engine._update_coordinate_library(
            element_name="測試按鈕",
            coord=(120, 220),
            resolution=(1920, 1080)
        )
        
        # 驗證加權平均
        with open(temp_library, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 預期: ((100*1 + 120) / 2, (200*1 + 220) / 2) = (110, 210)
        assert data["elements"]["測試按鈕"]["avg_coord"] == [110, 210]
        assert data["elements"]["測試按鈕"]["count"] == 2
    
    def test_get_statistics_empty(self, vlm_engine, tmp_path):
        """測試統計信息 - 空座標庫"""
        temp_library = tmp_path / "test_library.json"
        vlm_engine.COORDINATE_LIBRARY_PATH = str(temp_library)
        
        with open(temp_library, 'w', encoding='utf-8') as f:
            json.dump({"metadata": {}, "elements": {}}, f)
        
        stats = vlm_engine.get_statistics()
        
        assert stats["total_elements"] == 0
        assert stats["total_records"] == 0
    
    def test_get_statistics_with_data(self, vlm_engine, tmp_path):
        """測試統計信息 - 有數據"""
        temp_library = tmp_path / "test_library.json"
        vlm_engine.COORDINATE_LIBRARY_PATH = str(temp_library)
        
        with open(temp_library, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {},
                "elements": {
                    "按鈕1": {"count": 5},
                    "按鈕2": {"count": 10}
                }
            }, f)
        
        stats = vlm_engine.get_statistics()
        
        assert stats["total_elements"] == 2
        assert stats["total_records"] == 15
        assert "按鈕1" in stats["elements"]
        assert "按鈕2" in stats["elements"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
