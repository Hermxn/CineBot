import datetime

from dateutil.relativedelta import relativedelta


date_1_month = datetime.date.today() + relativedelta(months=1)
date_1_year = datetime.date.today() + relativedelta(months=12)
date_now_str = datetime.date.today().__format__('%d.%m.%Y')
date_1_month_str = date_1_month.__format__('%d.%m.%Y')
date_1_year_str = date_1_year.__format__('%d.%m.%Y')

request_release_month = (
    f'https://api.kinopoisk.dev/v1.3/movie?selectFields=premiere&selectFields='
    f'id&selectFields=enName&selectFields=name&selectFields=description&selectFields='
    f'rating.await&selectFields=shortDescription&selectFields=slogan&selectFields=poster.url&selectFields='
    f'videos.trailers.url&selectFields=poster.previewUrl&selectFields=votes.await&sortField='
    f'premiere&sortType=1&page=1&limit=20&type=movie&typeNumber=1&status=filming%20&status='
    f'pre-production&status=announced%20&status=post-production&rating.await='
    f'75-100&premiere.world={date_now_str}-{date_1_month_str}'
)

request_release_year = (
    f'https://api.kinopoisk.dev/v1.3/movie?selectFields=premiere&selectFields='
    f'id&selectFields=enName&selectFields=name&selectFields=description&selectFields='
    f'rating.await&selectFields=shortDescription&selectFields=slogan&selectFields=poster.url&selectFields='
    f'videos.trailers.url&selectFields=poster.previewUrl&selectFields=votes.await&sortField='
    f'premiere&sortType=1&page=1&limit=50&type=movie&typeNumber=1&status=filming%20&status='
    f'pre-production&status=announced%20&status=post-production&rating.await='
    f'75-100&premiere.world={date_now_str}-{date_1_year_str}'
)

request_info = 'https://api.kinopoisk.dev/v1.3/movie?page=1&limit=10&id='


request_id = (
    'https://api.kinopoisk.dev/v1.3/movie?selectFields=id&selectFields=name&selectFields='
    'enName&sortField=rating.imdb&sortType=-1&selectFields=year&page=1&limit=25&type=movie&type='
    'anime&type=cartoon&typeNumber=1&typeNumber=3&typeNumber=4&name='
)


request_random = 'https://api.kinopoisk.dev/v1.3/movie/random'
