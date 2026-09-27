"""Data model of the movies catalogue."""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg

SCORE_VALIDATORS = [
    MinValueValidator(settings.RATING_MIN_SCORE),
    MaxValueValidator(settings.RATING_MAX_SCORE),
]


class Genre(models.Model):
    """A genre used to group movies in the catalogue."""

    name = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Genre'
        verbose_name_plural = 'Genres'

    def __str__(self):
        return self.name


class Person(models.Model):
    """Someone involved in a movie, usually a director."""

    name = models.CharField(max_length=150)
    role = models.CharField(max_length=80, default='Director')
    birth_date = models.DateField(null=True, blank=True)
    biography = models.TextField(blank=True)
    photo = models.ImageField(upload_to='people/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Person'
        verbose_name_plural = 'People'

    def __str__(self):
        return self.name


class Movie(models.Model):
    """A movie of the catalogue, related to genres and directors."""

    title = models.CharField(max_length=200)
    year = models.PositiveIntegerField()
    summary = models.TextField(blank=True)
    poster = models.ImageField(upload_to='posters/', blank=True)
    genres = models.ManyToManyField(
        Genre,
        related_name='movies',
        blank=True,
        verbose_name='Genres',
    )
    directors = models.ManyToManyField(
        Person,
        related_name='movies',
        blank=True,
        verbose_name='Directors',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        verbose_name = 'Movie'
        verbose_name_plural = 'Movies'

    def __str__(self):
        return f'{self.title} ({self.year})'

    def average_score(self):
        """Return the mean of the ratings, or None when there are none."""
        average = self.ratings.aggregate(value=Avg('score'))['value']
        return round(average, 2) if average is not None else None

    def best_movies_of_same_genre(self, limit=5):
        """Return the best rated movies sharing at least one genre.

        This is the logic behind the public recommendation view. The admin
        panel cannot compute it: it only lists and edits records.
        """
        genre_ids = self.genres.values_list('id', flat=True)
        peers = (
            Movie.objects.filter(genres__in=genre_ids)
            .exclude(pk=self.pk)
            .annotate(score=Avg('ratings__score'))
            .filter(score__isnull=False)
            .order_by('-score', 'title')
            .distinct()[:limit]
        )
        return peers


class Rating(models.Model):
    """A score given by a reviewer to a movie."""

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name='ratings',
    )
    reviewer = models.CharField(max_length=120)
    score = models.PositiveSmallIntegerField(validators=SCORE_VALIDATORS)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-score', 'reviewer']
        verbose_name = 'Rating'
        verbose_name_plural = 'Ratings'
        constraints = [
            models.UniqueConstraint(
                fields=['movie', 'reviewer'],
                name='unique_rating_per_reviewer',
            ),
        ]

    def __str__(self):
        return f'{self.movie.title} - {self.score}/10 by {self.reviewer}'
