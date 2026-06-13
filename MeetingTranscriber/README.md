# 會議轉文字 (Meeting Transcriber) — Android

私人自用的「錄音 → 轉文字」Android App。手機**直接呼叫雲端語音轉文字 API**(無自建後端),
逐字稿與錄音都存在**手機本機**。API 金鑰由使用者在 App 設定頁手動填入,存於裝置加密區。

主要情境:長時間會議(中文/台灣國語為主),多人對話需區分說話者。

> 完整產品規格見 repo 根目錄規劃文件;本 README 對應 **M1**(直連打通)的實作。

## 技術堆疊
- Kotlin + Jetpack Compose (Material 3)、Navigation Compose
- ViewModel + Coroutines/Flow
- Room(本機儲存錄音與逐字稿)
- OkHttp + kotlinx.serialization(呼叫 STT API)
- security-crypto(EncryptedSharedPreferences,存放 API 金鑰)
- minSdk 26 / targetSdk 34

## 供應商
以 Provider 介面封裝,設定頁可切換,App 不依賴特定廠商:
- **ElevenLabs Scribe**(預設,中文準確度高、內建說話者分離)— `stt/ElevenLabsProvider.kt`
- **Deepgram Nova-3**(省成本備援)— `stt/DeepgramProvider.kt`

抽象介面與工廠:`stt/SttProvider.kt`、`stt/SttProviderFactory.kt`。

## M1 已實作功能
- 設定頁:選供應商、填各家 API 金鑰(加密儲存)、語言代碼、是否開啟說話者分離
- 錄音:`MediaRecorder`,16 kHz / mono / AAC(.m4a)
- **匯入既有音檔**轉譯(Storage Access Framework)
- 直連 STT 取得逐字稿 → 正規化為 `Transcript { segments[speaker, start, end, text] }`
- 錄音列表(待轉譯/轉譯中/完成/失敗)+ 逐字稿檢視(依說話者分段、時間戳)、複製全文
- **失敗保留音檔**並可一鍵重試

尚未包含(後續里程碑):長時間前景錄音服務、長音檔自動分段、播放跳轉、搜尋/匯出、
用量成本估算、Deepgram A/B 實測。詳見規劃文件 M2–M4。

## 建置與執行
需要 Android SDK(本 repo 容器未內建,請在本機 / Android Studio 操作)。

```bash
cd MeetingTranscriber
# Android Studio 直接 Open 此資料夾即可;或命令列:
./gradlew assembleDebug
./gradlew installDebug   # 連接裝置/模擬器後安裝
```

首次啟動 → 進入「設定」填入 ElevenLabs(或 Deepgram)API 金鑰 → 回首頁開始錄音或匯入音檔。

## 隱私
- 金鑰只存在裝置加密區(`EncryptedSharedPreferences`),不進原始碼、不進 git。
- 音檔僅在轉譯時上傳所選供應商;請留意該供應商的資料保留政策。
- 此為**個人自用**設計。若日後要把 APK 分享他人,金鑰會被反編譯抽出 → 屆時需改為後端代理架構。
