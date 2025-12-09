# api/__init__.py
from .base import BaseClient
from .tvmaze import TVMazeMixin
from .tmdb import TMDBMixin
from .anilist import AniListMixin
from .omdb import OMDbMixin
from .streams import StreamsMixin
from .cinemeta import CinemetaMixin  # <--- NEW IMPORT

class StremioClient(BaseClient, TVMazeMixin, TMDBMixin, AniListMixin, OMDbMixin, StreamsMixin, CinemetaMixin):
    pass
