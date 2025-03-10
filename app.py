import os
from flask import Flask, render_template, send_from_directory
from pymongo import MongoClient

app = Flask(__name__)
MONGODB_URI = os.environ.get("MONGODB_URI")

# Setup MongoDB connection
client = MongoClient(MONGODB_URI)
db = client['movie_db']
movies_collection = db['movies']

def get_movies():
    movies = movies_collection.find()
    movies_list = []
    for movie in movies:
        movies_list.append({
            'id': str(movie['_id']),
            'file_path': movie['file_path'],
            'poster_path': movie['poster_path'],
            'title': movie['title']
        })
    return movies_list

@app.route('/')
def index():
    movies = get_movies()
    return render_template('index.html', movies=movies)

@app.route('/movie/<movie_id>')
def movie_page(movie_id):
    from bson import ObjectId
    movie = movies_collection.find_one({"_id": ObjectId(movie_id)})
    if movie:
        movie_data = {
            'id': str(movie['_id']),
            'file_path': movie['file_path'],
            'poster_path': movie['poster_path'],
            'title': movie['title']
        }
        return render_template('movie.html', movie=movie_data)
    else:
        return "Movie not found", 404

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
