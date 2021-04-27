from playhouse.migrate import *
migrator = SqliteMigrator(db)
tagged_at_field = DateTimeField(default=datetime.datetime.now())
migrate(
    migrator.add_column('SongTag', 'tagged_at', tagged_at_field),
)

print('ok')