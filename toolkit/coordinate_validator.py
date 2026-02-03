# toolkit/coordinate_validator.py

"""座標驗證與數據持久化模組。

此模組提供 VLM 與圖像辨識座標的比對驗證功能，並將結果持久化至 JSON 文件。
"""

import json
import os
from datetime import datetime
from typing import Tuple, Dict, Any, Optional
from dataclasses import dataclass, asdict

from toolkit.types import Toolkit


@dataclass
class CoordinateComparison:
    """座標比對結果。
    
    Attributes:
        element_name: 元素名稱
        cv_coord: 圖像辨識座標 (x, y)
        vlm_coord: VLM 識別座標 (x, y)
        distance: 兩座標間的歐幾里得距離
        timestamp: 記錄時間戳
        threshold: 使用的距離閾值
        is_discrepancy: 是否超過閾值（標記為差異）
    """
    element_name: str
    cv_coord: Tuple[int, int]
    vlm_coord: Tuple[int, int]
    distance: float
    timestamp: str
    threshold: float
    is_discrepancy: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式以便 JSON 序列化。
        
        Returns:
            包含所有欄位的字典
        """
        return {
            'element_name': self.element_name,
            'cv_coord': list(self.cv_coord),
            'vlm_coord': list(self.vlm_coord),
            'distance': round(self.distance, 2),
            'timestamp': self.timestamp,
            'threshold': self.threshold,
            'is_discrepancy': self.is_discrepancy
        }


class CoordinateValidator:
    """座標驗證器，用於比對圖像辨識與 VLM 的識別結果。"""
    
    # 預設距離閾值（像素）
    DEFAULT_THRESHOLD = 15.0
    
    # 座標庫文件路徑
    COORDINATE_LIBRARY_PATH = "coordinate_library.json"
    
    def __init__(self, threshold: float = DEFAULT_THRESHOLD, logger=None):
        """初始化座標驗證器。
        
        Args:
            threshold: 距離閾值（像素），超過此距離將標記為差異
            logger: 日誌記錄器（可選）
        """
        self.threshold = threshold
        self.logger = logger
        self._ensure_library_exists()
    
    def _ensure_library_exists(self) -> None:
        """確保座標庫文件存在，若不存在則創建。"""
        if not os.path.exists(self.COORDINATE_LIBRARY_PATH):
            with open(self.COORDINATE_LIBRARY_PATH, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
    
    def _log(self, level: str, message: str) -> None:
        """記錄日誌。
        
        Args:
            level: 日誌級別 ('info', 'warning', 'error', 'debug')
            message: 日誌訊息
        """
        if self.logger:
            getattr(self.logger, level)(message)
        else:
            print(f"[{level.upper()}] {message}")
    
    def validate_coordinates(
        self,
        element_name: str,
        cv_coord: Tuple[int, int],
        vlm_coord: Tuple[int, int]
    ) -> CoordinateComparison:
        """驗證圖像辨識與 VLM 的座標差異。
        
        使用歐幾里得距離計算兩座標間的距離，並與閾值比較。
        若距離超過閾值，將在日誌中標註 VLM_DISCREPANCY_WARNING。
        
        Args:
            element_name: 元素名稱（用於識別）
            cv_coord: 圖像辨識得到的座標 (x, y)
            vlm_coord: VLM 識別得到的座標 (x, y)
            
        Returns:
            CoordinateComparison 物件，包含比對結果
            
        Example:
            >>> validator = CoordinateValidator(threshold=15.0)
            >>> result = validator.validate_coordinates(
            ...     "確認按鈕",
            ...     (100, 100),
            ...     (105, 103)
            ... )
            >>> result.distance
            5.83
            >>> result.is_discrepancy
            False
        """
        # 計算歐幾里得距離
        distance = Toolkit.calculate_distance(cv_coord, vlm_coord)
        
        # 判斷是否超過閾值
        is_discrepancy = distance > self.threshold
        
        # 創建比對結果
        comparison = CoordinateComparison(
            element_name=element_name,
            cv_coord=cv_coord,
            vlm_coord=vlm_coord,
            distance=distance,
            timestamp=datetime.now().isoformat(),
            threshold=self.threshold,
            is_discrepancy=is_discrepancy
        )
        
        # 記錄日誌
        if is_discrepancy:
            self._log(
                'warning',
                f"[VLM_DISCREPANCY_WARNING] 元素 '{element_name}' 座標差異過大: "
                f"CV={cv_coord}, VLM={vlm_coord}, 距離={distance:.2f}px (閾值={self.threshold}px)"
            )
        else:
            self._log(
                'info',
                f"[VLM_VALIDATION_OK] 元素 '{element_name}' 座標驗證通過: "
                f"CV={cv_coord}, VLM={vlm_coord}, 距離={distance:.2f}px"
            )
        
        return comparison
    
    def save_to_library(self, comparison: CoordinateComparison) -> None:
        """將座標比對結果保存至座標庫。
        
        座標庫以 JSON 格式存儲，用於未來優化 VLM 識別精準度。
        
        Args:
            comparison: 座標比對結果
        """
        try:
            # 讀取現有數據
            with open(self.COORDINATE_LIBRARY_PATH, 'r', encoding='utf-8') as f:
                library = json.load(f)
            
            # 添加新記錄
            library.append(comparison.to_dict())
            
            # 寫回文件
            with open(self.COORDINATE_LIBRARY_PATH, 'w', encoding='utf-8') as f:
                json.dump(library, f, ensure_ascii=False, indent=2)
            
            self._log('debug', f"座標比對結果已保存至 {self.COORDINATE_LIBRARY_PATH}")
            
        except Exception as e:
            self._log('error', f"保存座標比對結果失敗: {e}")
    
    def validate_and_save(
        self,
        element_name: str,
        cv_coord: Tuple[int, int],
        vlm_coord: Tuple[int, int]
    ) -> CoordinateComparison:
        """驗證座標並保存至座標庫（便捷方法）。
        
        此方法結合了 validate_coordinates 和 save_to_library，
        適合在圖像辨識流程中一次性完成驗證與保存。
        
        Args:
            element_name: 元素名稱
            cv_coord: 圖像辨識座標
            vlm_coord: VLM 識別座標
            
        Returns:
            CoordinateComparison 物件
        """
        comparison = self.validate_coordinates(element_name, cv_coord, vlm_coord)
        self.save_to_library(comparison)
        return comparison
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取座標庫的統計信息。
        
        Returns:
            包含統計信息的字典，包括：
            - total_records: 總記錄數
            - discrepancy_count: 差異記錄數
            - discrepancy_rate: 差異比例
            - avg_distance: 平均距離
            - max_distance: 最大距離
        """
        try:
            with open(self.COORDINATE_LIBRARY_PATH, 'r', encoding='utf-8') as f:
                library = json.load(f)
            
            if not library:
                return {
                    'total_records': 0,
                    'discrepancy_count': 0,
                    'discrepancy_rate': 0.0,
                    'avg_distance': 0.0,
                    'max_distance': 0.0
                }
            
            total = len(library)
            discrepancies = sum(1 for record in library if record.get('is_discrepancy', False))
            distances = [record.get('distance', 0) for record in library]
            
            return {
                'total_records': total,
                'discrepancy_count': discrepancies,
                'discrepancy_rate': round(discrepancies / total * 100, 2) if total > 0 else 0.0,
                'avg_distance': round(sum(distances) / len(distances), 2) if distances else 0.0,
                'max_distance': round(max(distances), 2) if distances else 0.0
            }
            
        except Exception as e:
            self._log('error', f"獲取統計信息失敗: {e}")
            return {}
