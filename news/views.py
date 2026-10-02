"""
Views for the news application.

Each view only fetches data and hands it to a template; all the
presentation logic (loops, conditions, formatting) stays in the
templates using variables, tags and filters.
"""
from django.shortcuts import get_object_or_404, render

from .models import Article, Category


def home(request):
    """Front page: latest published articles."""
    articles = (
        Article.objects
        .filter(is_published=True)
        .select_related('author')
        .prefetch_related('categories')
    )
    return render(request, 'news/home.html', {'articles': articles})


def article_detail(request, slug):
    """Full page for a single article."""
    article = get_object_or_404(
        Article.objects.select_related('author').prefetch_related('categories'),
        slug=slug,
        is_published=True,
    )
    return render(request, 'news/article_detail.html', {'article': article})


def category_list(request, slug):
    """List of published articles that belong to one category."""
    category = get_object_or_404(Category, slug=slug)
    articles = (
        category.articles
        .filter(is_published=True)
        .select_related('author')
        .prefetch_related('categories')
    )
    return render(
        request,
        'news/category_list.html',
        {'category': category, 'articles': articles},
    )
