import os
import subprocess
from telegram.ext import Updater, MessageHandler, Filters
from telegram import Update
from telegram.ext import CallbackContext
from pymongo import MongoClient

# Environment variables
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
MONGODB_URI = os.environ.get("MONGODB_URI")
TARGET_CHANNEL_ID = int(os.environ.get("TARGET_CHANNEL_ID", 0))  # Channel ID as integer

# Directories for storing movies and posters
MOVIE_DIR = "static/movies"
POSTER_DIR = "static/posters"

os.makedirs(MOVIE_DIR, exist_ok=True)
os.makedirs(POSTER_DIR, exist_ok=True)

# Setup MongoDB connection
client = MongoClient(MONGODB_URI)
db = client['movie_db']         # Database name (can be changed)
movies_collection = db['movies']  # Collection name

def process_video(file_path, poster_path):
    """Extract a screenshot from the video at 10 seconds."""
    command = [
        "ffmpeg",
        "-y",  # Overwrite if the output file exists
        "-i", file_path,
        "-ss", "00:00:10",
        "-vframes", "1",
        poster_path
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def save_movie(file_path, poster_path, title):
    """Insert movie metadata into MongoDB."""
    movie_doc = {
        "file_path": file_path,
        "poster_path": poster_path,
        "title": title
    }
    movies_collection.insert_one(movie_doc)

def handle_message(update: Update, context: CallbackContext):
    message = update.effective_message

    # Only process messages from the target channel
    if update.effective_chat.id != TARGET_CHANNEL_ID:
        return

    file_obj = None
    # Process both document and video types
    if message.document:
        file_obj = message.document
    elif message.video:
        file_obj = message.video

    if file_obj:
        file_id = file_obj.file_id
        new_file = context.bot.getFile(file_id)
        file_name = file_obj.file_name if hasattr(file_obj, "file_name") else f"{file_id}.mp4"
        file_path_local = os.path.join(MOVIE_DIR, file_name)
        new_file.download(custom_path=file_path_local)

        # Create a poster file name based on the video file name
        poster_name = os.path.splitext(file_name)[0] + ".png"
        poster_path_local = os.path.join(POSTER_DIR, poster_name)

        # Extract a screenshot from the movie
        process_video(file_path_local, poster_path_local)

        # Save movie details into MongoDB
        title = os.path.splitext(file_name)[0]
        save_movie(file_path_local, poster_path_local, title)

        update.message.reply_text("Movie received and processed!")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Listen for messages from channels and filter for documents/videos
    dp.add_handler(MessageHandler(Filters.chat_type.channel, handle_message))
    dp.add_handler(MessageHandler(Filters.document | Filters.video, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
