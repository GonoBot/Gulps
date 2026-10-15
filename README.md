# 📥 Gulps v0.1

A versatile, lightweight, video downloader. It uses `yt-dlp` under the hood to extract and download high-quality videos, audio tracks, and images anonymously from across the multiple website and platform.

---

## ⚠️ Limitations & Scope
- **Anonymous Access Only:** This tool works entirely without logins. It **does not bypass** private accounts, age verifications, DRM restrictions, or paywalls.
- **Binary Processing:** Requires a fully configured system path for `ffmpeg` to process audio conversions or merge distinct high-definition video fragments.

---

## 🚀 Features
- **Smart Site Detection:** Informational tracking for platforms like YouTube, TikTok, Instagram, X/Twitter, Snapchat, Reddit, Pinterest, and more.
- **Multi-Video Extraction:** Automatically detects posts containing multiple items, rendering a numbered list (up to 15 items) with an option to download all at once.
- **Smart Orientation Targeting:** Dynamically adjusts format selectors based on horizontal or vertical aspect ratios to grab the cleanest resolution.
- **X/Twitter Photo Fallback:** Built-in public syndication scraping to grab high-resolution image-only posts that normally break `yt-dlp` engines.
- **Safe Filename Management:** Prevents Android block issues (Errno 36) by safely stripping illegal symbols and strictly shortening long social media text titles during downloads.

---

## 🛠️ Requirements & Installation

**Gulps** is built using standard, universal Python 3. This means the download engine can be executed anywhere Python runs—including Android (Termux), Desktop IDEs (VS Code on Windows/Mac/Linux), or deployed directly as a cloud-hosted Web App.

---

### ⚡ Android / Termux Installation (Quick 1-Liner)

Copy and paste this single command into your Termux app. It will update packages, install system dependencies, clone this repository, configure `yt-dlp`, and launch the interface automatically:

```bash
pkg update && pkg upgrade -y && pkg install python ffmpeg git -y && pip install --upgrade pip yt-dlp && git clone https://github.com/GonoBot/Gulps.git && cd Gulps && python main.py
```

---

### 💻 Desktop Installation (VS Code, Windows, Mac, Linux)

Because this project uses cross-platform Python syntax, you can open, edit, and run this repository directly inside **VS Code** or any desktop editor.

1. **Install Dependencies on your PC:**
   - Install [Python 3](https://python.org) on your computer.
   - Install [FFmpeg](https://ffmpeg.org) and ensure it is added to your system's Environmental Variables (PATH).
   - Open your desktop terminal and run:
     ```bash
     pip install --upgrade pip yt-dlp
     ```

2. **Clone and Run:**
   ```bash
   git clone https://github.com/GonoBot/Gulps.git
   cd Gulps
   python main.py
   ```

3. **Desktop Path Adjustment Note:**
   By default, the save paths in `core.py` and `image.py` are set to Android storage (`~/storage/downloads/...`). When running on a PC, simply edit the directory variables at the top of `core.py` to target your local user folder or a relative script directory:
   ```python
   # Example relative path for PC users:
   VIDEO_DIR = os.path.abspath("./downloads/Videos")
   AUDIO_DIR = os.path.abspath("./downloads/Audio")
   ```

---

### 🌐 Running as a Web App or Backend API

The core downloading logic located in `core.py` and `image.py` is entirely separated from the command-line interface loops. 

- **Web Frontend integration:** You can bypass `main.py` entirely and plug `core.py` straight into python web frameworks like **Streamlit**, **Anvil**, or **Flask**.
- **Backend API layout:** You can host this script on cloud platforms (such as Render or Hugging Face Spaces) to serve as a headless scraping engine that passes media assets directly to native iOS/Android client apps.



### Cloning & Running the Tool
Download this repository and launch the interface:

```bash
# Run the application interface
python main.py
```
