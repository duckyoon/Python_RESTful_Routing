from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
from dotenv import load_dotenv
import os
import requests

load_dotenv()
TOKEN_AUTH = os.getenv("TOKEN_AUTH")
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/original"

movie_url = "https://api.themoviedb.org/3/search/movie"


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

# CREATE DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///new_movie.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# CREATE TABLE
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)
    def __repr__(self):
        return f'<movie {self.title}>' 

# create wtform
class RateMovieForm(FlaskForm):
    rating = StringField('Your Rating Out of 10 e.g. 7.5 ', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Submit')
    
class addMovieForm(FlaskForm):
    title = StringField('Movie Title ', validators=[DataRequired()])
    submit = SubmitField('Add Movie')

# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
# with app.app_context():
#     db.create_all()
#     db.session.add(new_movie)
#     db.session.commit()

all_movies = []

@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()
    
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    
    return render_template("index.html", data=all_movies)

@app.route("/edit", methods=["GET", "POST"])
def rate_movie():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = Movie().query.get(movie_id)
    
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    
    return render_template('edit.html', movie=movie, form=form)

@app.route("/delete")
def delete_movie():
    movie_id = request.args.get("id")
    movie = Movie().query.get(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = addMovieForm()
    if form.validate_on_submit():
        movie_title = form.title.data
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {TOKEN_AUTH}",
        }
        params = {
            "query" : movie_title,
        }
        response = requests.get(movie_url, headers=headers, params=params)
        data = response.json()["results"]
        return render_template('select.html', data=data)
        
    return render_template('add.html', form=form)

@app.route('/find')
def movie_detail():
    movie_id = request.args.get("id")
    if movie_id:
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {TOKEN_AUTH}",
        }
        url = "https://api.themoviedb.org/3/movie"
        response = requests.get(url=f"{url}/{movie_id}", headers=headers)
        print(response.status_code)
        data = response.json()
        new_movie = Movie(
            title=data["title"],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            year=data["release_date"].split('-')[0],
            description=data["overview"],
            rating=None, 
            ranking=None,  
            review=None,
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('home'))
    
if __name__ == '__main__':
    app.run(debug=True)
