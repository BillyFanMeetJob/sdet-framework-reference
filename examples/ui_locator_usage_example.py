#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UILocator 使用示例

展示如何使用 UILocator 類來簡化 Page 層的代碼。
"""

from config import EnvConfig, UILocator
from base.desktop_app import DesktopApp


class ExamplePage(DesktopApp):
    """示例頁面類"""
    
    def __init__(self):
        super().__init__()
        # 獲取配置中的定位器
        self.locator_config = EnvConfig.LOCATOR_CONFIG
    
    # ==================== 方式 1：直接使用配置中的定位器 ====================
    
    def click_menu_icon_v1(self):
        """使用配置中的定位器點擊菜單圖標"""
        # ✅ 簡潔：直接使用配置中的 UILocator
        return self.click_with_locator(self.locator_config.MENU_ICON)
    
    def click_calendar_icon_v1(self):
        """使用配置中的定位器點擊日曆圖標"""
        return self.click_with_locator(self.locator_config.CALENDAR_ICON)
    
    # ==================== 方式 2：動態創建定位器 ====================
    
    def click_custom_button(self):
        """動態創建定位器"""
        # ✅ 靈活：根據需要動態創建定位器
        custom_locator = UILocator(
            x_ratio=0.5,
            y_ratio=0.5,
            image_path="custom/button.png",
            target_text="確認",
            timeout=5
        )
        return self.click_with_locator(custom_locator)
    
    # ==================== 方式 3：修改現有定位器 ====================
    
    def click_menu_with_offset(self):
        """使用帶偏移的定位器"""
        # ✅ 便捷：基於現有定位器創建變體
        menu_with_offset = self.locator_config.MENU_ICON.with_offset(
            offset_x=10,
            offset_y=5
        )
        return self.click_with_locator(menu_with_offset)
    
    def click_server_tile_with_text(self, server_name: str):
        """使用帶文字的定位器"""
        # ✅ 靈活：添加動態文字
        server_locator = self.locator_config.SERVER_TILE.with_text(server_name)
        return self.click_with_locator(server_locator)
    
    # ==================== 方式 4：組合使用 ====================
    
    def select_language(self, language: str):
        """選擇語言（組合使用多個定位器）"""
        # 1. 點擊語言下拉選單
        if not self.click_with_locator(self.locator_config.LANGUAGE_DROPDOWN):
            return False
        
        # 2. 選擇繁體中文（使用相對定位器）
        if "繁體" in language:
            return self.click_with_locator(self.locator_config.TRADITIONAL_CHINESE)
        
        return False
    
    # ==================== 對比：舊方式 vs 新方式 ====================
    
    def click_menu_old_way(self):
        """❌ 舊方式：需要傳入大量參數"""
        return self.smart_click(
            x_ratio=0.02,
            y_ratio=0.03,
            image_path="desktop_main/menu_icon.png",
            target_text=None,
            timeout=3,
            is_relative=False,
            from_bottom=False,
            clicks=1,
            click_type='left',
            use_ok_script=True,
            use_vlm=None,
            offset_x=0,
            offset_y=0
        )
    
    def click_menu_new_way(self):
        """✅ 新方式：簡潔明了"""
        return self.click_with_locator(self.locator_config.MENU_ICON)
    
    # ==================== 高級用法：鏈式調用 ====================
    
    def click_relative_button(self):
        """鏈式調用創建複雜定位器"""
        # ✅ 優雅：鏈式調用修改定位器屬性
        locator = (self.locator_config.MENU_ICON
                   .with_offset(offset_x=50, offset_y=20)
                   .with_text("設置")
                   .as_relative())
        return self.click_with_locator(locator)


# ==================== 使用示例 ====================

def main():
    """主函數：展示各種用法"""
    page = ExamplePage()
    
    print("=" * 60)
    print("UILocator 使用示例")
    print("=" * 60)
    
    # 示例 1：使用配置中的定位器
    print("\n1. 使用配置中的定位器：")
    print("   page.click_with_locator(page.locator_config.MENU_ICON)")
    
    # 示例 2：動態創建定位器
    print("\n2. 動態創建定位器：")
    print("   custom_locator = UILocator(x_ratio=0.5, y_ratio=0.5, ...)")
    print("   page.click_with_locator(custom_locator)")
    
    # 示例 3：修改現有定位器
    print("\n3. 修改現有定位器：")
    print("   menu_with_offset = page.locator_config.MENU_ICON.with_offset(10, 5)")
    print("   page.click_with_locator(menu_with_offset)")
    
    # 示例 4：鏈式調用
    print("\n4. 鏈式調用：")
    print("   locator = (page.locator_config.MENU_ICON")
    print("              .with_offset(50, 20)")
    print("              .with_text('設置')")
    print("              .as_relative())")
    print("   page.click_with_locator(locator)")
    
    print("\n" + "=" * 60)
    print("優勢：")
    print("  ✅ 代碼更簡潔（減少 80% 的參數傳遞）")
    print("  ✅ 可讀性更高（語義化的定位器名稱）")
    print("  ✅ 易於維護（集中管理配置）")
    print("  ✅ 類型安全（IDE 自動補全和類型檢查）")
    print("  ✅ 靈活擴展（支持鏈式調用和組合）")
    print("=" * 60)


if __name__ == "__main__":
    main()
