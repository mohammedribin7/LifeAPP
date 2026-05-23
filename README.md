# My Life Dashboard

A personal life tracking app — habits, goals, health, money — with daily streaks.

## Setup (5 minutes)

### 1. Install Python
Download from https://python.org (if not already installed)

### 2. Install Flask
Open Terminal and run:
```
pip install flask
```

### 3. Run the app
```
cd lifeapp
python app.py
```

### 4. Open in browser
Go to: http://localhost:5000

---

## Use on your iPhone (same Wi-Fi)

1. Find your computer's local IP address:
   - Mac: System Settings → Wi-Fi → Details → IP Address (e.g. 192.168.1.5)
   - Windows: Run `ipconfig` in Command Prompt, look for IPv4 Address

2. On your iPhone browser, go to: `http://192.168.1.5:5000`
   (replace with your actual IP)

3. Add to Home Screen:
   - Tap the Share button in Safari
   - Tap "Add to Home Screen"
   - It opens full screen like a real app!

---

## Features
- Daily habit tracking with streaks (miss one = back to zero!)
- Master streak — only grows if ALL habits are done
- Sleep, water, steps quick logging
- Expense tracking
- Customizable goals with progress bars
- Health stats & sleep history
- Dark mode support
- Data saved locally in data.json

## Files
- app.py — the server
- templates/index.html — the app UI
- data.json — your data (auto-created on first run)
