import os
import yt_dlp
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import MessageNotModified
import sys

# Bot token from @BotFather
BOT_TOKEN = "BOT_TOKEN"
API_ID = "API_ID"
API_HASH = "API_HASH"

# Pyrogram client setup
app = Client("yt-dlp-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Global fetching_message to access it in hooks
fetching_message = None

# Hook function for yt-dlp to track download progress
def download_progress_hook(d):
    if d['status'] == 'downloading':
        downloaded = d.get('downloaded_bytes', 0)
        total = d.get('total_bytes', 1)
        progress = int(downloaded / total * 100)

        # Real-time console log with overwriting the same line
        sys.stdout.write(f"\r[Downloading] {progress}% complete ({downloaded / 1024 / 1024:.2f} MB of {total / 1024 / 1024:.2f} MB)")
        sys.stdout.flush()

        if fetching_message and progress % 10 == 0:  # Only update every 10% progress
            loop = asyncio.get_event_loop()
            asyncio.run_coroutine_threadsafe(update_message_progress(progress), loop)

    elif d['status'] == 'finished':
        print("\n[Download Complete] Download finished, converting the file...")  # New line after progress is done

        if fetching_message:
            loop = asyncio.get_event_loop()
            asyncio.run_coroutine_threadsafe(fetching_message.edit_text("Finished downloading, now converting..."), loop)

# Async function to update Telegram message with progress
async def update_message_progress(progress):
    try:
        await fetching_message.edit_text(f"Downloading... {progress}%")
    except MessageNotModified:
        pass

# Function to download and convert song from YouTube
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
        'progress_hooks': [download_progress_hook],  # Hook for download progress
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(f"ytsearch:{query}", download=True)
        if 'entries' in result:
            result = result['entries'][0]
        return ydl.prepare_filename(result).replace('.webm', '.mp3')

# Upload progress tracking
async def upload_progress(current, total, message: Message):
    progress = int(current / total * 100)

    if progress % 10 == 0:  # Only update every 10% progress
        # Real-time console log with overwriting the same line
        sys.stdout.write(f"\r[Uploading] {progress}% complete ({current / 1024 / 1024:.2f} MB of {total / 1024 / 1024:.2f} MB)")
        sys.stdout.flush()

        try:
            await message.edit_text(f"Uploading... {progress}%")
        except MessageNotModified:
            pass

# Telegram command handler for /song
@app.on_message(filters.command("song", prefixes=['/', '!']) & (filters.private | filters.group))
async def song_handler(client, message):
    global fetching_message  # Use the global message object

    query = " ".join(message.command[1:])

    if not query:
        await message.reply_text("Please provide the song name after /song.")
        return

    # Update the message immediately to reflect the search status
    fetching_message = await message.reply_text(f"Searching for song: {query} 🎧")

    try:
        # Print status in console
        print(f"Searching for song: {query}")

        # Call download_song function
        song_file = download_song(query)

        if song_file:
            # Update Telegram message after song is found
            await fetching_message.edit_text(f"Song found! 🎶\nDownloading song: {query}...")
        else:
            await fetching_message.edit_text(f"Song not found: {query}")
            return

        # Print to console when download finishes
        print(f"\n[Download Complete] File downloaded: {song_file}")

        # Update Telegram message after download finishes
        await fetching_message.edit_text("Finished downloading, now converting...")

        # Delay added to simulate conversion progress
        await asyncio.sleep(2)  # Simulate short delay for conversion if needed

        # Update Telegram message to indicate conversion is done
        await fetching_message.edit_text("Finished conversion, uploading...")

        uploading_message = await message.reply_text(f"Uploading {song_file}...")

        # Print status to console
        print(f"Uploading {song_file} to Telegram...")

        # Upload song to Telegram with progress
        await client.send_audio(
            chat_id=message.chat.id,
            audio=song_file,
            progress=upload_progress,
            progress_args=(uploading_message,)
        )

        # Print status when upload completes
        print("\n[Upload Complete] File successfully uploaded to Telegram.")

        # Delete file after sending
        os.remove(song_file)

        # Print status to console
        print(f"[Cleanup] Deleted file {song_file} from disk.")

        # Delete Telegram progress messages
        await fetching_message.delete()
        await uploading_message.delete()

    except Exception as e:
        await fetching_message.edit_text(f"Failed to fetch song: {str(e)}")
        print(f"[Error] Failed to fetch song: {str(e)}")

if __name__ == "__main__":
    print("[Bot Started] Running yt-dlp bot...")
    app.run()
