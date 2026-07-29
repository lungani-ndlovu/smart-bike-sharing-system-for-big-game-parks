# 🚴 SafariCycle — Smart Bike Sharing System for Game Parks

IoT-based automatic bike rental system for large game parks. Visitors use an Android app to locate a bike, pay, and unlock it remotely. Bikes are GPS-tracked in real time, and an emergency panic button alerts park rangers instantly.
---

## ✨ Features

- 📱 Android app — bike location, cashless payments, ride tracking
- 🔒 Remote solenoid lock — unlocks automatically after successful payment
- 📍 Real-time GPS tracking via GSM to Firebase
- 🚨 Emergency panic button — logs location and timestamp for ranger response
- 📊 Python/Streamlit admin dashboard — fleet status, ride stats, emergency alerts

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Mobile App | Android (Java) |
| Firmware | C++ (Arduino IDE / ESP32) |
| Backend | Firebase Realtime Database, Firebase Auth |
| Dashboard | Python, Streamlit, Plotly |
| GPS | Ublox Neo-6M V2, TinyGPSPlus |
| GSM | SIM800L, TinyGSM |

---


## 🚀 Getting Started

### Firmware

1. Copy `secrets.h.example` → `secrets.h` and fill in your credentials
2. Install Arduino libraries (see below)
3. Upload `.ino` to your ESP32 via Arduino IDE

### Dashboard

See [`dashboard/README.md`](dashboard/README.md)

---

## 📚 Arduino Libraries

Install via **Arduino IDE → Tools → Manage Libraries**:

| Library | Author |
|---------|--------|
| TinyGSM | Volodymyr Shymanskyy |
| TinyGPSPlus | Mikal Hart |
| FirebaseClient | Mobizt |
| Firebase ESP Client | Mobizt |
| ArduinoJson | Benoit Blanchon |
| EspSoftwareSerial | Dirk Kaar |

---

## 👤 Author

**Lungani Ndlovu**
📧 lunganindlovu601@gmail.com
