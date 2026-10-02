"""Tests for the movies administration panel and the public views."""

from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.db.models import Count
from django.test import TestCase
from django.urls import reverse

from .models import Genre, Movie, Person, Rating


def make_movie(title, year=2020, genres=(), directors=(), ratings=()):
    """Create a movie with its relations and ratings in one call."""
    movie = Movie.objects.create(title=title, year=year)
    movie.genres.set(genres)
    movie.directors.set(directors)
    for reviewer, score in ratings:
        Rating.objects.create(movie=movie, reviewer=reviewer, score=score)
    return movie


class ModelTests(TestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name='Science fiction')
        self.other_genre = Genre.objects.create(name='Drama')
        self.director = Person.objects.create(name='Denis Villeneuve')

    def test_str_of_each_model(self):
        movie = make_movie('Arrival', 2016, [self.genre], [self.director])
        rating = Rating.objects.create(movie=movie, reviewer='Ana', score=9)

        self.assertEqual(str(self.genre), 'Science fiction')
        self.assertEqual(str(self.director), 'Denis Villeneuve')
        self.assertEqual(str(movie), 'Arrival (2016)')
        self.assertEqual(str(rating), 'Arrival - 9/10 by Ana')

    def test_movie_uses_many_to_many_for_genres(self):
        first = make_movie('Arrival', 2016, [self.genre, self.other_genre])
        second = make_movie('Dune', 2021, [self.genre])

        self.assertEqual(first.genres.count(), 2)
        self.assertEqual(list(self.genre.movies.all()), [first, second])

    def test_rating_belongs_to_a_movie_and_is_deleted_with_it(self):
        movie = make_movie('Arrival', 2016, ratings=[('Ana', 9)])
        self.assertEqual(Rating.objects.count(), 1)

        movie.delete()

        self.assertEqual(Rating.objects.count(), 0)

    def test_average_score(self):
        movie = make_movie('Arrival', 2016, ratings=[('Ana', 9), ('Luis', 8)])

        self.assertEqual(movie.average_score(), 8.5)
        self.assertIsNone(make_movie('Dune', 2021).average_score())

    def test_best_movies_of_same_genre_excludes_itself_and_orders_by_score(self):
        weak = make_movie('Alien', 1979, [self.other_genre], ratings=[('Ana', 3)])
        best = make_movie('Dune', 2021, [self.genre], ratings=[('Ana', 10)])
        middle = make_movie('Arrival', 2016, [self.genre], ratings=[('Ana', 8)])
        movie = make_movie('Interstellar', 2014, [self.genre], ratings=[('Ana', 7)])
        unrated = make_movie('Solaris', 1972, [self.genre])

        result = list(movie.best_movies_of_same_genre())

        self.assertEqual(result, [best, middle])
        self.assertNotIn(movie, result)
        self.assertNotIn(weak, result)
        self.assertNotIn(unrated, result)

    def test_score_out_of_range_is_rejected(self):
        movie = make_movie('Arrival', 2016)
        rating = Rating(movie=movie, reviewer='Ana', score=11)

        with self.assertRaises(Exception):
            rating.full_clean()

    def test_one_rating_per_reviewer_and_movie(self):
        movie = make_movie('Arrival', 2016, ratings=[('Ana', 9)])

        with self.assertRaises(Exception):
            Rating.objects.create(movie=movie, reviewer='Ana', score=5)


class AdminRegistrationTests(TestCase):
    def test_the_four_models_are_registered(self):
        from django.contrib import admin

        from .admin import GenreAdmin, MovieAdmin, PersonAdmin, RatingAdmin

        self.assertIsInstance(admin.site._registry[Movie], MovieAdmin)
        self.assertIsInstance(admin.site._registry[Genre], GenreAdmin)
        self.assertIsInstance(admin.site._registry[Person], PersonAdmin)
        self.assertIsInstance(admin.site._registry[Rating], RatingAdmin)

    def test_movie_admin_customisation(self):
        from django.contrib import admin

        from .admin import MovieAdmin

        movie_admin = admin.site._registry[Movie]
        self.assertIsInstance(movie_admin, MovieAdmin)
        self.assertIn('title', MovieAdmin.list_display)
        self.assertIn('year', MovieAdmin.list_filter)
        self.assertIn('genres', MovieAdmin.list_filter)
        self.assertIn('title', MovieAdmin.search_fields)
        self.assertIn('directors__name', MovieAdmin.search_fields)
        self.assertEqual(MovieAdmin.readonly_fields, ['created_at', 'updated_at'])
        self.assertEqual([inline.__name__ for inline in MovieAdmin.inlines], ['RatingInline'])

    def test_rating_inline_is_tabular_and_editable(self):
        from .admin import RatingInline

        self.assertEqual(RatingInline.model, Rating)
        self.assertIn('score', RatingInline.fields)


class AdminPanelTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.admin = self.user_model.objects.create_superuser(
            username='root', email='root@example.com', password='lab-pass-1'
        )
        self.client.force_login(self.admin)

    def test_admin_index_lists_every_model(self):
        response = self.client.get(reverse('admin:index'))

        self.assertEqual(response.status_code, 200)
        for label in ['Movies', 'Genres', 'People', 'Ratings']:
            self.assertContains(response, label)

    def test_four_crud_operations_work_without_writing_a_view(self):
        genre = Genre.objects.create(name='Science fiction')
        person = Person.objects.create(name='Denis Villeneuve')
        movie = make_movie('Arrival', 2016, [genre], [person])

        add = self.client.post(
            reverse('admin:movies_movie_add'),
            {
                'title': 'Dune',
                'year': '2021',
                'summary': 'A desert planet.',
                'genres': [str(genre.pk)],
                'directors': [str(person.pk)],
                'ratings-TOTAL_FORMS': '0',
                'ratings-INITIAL_FORMS': '0',
            },
        )
        self.assertEqual(add.status_code, 302)
        self.assertTrue(Movie.objects.filter(title='Dune').exists())

        change = self.client.post(
            reverse('admin:movies_movie_change', args=[movie.pk]),
            {
                'title': 'Arrival (2016)',
                'year': '2016',
                'summary': '',
                'genres': [str(genre.pk)],
                'directors': [str(person.pk)],
                'ratings-TOTAL_FORMS': '0',
                'ratings-INITIAL_FORMS': '0',
            },
        )
        self.assertEqual(change.status_code, 302)
        movie.refresh_from_db()
        self.assertEqual(movie.title, 'Arrival (2016)')

        rating = Rating.objects.create(movie=movie, reviewer='Ana', score=9)
        self.assertTrue(
            self.client.post(
                reverse('admin:movies_rating_change', args=[rating.pk]),
                {'movie': str(movie.pk), 'reviewer': 'Ana', 'score': '7', 'comment': ''},
            ).status_code
            == 302
        )
        rating.refresh_from_db()
        self.assertEqual(rating.score, 7)

        self.assertTrue(
            self.client.post(
                reverse('admin:movies_rating_delete', args=[rating.pk]),
                {'post': 'yes'},
            ).status_code
            == 302
        )
        self.assertFalse(Rating.objects.filter(pk=rating.pk).exists())

    def test_ratings_are_created_from_the_movie_form(self):
        genre = Genre.objects.create(name='Drama')
        movie = make_movie('Roma', 2018, [genre])

        response = self.client.post(
            reverse('admin:movies_movie_change', args=[movie.pk]),
            {
                'title': 'Roma',
                'year': '2018',
                'summary': '',
                'genres': [str(genre.pk)],
                'directors': [],
                'ratings-TOTAL_FORMS': '2',
                'ratings-INITIAL_FORMS': '0',
                'ratings-0-reviewer': 'Ana',
                'ratings-0-score': '8',
                'ratings-0-comment': 'Nice.',
                'ratings-1-reviewer': 'Luis',
                'ratings-1-score': '9',
                'ratings-1-comment': '',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(movie.ratings.count(), 2)

    def test_audit_fields_are_not_writable(self):
        from django.contrib import admin

        from .admin import MovieAdmin

        genre = Genre.objects.create(name='Drama')
        movie = make_movie('Roma', 2018, [genre])

        movie_admin = admin.site._registry[Movie]
        self.assertEqual(MovieAdmin.readonly_fields, ['created_at', 'updated_at'])
        # Readonly fields are rendered from the record, never posted back.
        form_class = movie_admin.get_form(self._request())
        self.assertNotIn('created_at', form_class.base_fields)
        self.assertNotIn('updated_at', form_class.base_fields)

        response = self.client.get(reverse('admin:movies_movie_change', args=[movie.pk]))
        form = response.context['adminform'].form
        self.assertNotIn('created_at', form.fields)

        self.assertIsNotNone(movie.created_at)
        self.assertIsNotNone(movie.updated_at)

    def _request(self):
        from django.test import RequestFactory

        request = RequestFactory().get('/admin/')
        request.user = self.admin
        return request

    def test_posting_the_form_does_not_change_the_audit_dates(self):
        genre = Genre.objects.create(name='Drama')
        movie = make_movie('Roma', 2018, [genre])
        created_at = movie.created_at

        self.client.post(
            reverse('admin:movies_movie_change', args=[movie.pk]),
            {
                'title': 'Roma (2018)',
                'year': '2018',
                'summary': '',
                'genres': [str(genre.pk)],
                'directors': [],
                'created_at': '2000-01-01 00:00:00',
                'updated_at': '2000-01-01 00:00:00',
                'ratings-TOTAL_FORMS': '0',
                'ratings-INITIAL_FORMS': '0',
            },
        )

        movie.refresh_from_db()
        self.assertEqual(movie.title, 'Roma (2018)')
        self.assertEqual(movie.created_at, created_at)

    def test_movie_list_shows_average_and_filters(self):
        genre = Genre.objects.create(name='Drama')
        other = Genre.objects.create(name='Animation')
        make_movie('Roma', 2018, [genre], ratings=[('Ana', 8), ('Luis', 10)])
        make_movie('Totoro', 1988, [other], ratings=[('Ana', 9)])

        changelist = self.client.get(
            reverse('admin:movies_movie_changelist'),
            {'q': 'rom', 'genres__id__exact': str(genre.pk)},
        )

        self.assertEqual(changelist.status_code, 200)
        results = changelist.context['cl'].result_list
        self.assertEqual([movie.title for movie in results], ['Roma'])

    def test_search_finds_a_movie_by_director_name(self):
        genre = Genre.objects.create(name='Drama')
        director = Person.objects.create(name='Alfonso Cuaron')
        make_movie('Roma', 2018, [genre], [director])

        results = self.client.get(
            reverse('admin:movies_movie_changelist'), {'q': 'cuaron'}
        ).context['cl'].result_list

        self.assertEqual([movie.title for movie in results], ['Roma'])


class EditorGroupTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.group = Group.objects.create(name='editores')
        self.group.permissions.add(
            Permission.objects.get(codename='add_movie', content_type__app_label='movies'),
            Permission.objects.get(codename='change_movie', content_type__app_label='movies'),
            Permission.objects.get(codename='view_movie', content_type__app_label='movies'),
            Permission.objects.get(codename='add_rating', content_type__app_label='movies'),
            Permission.objects.get(codename='change_rating', content_type__app_label='movies'),
            Permission.objects.get(codename='view_rating', content_type__app_label='movies'),
            Permission.objects.get(codename='view_genre', content_type__app_label='movies'),
            Permission.objects.get(codename='view_person', content_type__app_label='movies'),
        )
        self.editor = self.user_model.objects.create_user(
            username='editor', password='lab-pass-2', is_staff=True
        )
        self.editor.groups.add(self.group)
        self.admin = self.user_model.objects.create_superuser(
            username='root', email='root@example.com', password='lab-pass-1'
        )
        self.client.force_login(self.editor)

    def _request(self, user=None):
        from django.test import RequestFactory

        request = RequestFactory().get('/admin/')
        request.user = user or self.editor
        return request

    def test_editor_can_add_and_change_but_not_delete_a_movie(self):
        genre = Genre.objects.create(name='Drama')
        movie = make_movie('Roma', 2018, [genre])

        self.assertTrue(self.editor.has_perm('movies.add_movie'))
        self.assertTrue(self.editor.has_perm('movies.change_movie'))
        self.assertFalse(self.editor.has_perm('movies.delete_movie'))

        self.assertEqual(self.client.get(reverse('admin:movies_movie_add')).status_code, 200)
        self.assertEqual(
            self.client.get(reverse('admin:movies_movie_change', args=[movie.pk])).status_code, 200
        )
        self.assertEqual(
            self.client.get(reverse('admin:movies_movie_delete', args=[movie.pk])).status_code, 403
        )

    def test_editor_delete_button_disappears_from_the_changelist(self):
        genre = Genre.objects.create(name='Drama')
        make_movie('Roma', 2018, [genre])
        response = self.client.get(reverse('admin:movies_movie_changelist'))
        actions = response.context['cl'].model_admin.get_actions(self._request())

        self.assertNotIn('delete_selected', actions)
        self.assertNotContains(response, 'delete_selected')

    def test_admin_delete_action_is_available_to_a_superuser(self):
        genre = Genre.objects.create(name='Drama')
        movie = make_movie('Roma', 2018, [genre])

        self.client.force_login(self.admin)
        changelist = self.client.get(reverse('admin:movies_movie_changelist'))
        change_form = self.client.get(reverse('admin:movies_movie_change', args=[movie.pk]))

        self.assertIn(
            'delete_selected', changelist.context['cl'].model_admin.get_actions(self._request(self.admin))
        )
        self.assertContains(changelist, 'delete_selected')
        self.assertContains(change_form, reverse('admin:movies_movie_delete', args=[movie.pk]))

    def test_editor_change_form_has_no_delete_button(self):
        genre = Genre.objects.create(name='Drama')
        movie = make_movie('Roma', 2018, [genre])

        response = self.client.get(reverse('admin:movies_movie_change', args=[movie.pk]))

        self.assertNotContains(response, reverse('admin:movies_movie_delete', args=[movie.pk]))

    def test_editor_add_and_change_links_stay_available(self):
        genre = Genre.objects.create(name='Drama')
        movie = make_movie('Roma', 2018, [genre])

        response = self.client.get(reverse('admin:movies_movie_changelist'))

        self.assertContains(response, reverse('admin:movies_movie_add'))
        self.assertContains(response, reverse('admin:movies_movie_change', args=[movie.pk]))

    def test_editor_cannot_manage_users_or_groups(self):
        self.assertEqual(self.client.get(reverse('admin:auth_user_changelist')).status_code, 403)
        self.assertEqual(self.client.get(reverse('admin:auth_group_changelist')).status_code, 403)

    def test_editor_cannot_add_genres(self):
        self.assertFalse(self.editor.has_perm('movies.add_genre'))
        self.assertEqual(
            self.client.get(reverse('admin:movies_genre_add')).status_code, 403
        )

    def test_superuser_keeps_every_permission(self):
        for codename in ['add', 'change', 'delete', 'view']:
            self.assertTrue(self.admin.has_perm(f'movies.{codename}_movie'))


class PublicViewTests(TestCase):
    def setUp(self):
        self.drama = Genre.objects.create(name='Drama')
        self.animation = Genre.objects.create(name='Animation')
        self.director = Person.objects.create(name='Hayao Miyazaki')
        self.spirited = make_movie(
            'Spirited Away', 2001, [self.animation], [self.director],
            ratings=[('Ana', 10), ('Luis', 9)],
        )
        self.totoro = make_movie(
            'My Neighbor Totoro', 1988, [self.animation], [self.director],
            ratings=[('Ana', 9)],
        )
        self.roma = make_movie('Roma', 2018, [self.drama], ratings=[('Ana', 8)])

    def test_recommendation_list_ranks_genres_by_average(self):
        response = self.client.get(reverse('movies:recommendation_list'))

        self.assertEqual(response.status_code, 200)
        names = [block['genre'].name for block in response.context['recommendations']]
        self.assertEqual(names, ['Animation', 'Drama'])

    def test_movie_detail_shows_its_ratings_and_peers(self):
        response = self.client.get(
            reverse('movies:movie_detail', args=[self.spirited.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['average_score'], 9.5)
        self.assertEqual(
            [movie.title for movie in response.context['recommendations']],
            ['My Neighbor Totoro'],
        )
        self.assertContains(response, 'Spirited Away')
        self.assertContains(response, '9,5')

    def test_movie_detail_returns_404_for_a_missing_movie(self):
        response = self.client.get(reverse('movies:movie_detail', args=[99999]))

        self.assertEqual(response.status_code, 404)

    def test_recommendation_view_is_public(self):
        self.assertNotIn('/admin/', reverse('movies:recommendation_list'))


class BootstrapCommandTests(TestCase):
    def test_seed_movies_is_idempotent(self):
        call_command('seed_movies', stdout=StringIO())
        first = (Genre.objects.count(), Movie.objects.count(), Rating.objects.count())

        call_command('seed_movies', stdout=StringIO())
        second = (Genre.objects.count(), Movie.objects.count(), Rating.objects.count())

        self.assertEqual(first, second)
        self.assertEqual(Genre.objects.count(), 4)
        self.assertEqual(Movie.objects.count(), 10)
        self.assertGreaterEqual(Rating.objects.count(), 5)
        self.assertGreaterEqual(
            Movie.objects.annotate(total=Count('ratings')).filter(total__gt=0).count(),
            5,
        )

    def test_bootstrap_editor_creates_group_and_user(self):
        call_command('bootstrap_editor', stdout=StringIO())

        group = Group.objects.get(name='editores')
        user = get_user_model().objects.get(username='editor')

        codenames = set(group.permissions.values_list('codename', flat=True))
        self.assertIn('add_movie', codenames)
        self.assertIn('change_movie', codenames)
        self.assertNotIn('delete_movie', codenames)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertIn(group, user.groups.all())
