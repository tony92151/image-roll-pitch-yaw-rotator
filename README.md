---
title: image-roll-pitch-yaw-rotator
emoji: 😻
colorFrom: green
colorTo: indigo
sdk: gradio
sdk_version: 5.23.2
app_file: app.py
pinned: false
license: mit
---

# image-roll-pitch-yaw-rotator

這是一個可部署在 Hugging Face Spaces 的 Gradio 應用程式，讓使用者：

- 上傳照片
- 用 Roll / Pitch / Yaw 三個拉桿調整影像角度
- 透過內建示意圖快速理解三軸的旋轉方向
- 即時看到轉換結果
- 下載轉換後圖片

## Local run

```bash
pip install -r requirements.txt
python app.py
```

## Hugging Face Spaces

1. 在 Hugging Face 建立一個 **Gradio** Space。
2. 上傳這個 repo 檔案（至少包含 `app.py` 與 `requirements.txt`）。
3. Space 會自動安裝依賴並啟動應用程式。
