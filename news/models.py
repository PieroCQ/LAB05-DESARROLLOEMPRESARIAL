"""
Models for the news application.

One model per responsibility, named in singular as required by the
course conventions:
- Category: a thematic section of the portal.
- Author:   a writer who signs articles.
- Article:  a published news piece with a featured image.
"""
from django.db import models
from django.urls import reverse


class Category(models.Model):
    """Thematic section used to group articles."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('news:category_list', args=[self.slug])


class Author(models.Model):
    """Writer of one or more articles."""

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='authors/', blank=True, null=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'


class Article(models.Model):
    """News article shown on the portal."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    summary = models.TextField(help_text='Short teaser shown in the cards.')
    body = models.TextField()
    featured_image = models.ImageField(upload_to='articles/', blank=True, null=True)
    published_at = models.DateTimeField()
    is_published = models.BooleanField(default=True)

    # Relationships: each article is signed by one author and can
    # belong to several categories.
    author = models.ForeignKey(
        Author,
        on_delete=models.PROTECT,
        related_name='articles',
    )
    categories = models.ManyToManyField(Category, related_name='articles')

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('news:article_detail', args=[self.slug])
