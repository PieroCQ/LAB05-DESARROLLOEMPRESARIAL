"""
Context processors for the news application.

`sidebar_categories` injects the full category list into every
template context, so the sidebar of base.html can render the section
links without each view having to pass them explicitly.
"""
from .models import Category


def sidebar_categories(request):
    return {'sidebar_categories': Category.objects.all()}
