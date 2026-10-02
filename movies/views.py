"""Public views of the movies catalogue.

The admin panel edits records; anything that needs to compute, aggregate or
rank movies needs a view of its own. The recommendation view is the example
required by the lab.
"""

from django.db.models import Avg
from django.shortcuts import get_object_or_404, render

from .models import Genre, Movie


def recommendation_list(request):
    """List the best rated movies of every genre.

    Genres are ranked by the mean score of their movies, so the page answers
    the question "what should I watch tonight?" without manual ordering.
    """
    genres = (
        Genre.objects.annotate(average_score=Avg('movies__ratings__score'))
        .filter(average_score__isnull=False)
        .order_by('-average_score', 'name')
    )

    recommendations = [
        {
            'genre': genre,
            'movies': list(
                Movie.objects.filter(genres=genre)
                .annotate(score=Avg('ratings__score'))
                .filter(score__isnull=False)
                .order_by('-score', 'title')[:3]
            ),
        }
        for genre in genres
    ]

    return render(
        request,
        'movies/recommendation_list.html',
        {'recommendations': recommendations},
    )


def movie_detail(request, pk):
    """Show a movie with its ratings and same-genre recommendations."""
    movie = get_object_or_404(
        Movie.objects.prefetch_related('genres', 'directors', 'ratings'),
        pk=pk,
    )
    return render(
        request,
        'movies/movie_detail.html',
        {
            'movie': movie,
            'average_score': movie.average_score(),
            'recommendations': movie.best_movies_of_same_genre(),
        },
    )
