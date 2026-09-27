# Administrador con Django — Semana 5

**Desarrollo de Aplicaciones Empresariales — 4-C24-A**
Alumno: Michael Montgomery Rosell

Catálogo de películas con panel de administración de Django: los cuatro modelos se
gestionan desde `/admin/` sin escribir una sola vista, y una vista pública
propia resuelve lo que el panel no puede calcular.

---

## 1. Puesta en marcha

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env          # en Linux/macOS: cp .env.example .env

python manage.py migrate
python manage.py seed_movies        # 4 generos, 8 personas, 10 peliculas, 17 valoraciones
python manage.py bootstrap_admin    # superusuario
python manage.py bootstrap_editor   # grupo "editores" + usuario de prueba
python manage.py runserver
```

Panel: <http://127.0.0.1:8000/admin/> — Vista pública: <http://127.0.0.1:8000/>

| Cuenta | Clave (solo laboratorio) | Rol |
| --- | --- | --- |
| `admin` | `admin-Lab05` | Superusuario: todo permitido |
| `editor` | `editor-Lab05` | Miembro del grupo `editores`: añade y cambia, nunca elimina |

Las credenciales se toman de `.env`, que está en `.gitignore`. `settings.py`
no contiene ninguna credencial escrita a mano: si falta `DJANGO_SECRET_KEY`, el
proyecto genera una aleatoria y la guarda en `.env` en la primera ejecución.

---

## 2. Estructura del proyecto

```
DESARROLLOEMPSEM5/
├── manage.py
├── requirements.txt          Django 6.1, Pillow 12.3
├── .env.example              plantilla de credenciales (el .env real no se sube)
├── .gitignore
├── config/                   proyecto (no una app de negocio)
│   ├── settings.py           lee el entorno; sin secretos en el código
│   ├── urls.py               admin/ y movies/
│   ├── asgi.py / wsgi.py
├── movies/                   única aplicación de negocio
│   ├── models.py             Genre, Person, Movie, Rating
│   ├── admin.py              ModelAdmin + inline + campos de solo lectura
│   ├── views.py              recomendación y detalle
│   ├── urls.py
│   ├── tests.py              31 pruebas
│   ├── migrations/0001_initial.py
│   ├── management/commands/  seed_movies, bootstrap_admin, bootstrap_editor
│   └── templates/movies/     base, recommendation_list, movie_detail
└── media/                    pósters y fotos (ignorado por git)
```

---

## 3. Modelos

| Modelo | Campos | Relaciones |
| --- | --- | --- |
| `Genre` | `name` (único), `description` | — |
| `Person` | `name`, `role`, `birth_date`, `biography`, `photo`, `created_at`, `updated_at` | — |
| `Movie` | `title`, `year`, `summary`, `poster`, `created_at`, `updated_at` | **M2M** `genres`→`Genre`, **M2M** `directors`→`Person` |
| `Rating` | `reviewer`, `score` (1-10), `comment`, `created_at`, `updated_at` | **FK** `movie`→`Movie` (`on_delete=CASCADE`, `related_name="ratings"`) |

Cada modelo lleva su `class Meta` (`ordering`, `verbose_name`) y su `__str__`:

- `Genre` → `Science fiction`
- `Person` → `Denis Villeneuve`
- `Movie` → `Arrival (2016)`
- `Rating` → `Arrival - 9/10 by Ana`

`Rating` tiene un `UniqueConstraint(movie, reviewer)`: un crítico no valora dos
veces la misma película. Pillow se necesita para los dos `ImageField`.

---

## 4. Configuración del panel

### 4.1 Las cuatro operaciones sin escribir vistas

`admin.site.register(Movie)` y compañía bastan para obtener alta, cambio,
borrado y lectura. Los cuatro modelos aparecen en `/admin/` con su
"añadir/ver/cambiar/eliminar" sin una sola vista escrita. Eso se comprueba en
`AdminPanelTests.test_four_crud_operations_work_without_writing_a_view`, que
recorre las cuatro URLs con el cliente de pruebas.

### 4.2 `ModelAdmin` por modelo

**`MovieAdmin`** — `movies/admin.py:29`

| Opción | Valor | Para qué |
| --- | --- | --- |
| `list_display` | `title, year, genres_list, directors_list, avg_score, updated_at` | Ver de un vistazo qué es cada película y cuánto vale |
| `list_filter` | `genres`, `year` | Los dos cortes que se usan al revisar el catálogo |
| `search_fields` | `title`, `directors__name` | Buscar por título **o** por director, sin salir del panel |
| `list_editable` | `year` | Corregir un año sin abrir la ficha |
| `list_per_page` | `10` | Las 15 filas por defecto obligaban a paginar en cada revisión |
| `filter_horizontal` | `genres`, `directors` | Checkbox de dos columnas, mejor que el multiselect con 8 personas |
| `readonly_fields` | `created_at`, `updated_at` | Auditoría gestionada por Django, no por el usuario |
| `inlines` | `[RatingInline]` | Las valoraciones se dan de alta dentro de la película |
| `fieldsets` | `Data`, `Relations`, `Audit` (plegado) | Formulario en tres bloques legibles |
| `get_queryset` | `annotate(avg_score=Avg(...))` | La columna de media es ordenable |

`genres_list`, `directors_list`, `avg_score` y `movie_count` son métodos
decorados con `@admin.display(description=...)`, con su `ordering` para que la
columna se pueda ordenar.

**`GenreAdmin`** — `name`, `movie_count`, `description`; busca por nombre y
descripción.
**`PersonAdmin`** — `name`, `role`, `birth_date`, `movie_count`, `updated_at`;
filtra por rol, busca por nombre/rol/biografía, auditoría de solo lectura.
**`RatingAdmin`** — `movie`, `reviewer`, `score`, `comment_short`, `created_at`;
filtra por nota y por película, edita la nota en línea, busca por crítico,
título de película o comentario, y usa `autocomplete_fields = ['movie']` para
no arrastrar un desplegable con 10 títulos.

### 4.3 Valoraciones en línea

`RatingInline(admin.TabularInline)` — `movies/admin.py:11`. Es una
`TabularInline` y no una `StackedInline` porque cada fila es un dato corto
(crítico, nota, comentario) y en tabla caben más sin desperdiciar alto. Con
`extra = 1` siempre hay una fila libre para la siguiente valoración. Así se
crean las valoraciones sin salir del registro de la película ni abrir otra
pestaña.

### 4.4 Auditoría de solo lectura

`created_at` (auto_now_add) y `updated_at` (auto_now) están en
`readonly_fields` de `MovieAdmin`, `PersonAdmin` y `RatingAdmin`. El panel los
muestra dentro del *fieldset* "Audit" plegado, pero no los incluye en el
formulario: no hay `<input>` que se pueda alterar. Comprobado en
`test_audit_fields_are_not_writable` y
`test_posting_the_form_does_not_change_the_audit_dates`, que envía fechas
falsas por POST y verifica que la base de datos no cambia.

---

## 5. Datos de prueba

`python manage.py seed_movies` carga **4 géneros** (Science fiction, Drama,
Thriller, Animation), **8 personas**, **10 películas** y **17 valoraciones sobre 8
de esas películas**. El comando es idempotente (`get_or_create` en todo), así que
se puede repetir sin duplicar nada. En el panel también se pueden crear a mano:
el enunciado pide cargarlos desde el panel, y el comando existe para que el
equipo pueda reproducir el estado inicial de la base de datos con un comando y
no con 30 clics.

---

## 6. Roles y permisos

El grupo `editores` se crea con `python manage.py bootstrap_editor` y lleva
exactamente ocho permisos:

| Permiso | Por qué sí |
| --- | --- |
| `add_movie`, `change_movie` | El editor carga y corrige fichas |
| `add_rating`, `change_rating` | El editor registra y ajusta valoraciones |
| `view_movie`, `view_rating`, `view_genre`, `view_person` | Puede consultar lo que edita |
| — | **`delete_movie` y `delete_rating` NO están.** Un borrado es irreversible y la decisión le corresponde a quien administra el catálogo |

Los géneros y las personas quedan solo en lectura para el editor: definirlos es
una decisión de taxonomía, no de carga de contenido. El grupo tampoco tiene
permisos sobre `auth.User` ni `auth.Group`, así que no puede crear cuentas ni
escalarse a sí mismo.

### Superusuario frente a usuario editor

Medido sobre el servidor real, con las dos cuentas dentro:

| Comprobación | `admin` (superusuario) | `editor` (grupo `editores`) |
| --- | --- | --- |
| Panel: Usuarios y Grupos | visible | **oculto** |
| Panel: Géneros / Personas / Valoraciones | visible | visible |
| Lista de películas: enlace "Añadir" | sí | sí |
| Lista de películas: acción "Eliminar seleccionados" | sí | **no aparece** |
| Lista de películas: filtro por género y por año | sí | sí |
| Lista de películas: buscador | sí | sí |
| Ficha de película: bloque de valoraciones en línea | sí | sí |
| Ficha de película: fechas de auditoría | visibles, no editables | visibles, no editables |
| Ficha de película: botón "Eliminar" | sí | **no aparece** |
| `GET /admin/movies/movie/1/delete/` | 200 | **403** |
| `GET /admin/movies/genre/add/` | 200 | **403** |
| `GET /admin/auth/user/` | 200 | **403** |
| `GET /admin/auth/group/` | 200 | **403** |

Lo importante es el **403**: no es que el botón esté oculto, es que la URL
también está protegida. Ocultar el enlace sin permiso detrás es la mitad del
trabajo; Django resuelve las dos.

---

## 7. Lo que el panel no puede hacer

El panel registra, filtra, busca y edita. No calcula. "Las películas del mismo
género mejor valoradas" necesita una agregación sobre `Rating`, y eso ya no es
un `ModelAdmin` sino una vista.

- `Movie.best_movies_of_same_genre()` — `movies/models.py:80`
- `movies.views.recommendation_list` — `movies/views.py:13` — ordena los géneros
  por la media de sus películas y muestra las tres mejores de cada uno.
- `movies.views.movie_detail` — `movies/views.py:47` — ficha con la media, las
  valoraciones y las recomendaciones del mismo género.

Las tres usan `Avg` sobre `ratings__score`; ninguna reutiliza el panel. Esa
diferencia es el punto del laboratorio: el administrador resuelve el CRUD, la
vista resuelve la consulta.

---

## 8. Casos de prueba

```bash
python manage.py test movies -v 2
```

31 pruebas, todas en verde. Cubren lo que la rúbrica pide comprobar.

| # | Caso | Qué demuestra |
| --- | --- | --- |
| 1 | `test_str_of_each_model` | El `__str__` de los cuatro modelos es legible en el panel |
| 2 | `test_movie_uses_many_to_many_for_genres` | M2M: una película en varios géneros, un género en varias películas |
| 3 | `test_rating_belongs_to_a_movie_and_is_deleted_with_it` | FK con `CASCADE`: al borrar la película se van sus valoraciones |
| 4 | `test_average_score` | La media de las notas, y `None` si no hay ninguna |
| 5 | `test_best_movies_of_same_genre_excludes_itself_and_orders_by_score` | La recomendación excluye la película, las de otro género y las no valoradas, y ordena por media |
| 6 | `test_score_out_of_range_is_rejected` | Una nota de 11 no se guarda |
| 7 | `test_one_rating_per_reviewer_and_movie` | La restricción `(movie, reviewer)` impide la doble valoración |
| 8 | `test_the_four_models_are_registered` | Los cuatro modelos están registrados con su `ModelAdmin` |
| 9 | `test_movie_admin_customisation` | `list_display`, `list_filter` por género y año, `search_fields` por título y director, `readonly_fields` y el inline |
| 10 | `test_rating_inline_is_tabular_and_editable` | El inline es `TabularInline` y expone la nota |
| 11 | `test_admin_index_lists_every_model` | El panel muestra Movies, Genres, People y Ratings |
| 12 | `test_four_crud_operations_work_without_writing_a_view` | Alta, cambio y borrado por POST, sin ninguna vista escrita |
| 13 | `test_ratings_are_created_from_the_movie_form` | Dos valoraciones creadas desde la ficha, sin salir de ella |
| 14 | `test_audit_fields_are_not_writable` | `created_at` y `updated_at` no están en el formulario |
| 15 | `test_posting_the_form_does_not_change_the_audit_dates` | Enviar fechas falsas por POST no altera la auditoría |
| 16 | `test_movie_list_shows_average_and_filters` | Buscador y filtro por género combinados en el listado |
| 17 | `test_search_finds_a_movie_by_director_name` | La búsqueda encuentra por director, no solo por título |
| 18 | `test_editor_can_add_and_change_but_not_delete_a_movie` | El editor accede a añadir y cambiar; el borrado da 403 |
| 19 | `test_editor_delete_button_disappears_from_the_changelist` | La acción `delete_selected` no está en el listado del editor |
| 20 | `test_editor_change_form_has_no_delete_button` | La ficha del editor no tiene botón de borrar |
| 21 | `test_admin_delete_action_is_available_to_a_superuser` | El superusuario sí conserva el borrado |
| 22 | `test_editor_add_and_change_links_stay_available` | El editor conserva alta y cambio |
| 23 | `test_editor_cannot_manage_users_or_groups` | Usuarios y grupos dan 403 para el editor |
| 24 | `test_editor_cannot_add_genres` | Los géneros son de solo lectura para el editor |
| 25 | `test_superuser_keeps_every_permission` | El superusuario conserva las cuatro operaciones |
| 26 | `test_recommendation_list_ranks_genres_by_average` | La vista pública ordena los géneros por media |
| 27 | `test_movie_detail_shows_its_ratings_and_peers` | El detalle muestra media, valoraciones y pares del mismo género |
| 28 | `test_movie_detail_returns_404_for_a_missing_movie` | 404 en una película inexistente |
| 29 | `test_recommendation_view_is_public` | La recomendación no vive en `/admin/` |
| 30 | `test_seed_movies_is_idempotent` | El seed se puede repetir: 4 géneros, 10 películas, 8 con nota, sin duplicar |
| 31 | `test_bootstrap_editor_creates_group_and_user` | El grupo se crea con añadir/cambiar y sin borrar; el usuario no es superusuario |

---

## 9. Reparto de trabajo

| Integrante | Tarea | Archivo |
| --- | --- | --- |
| Michael Montgomery Rosell | Modelos, migraciones, registro de los cuatro modelos y `ModelAdmin` con listado, filtros y búsqueda | `movies/models.py`, `movies/migrations/0001_initial.py` |
| Michael Montgomery Rosell | Inline de valoraciones y campos de auditoría de solo lectura | `movies/admin.py` |
| Michael Montgomery Rosell | Datos de prueba, grupo `editores` y su usuario de prueba | `movies/management/commands/` |
| Michael Montgomery Rosell | Vista pública de recomendación y plantillas | `movies/views.py`, `movies/urls.py`, `movies/templates/movies/` |
| Michael Montgomery Rosell | Casos de prueba y comparativa superusuario / editor | `movies/tests.py` |
| Pendiente de asignar | Revisión de la entrega y subida al campus virtual | — |

> Los nombres de los demás integrantes del equipo se completan aquí antes de
> subir el repositorio.

---

## 10. Conclusiones

1. **El panel no se personaliza con plantillas, sino con opciones.**
   `list_display`, `list_filter` y `search_fields` están pensados para cómo se
   usa el catálogo: se revisa por género y por año, y se busca por título o por
   director. Cambiar el listado sin filtros ni búsqueda deja el panel con la
   misma información, pero obliga a recorrer todos los registros para
   encontrar una película concreta.

2. **Los permisos hay que probarlos con dos cuentas, no leerlos.**
   El grupo `editores` parecía correcto en la pantalla de permisos. Al entrar
   con esa cuenta apareció lo que de verdad importa: el botón de borrar
   desaparece **y** la URL devuelve 403. Un permiso sin comprobar es una
   suposición.

3. **Separar quién decide y quién ejecuta evita borrados accidentales.**
   El editor carga y corrige; el borrado queda con quien administra. Esa
   separación es más valiosa que la cantidad de permisos concedidos.

4. **Lo que el panel no puede calcular necesita una vista.**
   La recomendación por género exige un `Avg` sobre las valoraciones. Ninguna
   opción de `ModelAdmin` resuelve eso. El laboratorio de esta semana muestra
   el límite del panel: es excelente editando registros, y se queda corto
   cuando la pregunta es "¿cuál recomiendas?".

5. **Las fechas de auditoría no se editan, se leen.**
   `readonly_fields` las saca del formulario. Es la forma más barata de
   garantizar que nadie inventa cuándo se creó un registro.

6. **Los datos de prueba también son código.**
   `seed_movies` es idempotente y reproducible: el equipo puede partir del
   mismo catálogo en cualquier máquina sin copiar la base de datos a mano.

---

## 11. Evidencia para el entregable

Capturas que hay que tomar en el editor y en el navegador:

1. Estructura del proyecto en VS Code.
2. `/admin/` **antes** de personalizar (registro simple).
3. `/admin/movies/movie/` **después**: listado con columnas, filtros y buscador.
4. Ficha de película con el bloque de valoraciones y el *fieldset* "Audit".
5. `/admin/movies/movie/1/change/` como superusuario, con el botón de borrar.
6. `/admin/movies/movie/1/change/` como `editor`, sin botón de borrar.
7. `/admin/movies/movie/1/delete/` como `editor`, con el 403.
8. `/admin/auth/user/` como `editor`, con el 403.
9. `/admin/auth/group/` con los ocho permisos de `editores` marcados.
10. `/` con las recomendaciones por género.
11. `/movies/1/` con la media y las recomendaciones del mismo género.
12. Salida de `python manage.py test movies -v 2` con los 31 casos en verde.
