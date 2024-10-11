import os
import yt_dlp
import asyncio
from pyrogram import Client, filters

# Bot token from @BotFather
BOT_TOKEN = "bot_token"
API_ID = "123456"
API_HASH = "kalsjbda789q3g8oiubdgoaiufabhjfbjdsk"

# Pyrogram client setup
app = Client("yt-dlp-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Function to download song from YouTube
def download_song(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(f"ytsearch:{query}", download=True)
        if 'entries' in result:
            result = result['entries'][0]
        return ydl.prepare_filename(result).replace('.webm', '.mp3')

# Telegram command handler for /song
@app.on_message(filters.command("song", prefixes=['/', '!']) & (filters.private | filters.group))
async def song_handler(client, message):
    query = " ".join(message.command[1:])

    if not query:
        await message.reply_text("Please provide the song name after /song.")
        return

    fetching_message = await message.reply_text(f"Fetching song: {query} 🎧")

    try:
        # Call your download_song function
        song_file = download_song(query)
        uploading_message = await message.reply_text(f"Uploading {song_file}...")

        # Upload song to Telegram
        await message.reply_audio(audio=song_file)

        # Delete file after sending
        os.remove(song_file)

        # Delete the "Fetching..." and "Uploading..." messages
        await fetching_message.delete()
        await uploading_message.delete()

    except Exception as e:
        error_message = await message.reply_text(f"Failed to fetch song: {str(e)}")
        await error_message.delete()

if __name__ == "__main__":
    app.run()
