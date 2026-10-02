"""
Seed the database with demo content for the news portal.

Creates 3 categories, 2 authors and 6 published articles with a
generated featured image for each one (Pillow). One of the articles
stores raw HTML in its body on purpose to demonstrate the template
auto-escaping behaviour.

Usage:
    python manage.py seed_news
"""
from datetime import timedelta
from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from PIL import Image, ImageDraw, ImageFont

from news.models import Article, Author, Category

CATEGORIES = [
    {
        'name': 'Tecnología',
        'description': 'Noticias sobre software, hardware y el mundo digital.',
        'color': (26, 58, 92),
    },
    {
        'name': 'Deportes',
        'description': 'Resultados, fichajes y toda la actualidad deportiva.',
        'color': (39, 174, 96),
    },
    {
        'name': 'Cultura',
        'description': 'Cine, libros, música y agenda cultural.',
        'color': (142, 68, 173),
    },
]

AUTHORS = [
    {
        'first_name': 'Lucía',
        'last_name': 'Ramírez',
        'email': 'lucia.ramirez@example.com',
        'bio': 'Redactora senior especializada en tecnología y deportes.',
    },
    {
        'first_name': 'Marco',
        'last_name': 'Torres',
        'email': 'marco.torres@example.com',
        'bio': 'Cronista cultural y fotógrafo del portal.',
    },
]

ARTICLES = [
    {
        'title': 'La inteligencia artificial llega a las aulas peruanas',
        'category': 'Tecnología',
        'author': 'lucia.ramirez@example.com',
        'summary': (
            'Varios institutos piloto incorporan asistentes de IA en sus '
            'laboratorios de programación para el próximo ciclo lectivo.'
        ),
        'body': (
            'Un grupo de institutos tecnológicos del país iniciará el próximo '
            'semestre un programa piloto que integra asistentes de '
            'inteligencia artificial en los cursos de desarrollo de software.\n\n'
            'Los docentes destacan que la herramienta no reemplaza al '
            'profesor, sino que actúa como un tutor disponible las 24 horas '
            'para resolver dudas de sintaxis y buenas prácticas.'
        ),
        'days_ago': 0,
    },
    {
        'title': 'Django 6 consolida el desarrollo web en Python',
        'category': 'Tecnología',
        'author': 'marco.torres@example.com',
        'summary': (
            'El framework más popular de Python estrena versión con mejoras '
            'en el motor de plantillas y en el panel de administración.'
        ),
        'body': (
            'La nueva versión del framework refuerza el sistema de plantillas '
            'con herencia y fragmentos reutilizables, dos piezas clave para '
            'mantener portales de noticias sin duplicar marcado.\n\n'
            'La comunidad celebra también las mejoras de rendimiento en el '
            'panel de administración, que sigue siendo una de las razones '
            'principales para elegir Django en proyectos editoriales.'
        ),
        'days_ago': 1,
    },
    {
        'title': 'El clásico se tiñe de rojo: crónica de una noche histórica',
        'category': 'Deportes',
        'author': 'lucia.ramirez@example.com',
        'summary': (
            'Un gol en el minuto 93 desató la locura en el estadio y deja al '
            'equipo local a un paso del título del torneo.'
        ),
        'body': (
            'El estadio entero contuvo la respiración hasta el minuto 93, '
            'cuando un cabezazo en el segundo palo puso el 2-1 definitivo en '
            'el marcador del clásico.\n\n'
            'Con este resultado, el equipo local queda a un solo punto de '
            'asegurar el campeonato a falta de dos jornadas para el final.'
        ),
        'days_ago': 2,
    },
    {
        'title': 'Atleta peruana bate el récord sudamericano de los 400 metros',
        'category': 'Deportes',
        'author': 'marco.torres@example.com',
        'summary': (
            'Con un tiempo de 49.87 segundos, la velocista nacional firmó la '
            'mejor marca continental de la década.'
        ),
        'body': (
            'La atleta nacional detuvo el crono en 49.87 segundos y estableció '
            'un nuevo récord sudamericano de los 400 metros lisos.\n\n'
            'La marca la acredita además como una de las principales '
            'candidatas a la medalla en el próximo campeonato mundial.'
        ),
        'days_ago': 3,
    },
    {
        'title': 'El festival de cine independiente abre sus puertas en el centro histórico',
        'category': 'Cultura',
        'author': 'marco.torres@example.com',
        'summary': (
            'Doce óperas primas compiten esta semana por el galardón del '
            'público en la décima edición del certamen.'
        ),
        'body': (
            'La décima edición del festival reúne doce óperas primas de '
            'directores emergentes de toda la región.\n\n'
            'Además de la competencia oficial, la programación incluye '
            'talleres de guion y charlas con directores consagrados.'
        ),
        'days_ago': 4,
    },
    {
        'title': 'Prueba del escapado automático de plantillas',
        'category': 'Cultura',
        'author': 'lucia.ramirez@example.com',
        'summary': (
            'Noticia de prueba: su cuerpo contiene etiquetas HTML escritas a '
            'mano para comprobar el escapado automático de Django.'
        ),
        # This body intentionally contains raw HTML, including a script
        # tag, to verify that the template engine escapes it.
        'body': (
            'Este párrafo contiene <strong>negrita escrita a mano</strong> y '
            'un enlace <a href="https://example.com">de ejemplo</a> guardados '
            'como texto en la base de datos.\n\n'
            'Incluso intentamos colar un script: '
            '<script>alert("ataque XSS")</script>. '
            'Si el motor de plantillas hace su trabajo, todo esto se muestra '
            'tal cual, sin ejecutarse.'
        ),
        'days_ago': 5,
    },
]


def make_placeholder_image(text, color, size=(800, 450)):
    """Generate a simple featured image with Pillow."""
    image = Image.new('RGB', size, color)
    draw = ImageDraw.Draw(image)

    # Draw a lighter diagonal band to give the image some texture.
    lighter = tuple(min(channel + 40, 255) for channel in color)
    draw.polygon(
        [(0, size[1]), (size[0] * 0.6, size[1]), (size[0], 0), (size[0] * 0.4, 0)],
        fill=lighter,
    )

    try:
        font = ImageFont.truetype('arial.ttf', 54)
    except OSError:
        font = ImageFont.load_default(size=40)

    bounding_box = draw.textbbox((0, 0), text, font=font)
    text_width = bounding_box[2] - bounding_box[0]
    text_height = bounding_box[3] - bounding_box[1]
    position = ((size[0] - text_width) / 2, (size[1] - text_height) / 2)
    draw.text(position, text, font=font, fill=(255, 255, 255))

    buffer = BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()


class Command(BaseCommand):
    help = 'Seed the database with demo news content.'

    def handle(self, *args, **options):
        categories = {}
        for data in CATEGORIES:
            category, created = Category.objects.update_or_create(
                slug=slugify(data['name']),
                defaults={
                    'name': data['name'],
                    'description': data['description'],
                },
            )
            categories[data['name']] = category
            self.stdout.write(
                f"Category '{category.name}': {'created' if created else 'updated'}"
            )

        authors = {}
        for data in AUTHORS:
            author, created = Author.objects.update_or_create(
                email=data['email'],
                defaults=data,
            )
            authors[data['email']] = author
            self.stdout.write(
                f"Author '{author}': {'created' if created else 'updated'}"
            )

        now = timezone.now()
        for index, data in enumerate(ARTICLES, start=1):
            category = categories[data['category']]
            article, created = Article.objects.update_or_create(
                slug=slugify(data['title']),
                defaults={
                    'title': data['title'],
                    'summary': data['summary'],
                    'body': data['body'],
                    'author': authors[data['author']],
                    'published_at': now - timedelta(days=data['days_ago']),
                    'is_published': True,
                },
            )
            article.categories.set([category])

            if created or not article.featured_image:
                image_bytes = make_placeholder_image(
                    data['category'],
                    next(c['color'] for c in CATEGORIES if c['name'] == data['category']),
                )
                filename = f"{article.slug or 'article'}-{index}.png"
                article.featured_image.save(
                    Path(filename).name, ContentFile(image_bytes), save=True
                )

            self.stdout.write(
                f"Article '{article.title}': {'created' if created else 'updated'}"
            )

        self.stdout.write(self.style.SUCCESS('Seed complete: 3 categories, '
                                             '2 authors, 6 articles.'))
