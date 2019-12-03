from flask import Flask, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_restful import Resource, Api, reqparse
from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import ModelSchema

app = Flask(__name__)
api = Api(app)
ma = Marshmallow(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Track.db'
app.config['FLASK_ADMIN_SWATCH'] = 'Yeti'
app.config['SECRET_KEY'] = "NoPasswordIsSafe"

db = SQLAlchemy(app)

Tracks_Producers_association = db.Table('producers',
    db.Column('producer_id', db.Integer, db.ForeignKey('producer.id'), primary_key=True),
    db.Column('track_id', db.Integer, db.ForeignKey('track.id'), primary_key=True)
)


class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True, nullable=False)
    genre_id = db.Column(db.Integer, db.ForeignKey('genre.id'), nullable=False)
    genre = db.relationship('Genre', backref=db.backref('track', lazy=True))
    cast = db.relationship('Producer', secondary=Tracks_Producers_association, lazy=True,
                         backref=db.backref('tracks', lazy=True))

    def __repr__(self):
        return self.title


class Genre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20),unique=True,nullable=False)

    def __repr__(self):
        return self.name


class Producer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100),unique=True,nullable=False)

    def __repr__(self):
        return self.name


# Flask marshmallow serializer
class TrackSchema(ModelSchema):
    class Meta:
        model = Track


db.create_all()


tracks_schema = TrackSchema(many=True)
track_schema = TrackSchema()


# Flask Admin
admin = Admin(app, name='Texas Production Alliance', template_mode='bootstrap3')
admin.add_view(ModelView(Track, db.session))
admin.add_view(ModelView(Genre, db.session))
admin.add_view(ModelView(Producer, db.session))


# Flask Restful
class OneTrack(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('track_id', type=int, required=True)
        self.args = parser.parse_args()

        track = Track.query.filter(Track.id == self.args['track_id']).first()
        if not track:
            return abort(404, 'Track with id: {} does not exist in database.'.format(self.args['Track_id']))

        return jsonify(Tracks=track_schema.dump(Track))

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('title', type=str, required=True),
        parser.add_argument('genre_id', type=int, required=True),
        parser.add_argument('cast_id', action='append', type=str)
        self.args = parser.parse_args()

        title = self.args['title']
        genre_id = self.args['genre_id']

        existing_track = Track.query.filter(Track.title == title).first()
        if existing_track:
            return abort(400, 'Track with title: {} already exists in database.'.format(self.args['title']))

        track = Track(
            title=title,
            genre_id=genre_id
        )

        if self.args['cast_id']:
            for id in self.args['cast_id']:
                Producer = Producer.query.filter(Producer.id == id).first()
                if not Producer:
                    return abort(404, 'Producer with id: {} does not exist in database.'.format(id))
                Track.cast.append(Producer)
                db.session.commit()

        try:
            db.session.add(Track)
            db.session.commit()
        except:
            return abort(500, 'An error occurred while trying to add new Track to database.')

        return jsonify(message='New Track has been created.')


class TrackList(Resource):

    def get(self):
        tracks = Track.query.all()

        return jsonify(track=tracks_schema.dump(tracks))


api.add_resource(OneTrack, '/track')
api.add_resource(TrackList, '/track/all')

if __name__=='__main__':
    app.run(debug=True)






