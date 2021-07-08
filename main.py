import datetime
import spotipy
import dotenv
import sys

from peewee import *
from tabulate import tabulate
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
sp_data = sp.current_user_playing_track()

if sp_data:
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

choice = ""

if len(sys.argv) == 2:
  choice = sys.argv[1].strip()
else:
  print("What do you want to do (add/delete/list-songs/list-tags/query)?")
  choice = input("Enter your choice: ").strip()

if choice in ["add", "a"]:
  add_tags = input("Enter comma separated list of tags: ").strip().split(',')

  for tag in add_tags:
    db_tag, _ = Tag.get_or_create(name=tag.strip())
    SongTag.get_or_create(song_id=db_song.id, tag_id=db_tag.id, defaults={'tagged_at': datetime.datetime.now()})

elif choice in ["delete", "del", "d"]:
  remove_tags = input("Enter comma separated list of tags: ").strip().split(',')

  for tag in remove_tags:
    db_tag = Tag.get(name=tag.strip())
    SongTag.get((SongTag.song == db_song) & (SongTag.tag == db_tag)).delete_instance()
elif choice in ["list-songs", "ls"]:
  all_tags  = SongTag.select()
  for tag in all_tags:
    print(f"{tag.song.name} tagged as '#{tag.tag.name}' on {tag.tagged_at}")
elif choice in ["list-tags", "lt"]:
  all_tags  = Tag.select(Tag, fn.Count(SongTag.id).alias('count')).join(SongTag, JOIN.LEFT_OUTER).group_by(Tag).order_by(SQL('count').desc())
  tag_data  = [[tag.name, tag.count] for tag in all_tags]
  print()
  print(tabulate(tag_data, headers=["Name", "Count"]))

  for tag in all_tags:
    if tag.count == 0:
      tag.delete_instance()
elif choice in ["query", "q"]:
  query = input("Enter query: ").strip()
  
  tag = Tag.get(name=query)
  song_tags = SongTag.select().where(SongTag.tag == tag)
  print()
  
  for song_tag in song_tags:
    song = song_tag.song
    print(f"{song.name} - {song.artists}")

if choice in ["add", "a", "delete", "del", "d"]:
  new_tags = SongTag.select().join(Tag).where(SongTag.song == db_song)
  print(f"Tags: {[song_tag.tag.name for song_tag in new_tags]}")