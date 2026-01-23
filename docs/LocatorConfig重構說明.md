# LocatorConfig 安全重構說明

## 📋 重構目標

將 MainPage 和 CameraPage 中硬編碼的比例（x_ratio, y_ratio）與偏移量（offset）安全地遷移到 Config 層，確保：
1. **無損替換**：保留原值作為預設參數，確保 config 檔案毀損時 Demo 依然能跑
2. **路徑同步**：所有 image_path 統一由 RES_PATH 拼接生成
3. **業務意義命名**：使用具備業務意義的變數名稱

## 🏗️ 架構設計

### LocatorConfig 類別結構

在 `config.py` 中新增 `LocatorConfig` dataclass，收納所有定位器相關配置：

```python
@dataclass
class LocatorConfig:
    """定位器配置（Locator Configuration）"""
    
    # MainPage 定位器
    MENU_ICON_X_RATIO: float = 0.02
    MENU_ICON_Y_RATIO: float = 0.03
    MENU_ICON_IMAGE: str = "desktop_main/menu_icon.png"
    
    CALENDAR_ICON_X_RATIO: float = 0.92
    CALENDAR_ICON_Y_RATIO: float = 0.04
    CALENDAR_ICON_OFFSET_X: int = 0
    CALENDAR_ICON_OFFSET_Y: int = 0
    CALENDAR_ICON_IMAGE: str = "desktop_main/calendar_icon.png"
    
    # CameraPage 定位器
    SERVER_NODE_X_RATIO: float = 0.05
    SERVER_NODE_Y_RATIO: float = 0.15
    SERVER_NODE_IMAGE: str = "desktop_main/server_node.png"
    
    # ... 更多配置
```

### 配置整合

`LocatorConfig` 實例通過 `ExtendedConfig` 類別整合到 `EnvConfig`：

```python
class ExtendedConfig(DevConfig):
    LOCATOR_CONFIG = _locator_config
```

## 🔧 使用方式

### 安全獲取配置（推薦模式）

在 Page 層使用 `getattr` 並保留原值作為預設參數：

```python
# 🎯 從 LocatorConfig 獲取配置，保留原值作為預設值（安全備案）
locator = getattr(EnvConfig, 'LOCATOR_CONFIG', None)
menu_x_ratio = getattr(locator, 'MENU_ICON_X_RATIO', 0.02) if locator else 0.02
menu_y_ratio = getattr(locator, 'MENU_ICON_Y_RATIO', 0.03) if locator else 0.03
menu_image = getattr(locator, 'MENU_ICON_IMAGE', "desktop_main/menu_icon.png") if locator else "desktop_main/menu_icon.png"

success = self.smart_click(
    x_ratio=menu_x_ratio,
    y_ratio=menu_y_ratio,
    image_path=menu_image,  # 傳入相對路徑，smart_click 內部會統一由 RES_PATH 拼接
    timeout=3
)
```

### 安全備案機制

**三層保護**：
1. **第一層**：`getattr(EnvConfig, 'LOCATOR_CONFIG', None)` - 如果 `LOCATOR_CONFIG` 不存在，返回 `None`
2. **第二層**：`getattr(locator, 'MENU_ICON_X_RATIO', 0.02) if locator else 0.02` - 如果 `locator` 為 `None` 或屬性不存在，使用預設值
3. **第三層**：預設值與原本硬編碼的值相同，確保行為一致

## 📝 已重構的定位器

### MainPage

| 配置項 | 原值 | 配置名稱 | 說明 |
|--------|------|----------|------|
| 主選單圖標 X | 0.02 | `MENU_ICON_X_RATIO` | 左上角菜單圖標 |
| 主選單圖標 Y | 0.03 | `MENU_ICON_Y_RATIO` | 左上角菜單圖標 |
| 主選單圖標圖片 | "desktop_main/menu_icon.png" | `MENU_ICON_IMAGE` | 菜單圖標資源 |
| 本地設置 X | 0.1 | `LOCAL_SETTINGS_X_RATIO` | 選單中的本地設置項目 |
| 本地設置 Y | 0.32 | `LOCAL_SETTINGS_Y_RATIO` | 選單中的本地設置項目 |
| 日曆圖標 X | 0.92 | `CALENDAR_ICON_X_RATIO` | 右下角日曆圖標 |
| 日曆圖標 Y | 0.04 | `CALENDAR_ICON_Y_RATIO` | 右下角日曆圖標（從底部計算） |
| 日曆圖標偏移 X | 0 | `CALENDAR_ICON_OFFSET_X` | 日曆圖標點擊偏移 |
| 日曆圖標偏移 Y | 0 | `CALENDAR_ICON_OFFSET_Y` | 日曆圖標點擊偏移 |
| 日曆圖標圖片 | "desktop_main/calendar_icon.png" | `CALENDAR_ICON_IMAGE` | 日曆圖標資源 |
| 日期點擊偏移 X | 5 | `DATE_CLICK_OFFSET_X` | 補償 VLM 偏左誤差 |
| 日期點擊偏移 Y | 15 | `DATE_CLICK_OFFSET_Y` | 補償 VLM 偏上誤差 |
| 日期備選偏移 X | 0 | `DATE_FALLBACK_OFFSET_X` | 備選日期點擊偏移 |
| 日期備選偏移 Y | 0 | `DATE_FALLBACK_OFFSET_Y` | 備選日期點擊偏移 |

### CameraPage

| 配置項 | 原值 | 配置名稱 | 說明 |
|--------|------|----------|------|
| 伺服器節點 X | 0.05 | `SERVER_NODE_X_RATIO` | 右鍵點擊伺服器節點 |
| 伺服器節點 Y | 0.15 | `SERVER_NODE_Y_RATIO` | 右鍵點擊伺服器節點 |
| 伺服器節點圖片 | "desktop_main/server_node.png" | `SERVER_NODE_IMAGE` | 伺服器節點資源 |
| 添加攝影機選單 X | 0.1 | `ADD_CAMERA_MENU_X_RATIO` | 右鍵選單中的添加攝影機 |
| 添加攝影機選單 Y | 0.2 | `ADD_CAMERA_MENU_Y_RATIO` | 右鍵選單中的添加攝影機 |
| 添加攝影機選單圖片 | "desktop_main/add_camera_menu.png" | `ADD_CAMERA_MENU_IMAGE` | 添加攝影機選單資源 |
| 攝影機設定選單 X | 0.22 | `CAMERA_SETTINGS_MENU_X_RATIO` | 右鍵選單中的攝影機設定 |
| 攝影機設定選單 Y | 0.38 | `CAMERA_SETTINGS_MENU_Y_RATIO` | 右鍵選單中的攝影機設定 |
| 攝影機設定選單圖片 | "desktop_main/camera_settings_menu.png" | `CAMERA_SETTINGS_MENU_IMAGE` | 攝影機設定選單資源 |
| 錄影分頁簽 X | 0.25 | `RECORDING_TAB_X_RATIO` | 攝影機設定視窗中的錄影分頁簽 |
| 錄影分頁簽 Y 列表 | [0.10, 0.12, 0.15, 0.08] | `RECORDING_TAB_Y_RATIOS` | 嘗試多個垂直位置 |
| 錄影分頁簽圖片 | "desktop_settings/recording_tab.png" | `RECORDING_TAB_IMAGE` | 錄影分頁簽資源 |
| Radio Y X | 0.10 | `RADIO_Y_X_RATIO` | 錄影分頁簽中的啟用錄影選項 |
| Radio Y Y | 0.15 | `RADIO_Y_Y_RATIO` | 錄影分頁簽中的啟用錄影選項 |

## 🛡️ 安全機制

### 1. 無損替換

所有配置獲取都使用三層保護：

```python
# 第一層：檢查 LOCATOR_CONFIG 是否存在
locator = getattr(EnvConfig, 'LOCATOR_CONFIG', None)

# 第二層：檢查 locator 是否為 None，並獲取屬性
menu_x_ratio = getattr(locator, 'MENU_ICON_X_RATIO', 0.02) if locator else 0.02

# 第三層：預設值與原硬編碼值相同，確保行為一致
```

### 2. 路徑統一

所有 `image_path` 都：
- 在 `LocatorConfig` 中存儲為相對路徑（相對於 `res/`）
- 傳入 `smart_click` 時直接使用相對路徑
- `smart_click` 內部會統一由 `RES_PATH` 拼接

```python
# LocatorConfig 中
MENU_ICON_IMAGE: str = "desktop_main/menu_icon.png"

# Page 層使用
image_path=menu_image  # 傳入相對路徑

# smart_click 內部處理（在 base/desktop_app.py 中）
if image_path.startswith("res/") or image_path.startswith("res\\"):
    image_path = image_path[4:]
full_img = os.path.normpath(os.path.join(EnvConfig.RES_PATH, image_path))
```

## ✅ 重構檢查清單

- [x] 創建 `LocatorConfig` 類別
- [x] 收納 MainPage 硬編碼參數
- [x] 收納 CameraPage 硬編碼參數
- [x] 使用業務意義命名
- [x] 在 Page 層使用 `getattr` 並保留原值作為預設參數
- [x] 確保 image_path 統一由 RES_PATH 拼接
- [x] 語法檢查通過
- [x] 配置載入測試通過

## 📚 相關文件

- `config.py` - LocatorConfig 定義
- `pages/desktop/main_page.py` - MainPage 重構範例
- `pages/desktop/camera_page.py` - CameraPage 重構範例
- `base/desktop_app.py` - smart_click 路徑處理邏輯

## 🔄 後續擴展

如果需要添加新的定位器配置：

1. 在 `LocatorConfig` 中添加新屬性
2. 在對應的 Page 方法中使用 `getattr` 獲取配置
3. 保留原值作為預設參數

範例：

```python
# 1. 在 LocatorConfig 中添加
NEW_BUTTON_X_RATIO: float = 0.5
NEW_BUTTON_Y_RATIO: float = 0.5
NEW_BUTTON_IMAGE: str = "desktop_main/new_button.png"

# 2. 在 Page 中使用
locator = getattr(EnvConfig, 'LOCATOR_CONFIG', None)
new_x = getattr(locator, 'NEW_BUTTON_X_RATIO', 0.5) if locator else 0.5
new_y = getattr(locator, 'NEW_BUTTON_Y_RATIO', 0.5) if locator else 0.5
new_image = getattr(locator, 'NEW_BUTTON_IMAGE', "desktop_main/new_button.png") if locator else "desktop_main/new_button.png"
```
