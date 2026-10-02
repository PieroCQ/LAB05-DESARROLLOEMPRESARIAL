"""
Admin site customization for the news application.

Each model gets list_display, list_filter and search_fields so the
editorial team can manage content comfortably from the panel.
"""
from django.contrib import admin

from .models import Article, Author, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    list_filter = ('name',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email')
    list_filter = ('last_name',)
    search_fields = ('first_name', 'last_name', 'email')


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category_names', 'published_at', 'is_published')
    list_filter = ('categories', 'is_published', 'published_at')
    search_fields = ('title', 'summary', 'body')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    filter_horizontal = ('categories',)

    @admin.display(description='Categories')
    def category_names(self, obj):
        return ', '.join(category.name for category in obj.categories.all())
