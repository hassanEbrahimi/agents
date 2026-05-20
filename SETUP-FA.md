# راه‌اندازی سریع (فارسی)

## تست صوتی

1. **`run-voice-test.bat`** را دوبار کلیک کنید (یا در CMD اجرا کنید).
   - سرور LiveKit محلی را خودکار بالا می‌آورد
   - بعد ایجنت صوتی را با میکروفون اجرا می‌کند

2. یا دستی در **دو پنجره**:
   - پنجره ۱: `tools\start-livekit-server.bat`
   - پنجره ۲: `py myagent.py console`

## متغیرهای `.env`

| متغیر | توضیح |
|--------|--------|
| `GOOGLE_API_KEY` | کلید Gemini از Google AI Studio |
| `LIVEKIT_URL` | پیش‌فرض: `ws://localhost:7880` (سرور محلی) |
| `LIVEKIT_API_KEY` | پیش‌فرض: `devkey` |
| `LIVEKIT_API_SECRET` | پیش‌فرض: `secret` |

برای **LiveKit Cloud** به‌جای مقادیر محلی، از [cloud.livekit.io](https://cloud.livekit.io) URL و API Key بگیرید.

## عیب‌یابی

- **`LIVEKIT_URL` required** → سرور LiveKit را با `tools\start-livekit-server.bat` اجرا کنید.
- **Unicode / emoji error** → از `run-voice-test.bat` استفاده کنید یا قبل از اجرا: `chcp 65001` و `set PYTHONUTF8=1`
- **میکروفون** → `py myagent.py console --input-device "Realtek"`
