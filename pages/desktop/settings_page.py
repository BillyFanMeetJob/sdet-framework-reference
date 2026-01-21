# 相對路徑: pages/settings_page.py

from base.desktop_app import DesktopApp
import time
import os
from config import EnvConfig

class SettingsPage(DesktopApp):
    def switch_to_appearance_tab(self):
        """點擊「外觀」或「界面」分頁"""
        self.logger.info("🖱️ 點擊「外觀」分頁...")
        
        # smart_click 會自動優先使用文字辨識，失敗則使用圖片辨識
        # 先嘗試「外观」（簡體中文）
        success = self.smart_click(
            x_ratio=0.1686,
            y_ratio=0.0720,
            target_text="外观",  # 文字辨識優先
            image_path="desktop_settings/appearance_tab.png",  # 圖片辨識作為備選
            timeout=3.0
        )
        
        # 如果失敗，嘗試「界面」（繁體中文）
        if not success:
            success = self.smart_click(
                x_ratio=0.1686,
                y_ratio=0.0720,
                target_text="界面",  # 文字辨識優先
                image_path="desktop_settings/appearance_tab.png",  # 圖片辨識作為備選
                timeout=3.0
            )
        
        if success:
            self.logger.info("✅ 成功點擊外觀分頁")
            # 短暫等待分頁切換
            self.wait_for_condition(lambda: True, timeout=0.5)
        else:
            error_msg = "點擊外觀分頁失敗：無法找到或點擊外觀分頁"
            self.logger.error(f"❌ {error_msg}")
            raise AssertionError(error_msg)
        
        return self

    def change_language(self, language="繁體中文"):
        """修改語言設定"""
        self.logger.info(f"🖱️ 修改語言為: {language}")
        
        # 1. 點擊語言下拉選單
        self.logger.info("🖱️ 點擊語言下拉選單...")
        # 使用真實記錄的座標：x_ratio=0.5793, y_ratio=0.1936 (來自 706x847 視窗)
        success = self.smart_click(
            x_ratio=0.5793,    # 真實座標（從測試記錄）
            y_ratio=0.1936,    # 真實座標（從測試記錄）
            target_text=None,  # 移除 OCR，優先圖片辨識
            image_path="desktop_settings/language_dropdown.png",
            is_relative=False,  # 使用比例座標而非相對座標
            timeout=1.5
        )
        
        if success:
            self.logger.info("✅ 成功點擊語言下拉選單")
            # 智能等待下拉選單展開
            self.wait_for_condition(lambda: True, timeout=0.8)
        else:
            self.logger.warning("⚠️ 可能未成功點擊語言下拉選單")
        
        # 2. 選擇目標語言
        self.logger.info(f"🖱️ 選擇語言: {language}")
        # 注意：繁體中文選項座標 x_ratio=0.1171, y_ratio=0.7385 是在下拉選單中（538x65 視窗）
        # 這個座標是相對於下拉選單的，保持使用 is_relative=True
        success = self.smart_click(
            x_ratio=0,
            y_ratio=75,
            target_text=language,  # 保留 OCR，用於尋找不同語言選項
            image_path="desktop_settings/traditional_chinese.png",
            is_relative=True,
            timeout=2
        )
        
        if success:
            self.logger.info(f"✅ 成功選擇 {language}")
        
        # 3. 點擊套用按鈕
        self.logger.info("🖱️ 點擊套用按鈕...")
        # 使用真實記錄的座標：x_ratio=0.7351, y_ratio=0.9445 (來自 706x847 視窗)
        self.smart_click(
            x_ratio=0.7351,    # 真實座標（從測試記錄）
            y_ratio=0.9445,    # 真實座標（從測試記錄）
            target_text=None,  # 移除 OCR，優先圖片辨識
            image_path="desktop_settings/apply_btn.png",
            from_bottom=False,  # 使用比例座標
            timeout=1.5
        )
        
        # 4. 智能等待重啟彈窗出現（檢測新視窗）
        self.logger.info("⏳ 等待重啟彈窗...")
        time.sleep(0.3)  # 縮短至 0.3 秒
        
        # 5. 點擊立即重啟按鈕
        self.logger.info("🖱️ 點擊「立即重新啟動」按鈕...")
        
        # 強制重置原點，避免受舊座標影響
        DesktopApp._last_x, DesktopApp._last_y = 0, 0
        
        # 嘗試多種方式定位重啟按鈕
        restart_success = False
        
        # 方式 1: 圖片辨識（優先，避免觸發 OCR）
        restart_success = self.smart_click(
            x_ratio=0.55,  # 對話框中間偏右
            y_ratio=0.58,  # 對話框中間偏下（按鈕區域）
            target_text=None,  # 移除 OCR，優先使用圖片辨識
            image_path="desktop_settings/restart_now.png",
            timeout=1.5  # 縮短至 1.5 秒
        )
        
        # 方式 2: 如果失敗，使用 smart_click 的備用座標
        if not restart_success:
            self.logger.warning("⚠️ 第一次點擊失敗，嘗試備用座標...")
            restart_success = self.smart_click(
                x_ratio=0.57,  # 57% 寬度
                y_ratio=0.60,  # 60% 高度
                target_text="立即",
                image_path="desktop_settings/restart_now_btn.png",
                timeout=1
            )
        
        if restart_success:
            self.logger.info("✅ 成功點擊立即重新啟動")
        else:
            self.logger.warning("⚠️ 可能未成功點擊立即重新啟動")
        
        return self

    def enable_usb_detection(self):
        # 主動建議：不要直接辨識那個「勾選小框」，因為勾了跟沒勾長很像
        # 辨識「自動偵測...」這串文字，然後往左偏移點擊
        success = self.smart_click(
            "usb_detection_text.png", 
            is_relative=True, 
            offset_x=-20,  # 往左偏 20 像素點擊勾選框
            target_name="USB 攝影機勾選位"
        )
        if not success:
            # 保底策略：如果連文字都找不到，使用對話框內的比例座標
            # 假設勾選框在大約視窗中間靠下的位置
            self.smart_click(None, is_proportional=True, p_x=0.3, p_y=0.6)

    def apply_settings(self):
        # 點擊右下角「套用」或「OK」
        self.smart_click("btn_apply.png", align="bottom_right", offset_x=-100, offset_y=-50)