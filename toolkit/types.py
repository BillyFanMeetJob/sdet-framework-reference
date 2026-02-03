# toolkit/types.py

import math
from dataclasses import dataclass
from typing import Tuple, List, Dict, Any, Callable
from selenium.webdriver.common.by import By

# 定義 Locator 類型（Selenium 定位器）
# 例如：(By.ID, "username") 或 (By.XPATH, "//button[@class='submit']")
Locator = Tuple[By, str]

# 定義座標類型
Coordinate = Tuple[int, int]

# 定義區域類型 (x, y, width, height)
Region = Tuple[int, int, int, int]

# Step 與 Action 相關類型
Step = Dict[str, Any]
StepList = List[Step]

# Action function 型別：某個可被呼叫的流程函式
ActionFunc = Callable[..., Any]
# Action 對照表：action_name → Action function
ActionMap = Dict[str, ActionFunc]


@dataclass
class Area:
    """表示螢幕上的矩形區域。
    
    Attributes:
        x1: 左上角 X 座標
        y1: 左上角 Y 座標
        x2: 右下角 X 座標
        y2: 右下角 Y 座標
    """
    x1: int
    y1: int
    x2: int
    y2: int
    
    @property
    def width(self) -> int:
        """計算區域寬度。
        
        Returns:
            區域寬度（像素）
        """
        return self.x2 - self.x1
    
    @property
    def height(self) -> int:
        """計算區域高度。
        
        Returns:
            區域高度（像素）
        """
        return self.y2 - self.y1
    
    @property
    def center(self) -> Tuple[int, int]:
        """計算區域中心點座標。
        
        Returns:
            中心點座標 (x, y)
        """
        return (
            (self.x1 + self.x2) // 2,
            (self.y1 + self.y2) // 2
        )
    
    def to_tuple(self) -> Tuple[int, int, int, int]:
        """轉換為元組格式 (x1, y1, x2, y2)。
        
        Returns:
            包含四個座標值的元組
        """
        return (self.x1, self.y1, self.x2, self.y2)


class Toolkit:
    """提供座標計算與幾何運算的工具方法。"""
    
    @staticmethod
    def calculate_center(area: Area) -> Tuple[int, int]:
        """計算區域的中心點座標。
        
        Args:
            area: Area 物件，包含矩形區域的四個角座標
            
        Returns:
            中心點座標 (center_x, center_y)
            
        Example:
            >>> area = Area(x1=100, y1=100, x2=200, y2=200)
            >>> Toolkit.calculate_center(area)
            (150, 150)
        """
        center_x = (area.x1 + area.x2) // 2
        center_y = (area.y1 + area.y2) // 2
        return (center_x, center_y)
    
    @staticmethod
    def calculate_distance(p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
        """計算兩組座標間的歐幾里得距離。
        
        使用歐幾里得距離公式：
        distance = sqrt((x2 - x1)² + (y2 - y1)²)
        
        Args:
            p1: 第一個點的座標 (x1, y1)
            p2: 第二個點的座標 (x2, y2)
            
        Returns:
            兩點之間的歐幾里得距離（像素）
            
        Example:
            >>> Toolkit.calculate_distance((0, 0), (3, 4))
            5.0
        """
        return math.dist(p1, p2)
    
    @staticmethod
    def calculate_top_left_from_center(
        center: Tuple[int, int],
        width: int,
        height: int
    ) -> Tuple[int, int]:
        """從中心點座標計算左上角座標。
        
        計算公式：
        - top_left_x = center_x - width / 2
        - top_left_y = center_y - height / 2
        
        Args:
            center: 中心點座標 (center_x, center_y)
            width: 物件寬度（像素）
            height: 物件高度（像素）
            
        Returns:
            左上角座標 (top_left_x, top_left_y)
            
        Example:
            >>> Toolkit.calculate_top_left_from_center((150, 150), 100, 100)
            (100, 100)
        """
        center_x, center_y = center
        top_left_x = int(center_x - width / 2)
        top_left_y = int(center_y - height / 2)
        return (top_left_x, top_left_y)
    
    @staticmethod
    def create_area_from_center(
        center: Tuple[int, int],
        width: int,
        height: int
    ) -> Area:
        """從中心點座標創建 Area 物件。
        
        Args:
            center: 中心點座標 (center_x, center_y)
            width: 物件寬度（像素）
            height: 物件高度（像素）
            
        Returns:
            Area 物件，包含計算後的四個角座標
            
        Example:
            >>> area = Toolkit.create_area_from_center((150, 150), 100, 100)
            >>> area.to_tuple()
            (100, 100, 200, 200)
        """
        center_x, center_y = center
        half_width = width / 2
        half_height = height / 2
        
        return Area(
            x1=int(center_x - half_width),
            y1=int(center_y - half_height),
            x2=int(center_x + half_width),
            y2=int(center_y + half_height)
        )
