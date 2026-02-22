# Kids Voice Assistant

<img width="1024" height="1536" alt="image" src="https://github.com/user-attachments/assets/b2988317-2733-4e27-be51-e47f042ae642" />


A voice assistant project for kids that is friendly, helpful, and not intrusive.

This project is designed as a configurable system that can be used as a personal assistant in a kid's room. The focus is a safe, simple, and practical daily setup.

## Current Status

The current version uses a "Makro"-style implementation:
- A Python script opens Google AI Studio Live in the background.
- It handles browser actions automatically (open page, apply system instructions, press Talk).
- In daily use, this works quite well.

You can run this setup easily on a Raspberry Pi, and that is how I run it in practice.

## Vision

The long-term vision is a configurable voice-agent platform for children:
- Personal assistant experience in each kid's room.
- Helpful but not intrusive behavior.
- Kid-friendly responses and interaction style.

The next technical step is moving from browser automation (Makro style) to a direct realtime voice architecture using either:
- Google realtime APIs, or
- OpenAI Realtime API.

The core goals remain:
- Speak in multiple languages in a kid-friendly tone.
- Wake up on demand and go back to sleep automatically.
- Keep conversational context.
- Run reliably on a Raspberry Pi.

That migration is planned, but this project is not there yet.

## Installation

Run from the `server/` folder.

### 1. Python environment

Use Python 3.10+ and install dependencies:

```bash
pip install playwright python-dotenv
playwright install chromium
```

### 2. Optional environment settings

Create `.env` in the project root or in `server/` if you want to define custom values (for example `CHROMIUM_EXECUTABLE`).

## Run

```bash
cd server
python main.py
```

On first run, the script may ask for manual Google login in the opened browser window.

## Raspberry Pi: Auto-start on boot

On Raspberry Pi, run the script automatically with `systemd`.

Create `/etc/systemd/system/kids-voice-agent.service`:

```ini
[Unit]
Description=Kids Voice Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/react-voice-agent/server
ExecStart=/usr/bin/python3 /home/pi/react-voice-agent/server/main.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable kids-voice-agent.service
sudo systemctl start kids-voice-agent.service
sudo systemctl status kids-voice-agent.service
```

## Google-side Configuration (Current Makro Implementation)

For the current implementation, configure these items on the Google side:

1. Use a Google account that has access to AI Studio Live.
2. Open `https://aistudio.google.com/live` once manually and verify login works.
3. Grant microphone permission in the browser profile used by the script.
4. If prompted, grant camera permission too (the script requests both).
5. Keep using the same persistent browser profile (`server/user_data`) so login/session is remembered.
6. Ensure the Live page and Talk button are available for that account and region.
7. If login loops or UI controls are not found, re-login manually and retry.

## My current Assistant
The System message for my current assistant is:
"Your name is Lexa. Speak in child friendly tone. Omit all critical topics. Always be friendly."

My setup currently looks like:
<img width="752" height="1002" alt="image" src="https://github.com/user-attachments/assets/e1a3c1aa-55bc-4730-a0c2-03455ad7b149" />


<img width="752" height="1002" alt="image" src="https://github.com/user-attachments/assets/297db9e7-431c-4de9-9f50-8b19253adb28" />


I am using the following components:

- Raspberry Pi 5 8GB
- A USB-Soundcard with integrated Microphone and external Speakers (Bluetooth-Speakers would work as well!)
- An extra power supply to easily turn the Raspberry on and off.



## Notes

- The script uses Playwright with a persistent Chromium profile.
- If Chromium is installed in a non-standard location, set `CHROMIUM_EXECUTABLE`.
- If automation fails to find controls, screenshots are saved in `server/` for debugging.
- This 
