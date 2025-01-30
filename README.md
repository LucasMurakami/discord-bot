# Discord Music Bot

A feature-rich Discord music bot built with Python, discord.py, and yt-dlp for seamless music playback and playlist management.

## Features

- 🎵 Play audio from YouTube URLs and search queries
- 🔁 Repeat Mode (it repeats the same audio untill is set to off)
- 📊 Real-time queue management
- ⏭ Skip tracks and view current playback

## Installation

### Prerequisites

- Python 3.8+
- FFmpeg installed and added to system PATH
- Discord bot token

### Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/discord-music-bot.git
cd discord-music-bot
```

2. Create and use Virtual Environment

```bash
python -m venv env
source env/bin/activate  # Linux/MacOS
env\Scripts\activate  # Windows
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Create .env file

```bash
DISCORD_TOKEN=your_bot_token_here
```

5. Run the bot

```bash
python bot.py
```
