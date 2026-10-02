# Portal de Noticias — Laboratorio de plantillas Django

Proyecto del laboratorio de la sesión: motor de plantillas de Django con
herencia, fragmentos reutilizables, filtros, panel de administración y
contenido gestionado íntegramente desde el panel.

## 1. Requisitos

- Windows 10 o superior
- Python 3.12 o superior (probado con 3.13)
- Git
- Visual Studio Code

## 2. Puesta en marcha

```powershell
# Crear y activar el entorno virtual
py -m venv .venv
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Aplicar migraciones y cargar los datos de demostración
python manage.py migrate
python manage.py seed_news

# Crear el superusuario (o reutilizar el ya creado: admin / Admin12345)
python manage.py createsuperuser

# Arrancar el servidor de desarrollo
python manage.py runserver
```

Páginas disponibles:

| Página                    | URL                                              | Nombre de ruta          |
| ------------------------- | ------------------------------------------------ | ----------------------- |
| Portada                   | http://127.0.0.1:8000/                           | `news:home`             |
| Detalle de noticia        | http://127.0.0.1:8000/article/<slug>/            | `news:article_detail`   |
| Listado por categoría     | http://127.0.0.1:8000/category/<slug>/           | `news:category_list`    |
| Panel de administración   | http://127.0.0.1:8000/admin/                     | —                       |

## 3. Estructura del proyecto

```
DESARROLLOEPM/
├── config/                     # Proyecto Django
│   ├── settings.py             # Sin credenciales escritas a mano
│   └── urls.py                 # Sirve los medios en desarrollo
├── news/                       # Aplicación de noticias
│   ├── management/commands/
│   │   └── seed_news.py        # Datos de demostración (Pillow)
│   ├── migrations/             # Migraciones versionadas
│   ├── templates/news/
│   │   ├── _article_card.html  # Fragmento reutilizable (tarjeta)
│   │   ├── home.html           # Portada
│   │   ├── article_detail.html # Detalle de la noticia
│   │   └── category_list.html  # Listado por categoría
│   ├── admin.py                # list_display, list_filter, search_fields
│   ├── context_processors.py   # Categorías para la barra lateral
│   ├── models.py               # Article, Category, Author (singular)
│   ├── urls.py                 # Rutas con nombre propio
│   └── views.py                # Vistas de las tres páginas
├── static/css/styles.css       # Hoja de estilos ({% load static %})
├── templates/base.html         # Plantilla base con 3 bloques
├── media/                      # Imágenes subidas (no se versiona)
├── manage.py
└── requirements.txt
```

## 4. Cómo se cumple cada punto del procedimiento

1. **Proyecto y app** — `django-admin startproject config .` +
   `startapp news`; Pillow instalado; `news` declarada en
   `INSTALLED_APPS` (`config/settings.py`).
2. **Plantillas, estáticos y medios** — `TEMPLATES['DIRS']` apunta a
   `templates/`, `STATICFILES_DIRS` a `static/`, y `MEDIA_URL` /
   `MEDIA_ROOT` están configurados; `config/urls.py` sirve los medios
   con `static()` cuando `DEBUG` está activo.
3. **Modelos** — `Article` (imagen destacada `ImageField`,
   `published_at`, relación `ForeignKey` con `Author` y
   `ManyToManyField` con `Category`), `Category` y `Author`, todos en
   singular. Migraciones versionadas en `news/migrations/`.
4. **base.html** — estructura común con tres bloques: `title`,
   `content` y `sidebar`.
5. **_article_card.html** — fragmento de tarjeta incluido con
   `{% include %}` desde `home.html` y `category_list.html`; el marcado
   no se repite.
6. **Portada** — `{% for %}` sobre las noticias, `{% empty %}` para el
   caso sin resultados, filtro `date` para la fecha de publicación y
   `truncatewords` para recortar el resumen.
7. **Detalle** — hereda de la base y muestra imagen destacada, autor
   (con caja de biografía) y categorías enlazadas.
8. **Listado por categoría** — reutiliza el mismo fragmento de tarjeta.
9. **Rutas con nombre** — `home`, `article_detail` y `category_list`
   bajo el espacio de nombres `news`; todos los enlaces usan
   `{% url %}`, ninguna dirección se escribe a mano.
10. **Estáticos** — `base.html` hace `{% load static %}` y enlaza
    `static/css/styles.css`; las imágenes destacadas se sirven desde
    `MEDIA_ROOT`.
11. **Administrador** — los tres modelos personalizados con
    `list_display`, `list_filter` y `search_fields` (ver
    `news/admin.py`); el comando `seed_news` da de alta las 6 noticias
    en 3 categorías.
12. **Escapado automático** — ver la sección siguiente.
13. **Repositorio** — proyecto versionado con Git (`.gitignore`
    incluido).

## 5. Prueba del escapado automático (punto 12)

La noticia **«Prueba del escapado automático de plantillas»** guarda en
su cuerpo HTML escrito a mano:

```html
Este párrafo contiene <strong>negrita escrita a mano</strong> y un
enlace <a href="https://example.com">de ejemplo</a> …
<script>alert("ataque XSS")</script>
```

**Qué muestra la página:** las etiquetas aparecen como texto literal en
pantalla (`<strong>…`, `<script>…`), sin aplicar negrita, sin enlace
clicable y sin ejecutar el script.

**Por qué:** el motor de plantillas de Django escapa automáticamente el
contenido de las variables (`{{ article.body }}`), sustituyendo `<`,
`>`, `"` y `&` por sus entidades HTML (`&lt;`, `&gt;`, `&quot;`,
`&amp;`). Así, cualquier HTML almacenado en la base de datos se muestra
como texto en lugar de interpretarse, lo que neutraliza ataques XSS por
defecto. Solo si se aplicara el filtro `|safe` el HTML se renderizaría,
y eso sería una decisión explícita del desarrollador.

## 6. Casos de prueba

| # | Caso | Resultado esperado |
|---|------|--------------------|
| 1 | Abrir `/` | Se listan las 6 noticias ordenadas de la más reciente a la más antigua |
| 2 | Portada sin noticias (despublicar todas desde el admin) | Aparece el mensaje «Todavía no hay noticias publicadas» (`{% empty %}`) |
| 3 | Clic en el título de una tarjeta | Se abre el detalle con imagen, fecha formateada, autor y categorías |
| 4 | Clic en una etiqueta de categoría | Se abre el listado filtrado; solo aparecen las noticias de esa sección |
| 5 | Categoría sin noticias | Mensaje «Esta sección aún no tiene noticias publicadas» |
| 6 | Editar una noticia en `/admin/` | El cambio se refleja en el portal sin tocar código |
| 7 | Buscar «Django» en el buscador del admin de artículos | Filtra por título, resumen y cuerpo |
| 8 | Ver el detalle de la noticia «Prueba del escapado…» | Las etiquetas HTML se muestran como texto, no se ejecutan |
| 9 | Revisar el código fuente de cualquier página | Los enlaces internos se generaron con `{% url %}` y la CSS con `{% static %}` |
| 10 | Abrir directamente `/media/articles/…png` | La imagen destacada se sirve en desarrollo |

## 7. Evidencias para el entregable

Para cada integrante, en la sección de desarrollo del informe:

1. Nombre del alumno y título del desarrollo.
2. Captura del resultado (portada, detalle, listado y admin).
3. Código correspondiente.
4. Explicación del resultado.
5. Casos de prueba (tabla anterior).
6. Captura de la estructura del proyecto en el explorador de VS Code.
