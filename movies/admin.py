"""Administration panel configuration for the movies catalogue."""

from django.contrib import admin
from django.db.models import Avg

from .models import Genre, Movie, Person, Rating

admin.site.site_header = 'Movies administration'
admin.site.site_title = 'Movies admin'
admin.site.index_title = 'Catalogue management'


class RatingInline(admin.TabularInline):
    """Ratings are edited as a block of rows inside the movie form."""

    model = Rating
    extra = 1
    fields = ['reviewer', 'score', 'comment']
    autocomplete_fields = []
    ordering = ['-score', 'reviewer']


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'year',
        'genres_list',
        'directors_list',
        'avg_score',
        'updated_at',
    ]
    list_filter = ['genres', 'year']
    search_fields = ['title', 'directors__name']
    list_editable = ['year']
    list_per_page = 10
    filter_horizontal = ['genres', 'directors']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [RatingInline]
    fieldsets = [
        ('Data', {'fields': ['title', 'year', 'summary', 'poster']}),
        ('Relations', {'fields': ['genres', 'directors']}),
        ('Audit', {'fields': ['created_at', 'updated_at'], 'classes': ['collapse']}),
    ]

    @admin.display(description='Genres', ordering='genres__name')
    def genres_list(self, obj):
        return ', '.join(genre.name for genre in obj.genres.all())

    @admin.display(description='Directors', ordering='directors__name')
    def directors_list(self, obj):
        return ', '.join(person.name for person in obj.directors.all())

    @admin.display(description='Average score', ordering='avg_score')
    def avg_score(self, obj):
        return obj.average_score() or '-'

    def get_queryset(self, request):
        # One extra join so the "Average score" column can be sorted.
        return super().get_queryset(request).annotate(avg_score=Avg('ratings__score'))


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'movie_count', 'description']
    search_fields = ['name', 'description']
    ordering = ['name']

    @admin.display(description='Movies')
    def movie_count(self, obj):
        return obj.movies.count()


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'birth_date', 'movie_count', 'updated_at']
    list_filter = ['role']
    search_fields = ['name', 'role', 'biography']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'birth_date'
    fieldsets = [
        ('Data', {'fields': ['name', 'role', 'birth_date', 'biography', 'photo']}),
        ('Audit', {'fields': ['created_at', 'updated_at'], 'classes': ['collapse']}),
    ]

    @admin.display(description='Movies')
    def movie_count(self, obj):
        return obj.movies.count()


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['movie', 'reviewer', 'score', 'comment_short', 'created_at']
    list_filter = ['score', 'movie']
    list_editable = ['score']
    search_fields = ['reviewer', 'movie__title', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['movie']
    date_hierarchy = 'created_at'
    list_per_page = 25

    @admin.display(description='Comment', ordering='comment')
    def comment_short(self, obj):
        return obj.comment[:60] + '...' if len(obj.comment) > 60 else obj.comment
