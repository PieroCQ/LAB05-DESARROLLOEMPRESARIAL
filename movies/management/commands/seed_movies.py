"""Load the sample data required by the lab.

Creates 4 genres, 8 people, 10 movies and ratings on 8 of them. The command
is idempotent: running it twice does not duplicate anything.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from movies.models import Genre, Movie, Person, Rating

GENRES = [
    ('Science fiction', 'Worlds built on speculative science or technology.'),
    ('Drama', 'Stories focused on characters and conflict.'),
    ('Thriller', 'Tension, suspense and revealing secrets.'),
    ('Animation', 'Hand drawn or computer generated animated features.'),
]

PEOPLE = [
    ('Denis Villeneuve', 'Director', '1967-10-03'),
    ('Christopher Nolan', 'Director', '1970-07-30'),
    ('Bong Joon-ho', 'Director', '1969-09-11'),
    ('Alfonso Cuaron', 'Director', '1961-11-28'),
    ('Hayao Miyazaki', 'Director', '1941-01-05'),
    ('Brad Pitt', 'Actor', '1963-12-18'),
    ('Florence Pugh', 'Actor', '1996-01-03'),
    ('Song Kang-ho', 'Actor', '1967-01-17'),
]

MOVIES = [
    {
        'title': 'Arrival',
        'year': 2016,
        'genres': ['Science fiction', 'Drama'],
        'directors': ['Denis Villeneuve'],
        'summary': 'A linguist works with the military to communicate with visitors.',
        'ratings': [('Ana Ruiz', 9, 'Slow and dense, worth it.'), ('Luis Vega', 8, '')],
    },
    {
        'title': 'Blade Runner 2049',
        'year': 2017,
        'genres': ['Science fiction', 'Thriller'],
        'directors': ['Denis Villeneuve'],
        'summary': 'A young blade runner uncovers a secret capable of toppling society.',
        'ratings': [('Ana Ruiz', 9, 'Best visuals of the decade.'), ('Carlos Diaz', 7, 'Slow ending.')],
    },
    {
        'title': 'Dune',
        'year': 2021,
        'genres': ['Science fiction', 'Drama'],
        'directors': ['Denis Villeneuve'],
        'summary': 'A noble family becomes embroiled in a war for a desert planet.',
        'ratings': [('Maria Lopez', 8, ''), ('Carlos Diaz', 9, 'Impressive scale.')],
    },
    {
        'title': 'Inception',
        'year': 2010,
        'genres': ['Science fiction', 'Thriller'],
        'directors': ['Christopher Nolan'],
        'summary': 'A thief steals secrets from inside dreams.',
        'ratings': [('Luis Vega', 10, 'Masterpiece.'), ('Maria Lopez', 9, 'Complex but rewarding.')],
    },
    {
        'title': 'Interstellar',
        'year': 2014,
        'genres': ['Science fiction', 'Drama'],
        'directors': ['Christopher Nolan'],
        'summary': 'Explorers travel through a wormhole looking for a new home.',
        'ratings': [('Ana Ruiz', 9, ''), ('Luis Vega', 9, 'The music carries it.')],
    },
    {
        'title': 'Parasite',
        'year': 2019,
        'genres': ['Drama', 'Thriller'],
        'directors': ['Bong Joon-ho'],
        'summary': 'A poor family infiltrates the household of a wealthy one.',
        'ratings': [('Maria Lopez', 10, 'Perfect script.'), ('Carlos Diaz', 8, '')],
    },
    {
        'title': 'Roma',
        'year': 2018,
        'genres': ['Drama'],
        'directors': ['Alfonso Cuaron'],
        'summary': 'A year in the life of a live-in maid for a middle class family.',
        'ratings': [('Ana Ruiz', 8, 'Black and white works.')],
    },
    {
        'title': 'Harry Potter and the Prisoner of Azkaban',
        'year': 2004,
        'genres': ['Drama', 'Thriller'],
        'directors': ['Alfonso Cuaron'],
        'summary': 'Harry learns about his past and the threat that follows him.',
        'ratings': [('Luis Vega', 8, '')],
    },
    {
        'title': 'Spirited Away',
        'year': 2001,
        'genres': ['Animation', 'Drama'],
        'directors': ['Hayao Miyazaki'],
        'summary': 'A girl wanders into a world of spirits and must work to free her parents.',
        'ratings': [('Maria Lopez', 10, ''), ('Ana Ruiz', 9, 'Perfect for every age.')],
    },
    {
        'title': 'My Neighbor Totoro',
        'year': 1988,
        'genres': ['Animation', 'Drama'],
        'directors': ['Hayao Miyazaki'],
        'summary': 'Two sisters move to the countryside and meet forest spirits.',
        'ratings': [('Carlos Diaz', 9, 'Quiet and lovely.')],
    },
]


class Command(BaseCommand):
    help = 'Load the sample genres, people, movies and ratings of the lab.'

    @transaction.atomic
    def handle(self, *args, **options):
        genres = {}
        for name, description in GENRES:
            genre, _ = Genre.objects.get_or_create(
                name=name, defaults={'description': description}
            )
            genres[name] = genre

        people = {}
        for name, role, birth_date in PEOPLE:
            person, _ = Person.objects.get_or_create(
                name=name, defaults={'role': role, 'birth_date': birth_date}
            )
            people[name] = person

        movies = 0
        ratings = 0
        for data in MOVIES:
            movie, _ = Movie.objects.get_or_create(
                title=data['title'],
                year=data['year'],
                defaults={'summary': data['summary']},
            )
            movie.genres.set(genres[name] for name in data['genres'])
            movie.directors.set(people[name] for name in data['directors'])
            movies += 1

            for reviewer, score, comment in data['ratings']:
                _, created = Rating.objects.get_or_create(
                    movie=movie,
                    reviewer=reviewer,
                    defaults={'score': score, 'comment': comment},
                )
                ratings += int(created)

        self.stdout.write(
            self.style.SUCCESS(
                f'Genres: {Genre.objects.count()} | '
                f'Personas: {Person.objects.count()} | '
                f'Peliculas: {Movie.objects.count()} | '
                f'Valoraciones: {Rating.objects.count()} '
                f'({ratings} creadas en esta ejecucion)'
            )
        )
