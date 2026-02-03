# -*- coding: utf-8 -*-
"""
座標驗證功能測試

測試 Area 類型、Toolkit 工具方法和 CoordinateValidator 的功能。
"""

import pytest
from toolkit.types import Area, Toolkit
from toolkit.coordinate_validator import CoordinateValidator


class TestArea:
    """測試 Area 類型"""
    
    def test_area_creation(self):
        """測試 Area 物件創建"""
        area = Area(x1=100, y1=100, x2=200, y2=200)
        assert area.x1 == 100
        assert area.y1 == 100
        assert area.x2 == 200
        assert area.y2 == 200
    
    def test_area_width_height(self):
        """測試 Area 寬高計算"""
        area = Area(x1=100, y1=100, x2=200, y2=150)
        assert area.width == 100
        assert area.height == 50
    
    def test_area_center(self):
        """測試 Area 中心點計算"""
        area = Area(x1=100, y1=100, x2=200, y2=200)
        center = area.center
        assert center == (150, 150)
    
    def test_area_to_tuple(self):
        """測試 Area 轉換為元組"""
        area = Area(x1=100, y1=100, x2=200, y2=200)
        assert area.to_tuple() == (100, 100, 200, 200)


class TestToolkit:
    """測試 Toolkit 工具方法"""
    
    def test_calculate_center(self):
        """測試計算區域中心點"""
        area = Area(x1=100, y1=100, x2=200, y2=200)
        center = Toolkit.calculate_center(area)
        assert center == (150, 150)
    
    def test_calculate_distance(self):
        """測試計算歐幾里得距離"""
        # 3-4-5 直角三角形
        distance = Toolkit.calculate_distance((0, 0), (3, 4))
        assert distance == 5.0
        
        # 相同點距離為 0
        distance = Toolkit.calculate_distance((100, 100), (100, 100))
        assert distance == 0.0
        
        # 水平距離
        distance = Toolkit.calculate_distance((0, 0), (10, 0))
        assert distance == 10.0
        
        # 垂直距離
        distance = Toolkit.calculate_distance((0, 0), (0, 10))
        assert distance == 10.0
    
    def test_calculate_top_left_from_center(self):
        """測試從中心點計算左上角座標"""
        # 100x100 的矩形，中心點在 (150, 150)
        top_left = Toolkit.calculate_top_left_from_center(
            center=(150, 150),
            width=100,
            height=100
        )
        assert top_left == (100, 100)
        
        # 80x60 的矩形，中心點在 (100, 100)
        top_left = Toolkit.calculate_top_left_from_center(
            center=(100, 100),
            width=80,
            height=60
        )
        assert top_left == (60, 70)
    
    def test_create_area_from_center(self):
        """測試從中心點創建 Area"""
        area = Toolkit.create_area_from_center(
            center=(150, 150),
            width=100,
            height=100
        )
        assert area.x1 == 100
        assert area.y1 == 100
        assert area.x2 == 200
        assert area.y2 == 200
        assert area.center == (150, 150)


class TestCoordinateValidator:
    """測試 CoordinateValidator 座標驗證器"""
    
    def test_validator_creation(self):
        """測試驗證器創建"""
        validator = CoordinateValidator(threshold=15.0)
        assert validator.threshold == 15.0
    
    def test_validate_coordinates_pass(self):
        """測試座標驗證通過（距離小於閾值）"""
        validator = CoordinateValidator(threshold=15.0)
        
        comparison = validator.validate_coordinates(
            element_name="測試按鈕",
            cv_coord=(100, 100),
            vlm_coord=(105, 103)
        )
        
        assert comparison.element_name == "測試按鈕"
        assert comparison.cv_coord == (100, 100)
        assert comparison.vlm_coord == (105, 103)
        assert comparison.distance == pytest.approx(5.83, rel=0.01)
        assert comparison.is_discrepancy is False
    
    def test_validate_coordinates_fail(self):
        """測試座標驗證失敗（距離大於閾值）"""
        validator = CoordinateValidator(threshold=15.0)
        
        comparison = validator.validate_coordinates(
            element_name="測試按鈕",
            cv_coord=(100, 100),
            vlm_coord=(120, 115)
        )
        
        assert comparison.element_name == "測試按鈕"
        assert comparison.cv_coord == (100, 100)
        assert comparison.vlm_coord == (120, 115)
        assert comparison.distance == pytest.approx(25.0, rel=0.01)
        assert comparison.is_discrepancy is True
    
    def test_validate_coordinates_edge_case(self):
        """測試座標驗證邊界情況（距離剛好等於閾值）"""
        validator = CoordinateValidator(threshold=15.0)
        
        # 距離剛好等於 15
        comparison = validator.validate_coordinates(
            element_name="測試按鈕",
            cv_coord=(0, 0),
            vlm_coord=(9, 12)  # sqrt(81 + 144) = 15
        )
        
        assert comparison.distance == 15.0
        assert comparison.is_discrepancy is False  # 等於閾值不算差異
    
    def test_comparison_to_dict(self):
        """測試 CoordinateComparison 轉換為字典"""
        validator = CoordinateValidator(threshold=15.0)
        
        comparison = validator.validate_coordinates(
            element_name="測試按鈕",
            cv_coord=(100, 100),
            vlm_coord=(105, 103)
        )
        
        result_dict = comparison.to_dict()
        
        assert result_dict['element_name'] == "測試按鈕"
        assert result_dict['cv_coord'] == [100, 100]
        assert result_dict['vlm_coord'] == [105, 103]
        assert 'distance' in result_dict
        assert 'timestamp' in result_dict
        assert 'threshold' in result_dict
        assert 'is_discrepancy' in result_dict


class TestIntegration:
    """整合測試"""
    
    def test_full_workflow(self):
        """測試完整的座標驗證工作流程"""
        # 1. 圖像辨識得到物件區域
        cv_center = (150, 150)
        cv_width = 100
        cv_height = 80
        
        # 2. 計算左上角座標（用於繪圖）
        top_left = Toolkit.calculate_top_left_from_center(
            center=cv_center,
            width=cv_width,
            height=cv_height
        )
        assert top_left == (100, 110)
        
        # 3. 創建 Area 物件
        area = Toolkit.create_area_from_center(
            center=cv_center,
            width=cv_width,
            height=cv_height
        )
        assert area.center == cv_center
        
        # 4. VLM 識別得到座標
        vlm_center = (155, 148)
        
        # 5. 計算距離
        distance = Toolkit.calculate_distance(cv_center, vlm_center)
        assert distance == pytest.approx(5.39, rel=0.01)
        
        # 6. 驗證座標
        validator = CoordinateValidator(threshold=15.0)
        comparison = validator.validate_coordinates(
            element_name="確認按鈕",
            cv_coord=cv_center,
            vlm_coord=vlm_center
        )
        
        assert comparison.is_discrepancy is False
        assert comparison.distance < 15.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
