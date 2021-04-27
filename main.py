import datetime
import spotipy
import dotenv
from peewee import *
from spotipy.oauth2 import SpotifyOAuth

dotenv.load_dotenv()

auth_manager = SpotifyOAuth(scope='user-read-currently-playing', redirect_uri='http://localhost:8080/callback')
sp = spotipy.Spotify(auth_manager=auth_manager)

db = SqliteDatabase('tags.db')
db.connect()

class Tag(Model):
    name = CharField()

    class Meta:
        database = db

class Song(Model):
    uid     = CharField(unique=True)
    name    = CharField()
    artists = CharField()
    album   = CharField()

    class Meta:
        database = db

class SongTag(Model):
    song = ForeignKeyField(Song, backref='tags')
    tag  = ForeignKeyField(Tag, backref='songs')
    tagged_at = DateTimeField()
    
    class Meta:
        database = db
        indexes = (
            (('song', 'tag'), True),
        )

data = sp.current_user_playing_track()['item']

song_name = data['name']
song_artists = ", ".join([artist['name'] for artist in data['artists']])
song_album = data['album']['name']
song_uid = data['id']

db_song, _ = Song.get_or_create(uid=song_uid, name=song_name, artists=song_artists, album=song_album)
tags = SongTag.select().join(Tag).where(SongTag.song == db_song)

print(f"Currently playing: {song_name} - {song_artists}")
print(f"Tags: {[song_tag.tag.name for song_tag in tags]}")
print()
print("What do you want to do (add/delete/list)?")
choice = input("Enter your choice: ").strip()

if choice in ["add", "a"]:
  add_tags = input("Enter comma separated list of tags: ").strip().split(',')

  for tag in add_tags:
    db_tag, _ = Tag.get_or_create(name=tag)
    SongTag.get_or_create(song_id=db_song.id, tag_id=db_tag.id, defaults={'tagged_at': datetime.datetime.now()})

elif choice in ["delete", "del", "d"]:
  remove_tags = input("Enter comma separated list of tags: ").strip().split(',')

  for tag in remove_tags:
    db_tag = Tag.get(name=tag)
    SongTag.get((SongTag.song == db_song) & (SongTag.tag == db_tag)).delete_instance()
elif choice in ["list", "l"]:
  all_tags  = SongTag.select()
  for tag in all_tags:
    print(f"{tag.song.name} tagged as '#{tag.tag.name}' on {tag.tagged_at}")

new_tags = SongTag.select().join(Tag).where(SongTag.song == db_song)
print(f"Tags: {[song_tag.tag.name for song_tag in new_tags]}")