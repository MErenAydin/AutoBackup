# AutoBackup

A lightweight **real-time folder backup tool** written in Python.
Originally developed to automatically back up **Don't Starve Together** server clusters.  
It automatically detects file changes and creates versioned backups, optionally as ZIP archives.

---

## Features

- Real-time monitoring using [`watchdog`](https://pypi.org/project/watchdog/)
- Automatic ZIP or folder copy backups
- Auto cleanup of old backups (configurable buffer)
- Adjustable cooldown to prevent multiple saves in quick succession
- Simple command-line interface

---

## Installation

```bash
git clone https://github.com/MErenAydin/AutoBackup.git
cd AutoBackup
pip install -r requirements.txt
```
---

## Usage

Run the script with Python:

```bash
python AutoBackup.py --source-path "C:\path\to\your\source" --backup-path "C:\path\to\your\destination" --buffer-size 30 --cooldown 120 --zip
