import dataclasses


@dataclasses.dataclass
class Movie:
    id: int
    name: str
    name_en: str
    description: str
    short_description: str
    poster: str


@dataclasses.dataclass
class MovieReleased(Movie):
    released_year: str
    rating_imdb: str
    rating_kp: str
    fees_value: str
    fees_currency: str

    @classmethod
    def from_dict_released(cls, list_of_movies: dict):
        poster_data = list_of_movies.get('poster', {})
        poster_url = poster_data.get('url') if poster_data else None
        return cls(
            id=list_of_movies.get('id'),
            name=list_of_movies.get('name'),
            name_en=list_of_movies.get('enName', ''),
            description=list_of_movies.get('description', ''),
            short_description=list_of_movies.get('shortDescription', ''),
            poster=poster_url,
            released_year=list_of_movies.get('year', ''),
            rating_imdb=list_of_movies.get('rating', {}).get('imdb', ''),
            rating_kp=list_of_movies.get('rating', {}).get('kp', ''),
            fees_value=list_of_movies.get('fees', {}).get('world', {}).get('value', ''),
            fees_currency=list_of_movies.get('fees', {})
            .get('world', {})
            .get('currency', ''),
        )


@dataclasses.dataclass
class MovieInProduction(Movie):
    premiere_date: str
    awaiting_rating: str
    awaiting_votes: str

    @classmethod
    def from_dict_in_production(cls, list_of_movies: dict):
        poster_data = list_of_movies.get('poster', {})
        poster_url = poster_data.get('url') if poster_data else None
        return cls(
            id=list_of_movies.get('id'),
            name=list_of_movies.get('name'),
            name_en=list_of_movies.get('enName', ''),
            description=list_of_movies.get('description', ''),
            short_description=list_of_movies.get('shortDescription') or '',
            poster=poster_url,
            premiere_date=list_of_movies.get('premiere', {}).get('world', ''),
            awaiting_rating=list_of_movies.get('rating', {}).get('await', ''),
            awaiting_votes=list_of_movies.get('votes', {}).get('await', ''),
        )
