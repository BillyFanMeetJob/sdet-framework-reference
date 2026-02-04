# 相對路徑: pages/settings_page.py

from base.desktop_app import DesktopApp
import time
import os
from config import EnvConfig

class SettingsPage(DesktopApp):
    def switch_to_appearance_tab(self):
        """點擊「外觀」或「界面」分頁 - 圖片優先，VLM 為輔"""
        self.logger.info("🖱️ 點擊「外觀」分頁...")
        
        # 🎯 策略：圖片優先，VLM 為輔
        # 設置 use_vlm=False 以啟用「圖片優先」模式
        # 在圖片優先模式下，smart_click 會先嘗試圖片，失敗後再嘗試 VLM
        success = self.smart_click(
            x_ratio=0.1686,
            y_ratio=0.0720,
            target_text="界面外观",  # 保留文字，作為 VLM 備選
            image_path="desktop_settings/appearance_tab.png",  # 圖片優先
            use_ok_script=True,  # 啟用圖片辨識
            use_vlm=False,  # 設置為 False 以啟用「圖片優先」模式（VLM 作為備選）
            timeout=3.0
        )
        
        # 如果失敗，嘗試繁體中文
        if not success:
            success = self.smart_click(
                x_ratio=0.1686,
                y_ratio=0.0720,
                target_text="界面外觀",  # 保留文字，作為 VLM 備選
                image_path="desktop_settings/appearance_tab.png",  # 圖片優先
                use_ok_script=True,  # 啟用圖片辨識
                use_vlm=False,  # 設置為 False 以啟用「圖片優先」模式
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
        
        # 🎯 從 LocatorConfig 獲取配置
        from config import EnvConfig
        locator = getattr(EnvConfig, 'LOCATOR_CONFIG', None)
        dropdown_x = getattr(locator, 'LANGUAGE_DROPDOWN_X_RATIO', 0.5793) if locator else 0.5793
        dropdown_y = getattr(locator, 'LANGUAGE_DROPDOWN_Y_RATIO', 0.1936) if locator else 0.1936
        dropdown_image = getattr(locator, 'LANGUAGE_DROPDOWN_IMAGE', "desktop_settings/language_dropdown.png") if locator else "desktop_settings/language_dropdown.png"
        
        success = self.smart_click(
            x_ratio=dropdown_x,
            y_ratio=dropdown_y,
            target_text=None,  # 移除 OCR，優先圖片辨識
            image_path=dropdown_image,
            is_relative=False,  # 使用比例座標而非相對座標
            timeout=1.5
        )
        
        if success:
            self.logger.info("✅ 成功點擊語言下拉選單")
            # 智能等待下拉選單展開（增加等待時間確保完全展開）
            import time
            time.sleep(0.5)  # 固定等待 0.5 秒
            self.wait_for_condition(lambda: True, timeout=0.5)  # 額外等待最多 0.5 秒
        else:
            self.logger.warning("⚠️ 可能未成功點擊語言下拉選單")
        
        # 2. 選擇目標語言
        self.logger.info(f"🖱️ 選擇語言: {language}")
        
        # 🎯 策略：圖片優先，VLM 為輔，OCR 備選，座標保底
        # 已知下拉選單只有兩個選項，不需要捲動
        success = False
        
        # 策略 1: 圖片辨識優先（最穩定）
        # 繁體中文通常是第一個選項，位置在語言下拉選單下方約 30-50 像素處
        if "繁體" in language or "Traditional" in language:
            self.logger.info("[語言選擇] 嘗試圖片辨識：traditional_chinese.png")
            
            # 🎯 從 LocatorConfig 獲取配置
            offset_x = getattr(locator, 'TRADITIONAL_CHINESE_OFFSET_X', 0) if locator else 0
            offset_y = getattr(locator, 'TRADITIONAL_CHINESE_OFFSET_Y', 40) if locator else 40
            chinese_image = getattr(locator, 'TRADITIONAL_CHINESE_IMAGE', "desktop_settings/traditional_chinese.png") if locator else "desktop_settings/traditional_chinese.png"
            
            # 使用相對座標，從上次點擊位置（語言下拉選單）向下偏移
            success = self.smart_click(
                x_ratio=offset_x,  # 保持 X 座標不變（相對於上次點擊）
                y_ratio=offset_y,  # 向下偏移（第一個選項位置）
                target_text=None,  # 禁用文字辨識，優先圖片
                image_path=chinese_image,
                is_relative=True,  # 使用相對座標
                use_ok_script=True,
                use_vlm=False,  # 圖片優先模式
                timeout=2
            )
        
        # 策略 2: 如果圖片失敗，嘗試 VLM（理解自然語言）
        if not success:
            self.logger.info(f"[語言選擇] 圖片失敗，嘗試 VLM 備選: '{language}'")
            # 構建多語言搜索文本
            search_texts = []
            if "繁體" in language or "Traditional" in language:
                search_texts = ["繁體中文", "Chinese (Traditional)", "Traditional Chinese", "Traditional"]
            elif "简体" in language or "Simplified" in language:
                search_texts = ["简体中文", "Chinese (Simplified)", "Simplified Chinese", "Simplified"]
            elif "English" in language or "英文" in language:
                search_texts = ["English", "英文"]
            
            for search_text in search_texts:
                self.logger.info(f"[語言選擇] VLM 搜索: '{search_text}'")
                success = self.smart_click(
                    x_ratio=0.5,  # 下拉選單中央
                    y_ratio=0.5,  # 下拉選單中央
                    target_text=search_text,
                    image_path=None,  # 不使用圖片
                    use_ok_script=False,
                    use_vlm=True,  # 啟用 VLM
                    timeout=2
                )
                if success:
                    break
        
        # 策略 3: 如果 VLM 失敗，嘗試 OCR
        if not success:
            self.logger.info(f"[語言選擇] VLM 失敗，嘗試 OCR 備選: '{language}'")
            success = self.smart_click(
                x_ratio=0.5,
                y_ratio=0.5,
                target_text=language,
                image_path=None,
                use_ok_script=False,
                use_vlm=False,  # 禁用 VLM，只使用 OCR
                timeout=2
            )
        
        # 策略 4: 如果都失敗，使用座標保底（已知下拉選單只有兩個選項）
        if not success:
            self.logger.warning(f"[語言選擇] 所有辨識方法失敗，使用座標保底")
            # 繁體中文通常是第一個選項，座標在中央偏上
            win = self.get_nx_window()
            if win:
                # 計算下拉選單中央位置（假設下拉選單在對話框中央）
                center_x = win.left + (win.width // 2)
                center_y = win.top + int(win.height * 0.25)  # 第一個選項通常在 25% 高度處
                import pyautogui
                pyautogui.click(center_x, center_y)
                self.logger.info(f"[語言選擇] 座標保底點擊: ({center_x}, {center_y})")
                success = True
            else:
                self.logger.error("[語言選擇] 無法獲取視窗，座標保底失敗")
        
        if success:
            self.logger.info(f"✅ 成功選擇 {language}")
        else:
            self.logger.error(f"❌ 選擇語言失敗: {language}")
            raise AssertionError(f"無法選擇語言: {language}")
        
        # 3. 點擊套用按鈕
        self.logger.info("🖱️ 點擊套用按鈕...")
        
        # 🎯 從 LocatorConfig 獲取配置
        apply_x = getattr(locator, 'APPLY_BTN_X_RATIO', 0.7351) if locator else 0.7351
        apply_y = getattr(locator, 'APPLY_BTN_Y_RATIO', 0.9445) if locator else 0.9445
        apply_image = getattr(locator, 'APPLY_BTN_IMAGE', "desktop_settings/apply_btn.png") if locator else "desktop_settings/apply_btn.png"
        
        self.smart_click(
            x_ratio=apply_x,
            y_ratio=apply_y,
            target_text=None,  # 移除 OCR，優先圖片辨識
            image_path=apply_image,
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