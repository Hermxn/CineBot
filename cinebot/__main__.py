import datetime
import time
import urllib.parse

import requests
import sqlalchemy
import telebot
from sqlalchemy import create_engine, orm

from cinebot import classes, config, models, urls


bot = telebot.TeleBot(config.BOT_TOKEN, parse_mode=None)
engine = create_engine(config.POSRGRES_URL, echo=True)
api_header = {'X-API-KEY': f'{config.API_TOKEN}'}


@bot.message_handler(commands=['start'])
def user_to_db(message: telebot.types.Message) -> None:
    telegram_id = message.from_user.id
    with sqlalchemy.orm.Session(bind=engine, expire_on_commit=False) as session:
        user: models.User | None = (
            session.query(models.User)
            .filter(models.User.telegram_id == telegram_id)
            .first()
        )
        if user is None:
            user = models.User(
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                telegram_id=telegram_id,
                username=message.from_user.username,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            bot.reply_to(
                message,
                f'Привет {user.first_name}! Бот Cinetrack может показывать информацию по твоим любимомым '
                f'фильмам, а также добавлять их в список избранного. Для более подробной информации'
                f'выбери комманду из списка в меню.',
            )
        else:
            bot.reply_to(
                message,
                'Бот уже запущен. Выбери нужную команду для продолжения.',
            )


@bot.message_handler(commands=['info'])
def command_info(message: telebot.types.Message) -> None:
    bot.reply_to(message, 'Какой фильм ищешь?')
    bot.register_next_step_handler_by_chat_id(
        chat_id=message.chat.id, callback=get_movie_info
    )


def get_movie_info(message: telebot.types.Message, **dict_of_movies_id: dict) -> None:
    message.chat.description = 'info'
    movie_id = None
    if message.text in dict_of_commands:
        exit_from_loop(message)
        return
    elif message.text.isdigit():
        try:
            movie_id = str(dict_of_movies_id['dict_of_movies_id'])
        except KeyError:
            bot.reply_to(
                message,
                'Не удалось найти информацию по этому фильму. Проверь введённое название и попробуй снова.',
            )
    else:
        movie_id = str(movie_id_request(message))
    if movie_id is not None:
        request = requests.get(
            urls.request_info + movie_id,
            headers=api_header,
        )
        respond = request.json()
        movie = classes.MovieReleased.from_dict_released(respond['docs'][0])
        fee_str = str(movie.fees_value)[::-1]
        movie.fees_value = ' '.join(
            fee_str[i : i + 3] for i in range(0, len(fee_str), 3)
        )[::-1]
        text_to_render = (
            f'Фильм: {movie.name}\n\n'
            f'Год релиза: {movie.released_year}\n'
            f'Рейтинг IMDB: {movie.rating_imdb if movie.rating_imdb else "отсутствует"}\n'
            f'Рейтинг Кинопоиск: {movie.rating_kp if movie.rating_kp else "отсутствует"}\n'
            f'Мировые сборы: {movie.fees_value if movie.fees_value else "нет информации"} {movie.fees_currency}\n\n'
            f'{movie.description if movie.description else ""}'
        )
        if movie.poster:
            bot.send_photo(
                chat_id=message.chat.id, photo=movie.poster, caption=text_to_render
            )
        else:
            bot.send_message(chat_id=message.chat.id, text=text_to_render)


@bot.message_handler(commands=['add'])
def command_add(message: telebot.types.Message) -> None:
    bot.reply_to(message, 'Какой фильм добавить в избранное?')
    bot.register_next_step_handler_by_chat_id(
        chat_id=message.chat.id, callback=add_movie_to_db
    )


def add_movie_to_db(message: telebot.types.Message, **id_name_dict: dict) -> None:
    message.chat.description = 'add'
    if message.text in dict_of_commands:
        exit_from_loop(message)
        return
    elif message.text.isdigit():
        movie_id = id_name_dict['selected_id']
        name = id_name_dict['selected_name']
    else:
        movie_id = movie_id_request(message)
        name = message.text
    with sqlalchemy.orm.Session(bind=engine, expire_on_commit=False) as session:
        movie: models.Follows | None = (
            session.query(models.Follows)
            .filter(
                models.Follows.movie_id == movie_id,
                models.Follows.user_telegram_id == message.from_user.id,
            )
            .first()
        )
        if movie is None:
            movie = models.Follows(
                user_telegram_id=message.from_user.id,
                movie_id=movie_id,
                movie_name=name,
            )
            session.add(movie)
            session.commit()
            session.refresh(movie)
            bot.reply_to(
                message,
                f'Есть! Фильм "{movie.movie_name}" добавлен в список отслеживания.',
            )
        else:
            bot.reply_to(
                message,
                f'Фильм "{movie.movie_name}" уже добавлен в список отслеживания.',
            )


@bot.message_handler(commands=['del'])
def command_del(message: telebot.types.Message) -> None:
    movies = list_of_follows(message)
    if len(movies) == 0:
        bot.send_message(message.chat.id, "Твой список избранного пуст.")
    else:
        movies_list = '\n'.join(
            f'{index} - {movies[index]}' for index in sorted(movies)
        )
        bot.reply_to(
            message,
            f'Твой список избранного:\n\n{movies_list}\n\nКакой фильм удалить из избранного?',
        )
        bot.register_next_step_handler_by_chat_id(
            message.chat.id,
            callback=del_movie_from_db,
            dict_of_movies=movies,
        )


def del_movie_from_db(message: telebot.types.Message, **dict_of_movies: dict) -> None:
    if message.text in dict_of_commands:
        exit_from_loop(message)
        return
    else:
        with sqlalchemy.orm.Session(bind=engine, expire_on_commit=False) as session:
            if message.text.isdigit():
                try:
                    select = dict_of_movies['dict_of_movies'][int(message.text)]
                except KeyError:
                    bot.reply_to(
                        message,
                        'Фильма под таким номером нет в списке. Попробуй ещё раз.',
                    )
                    bot.register_next_step_handler(
                        message,
                        lambda message: del_movie_from_db(
                            message, dict_of_movies=dict_of_movies
                        ),
                    )
                movie = (
                    session.query(models.Follows)
                    .filter(
                        models.Follows.movie_name == select,
                        models.Follows.user_telegram_id == message.from_user.id,
                    )
                    .first()
                )
            else:
                movie = (
                    session.query(models.Follows)
                    .filter(
                        models.Follows.movie_name == message.text.strip(),
                        models.Follows.user_telegram_id == message.from_user.id,
                    )
                    .first()
                )
            try:
                movie_name = movie.__getattribute__('movie_name')
            except AttributeError:
                bot.reply_to(
                    message, 'Фильма с таким названием нет в списке. Попробуй ещё раз.'
                )
                bot.register_next_step_handler(
                    message,
                    lambda message: del_movie_from_db(
                        message, dict_of_movies=dict_of_movies
                    ),
                )
            session.delete(movie)
            session.commit()
            dict_of_follows = list_of_follows(message)
            list_of_movies = '\n'.join(
                f'{index} - {dict_of_follows[index]}'
                for index in sorted(dict_of_follows)
            )
            bot.reply_to(message, f"Фильм '{movie_name}' удалён из избранного.")
            time.sleep(1.0)
            if len(dict_of_follows) == 0:
                bot.send_message(message.chat.id, "Твой список избранного пуст.")
            else:
                bot.send_message(
                    message.chat.id, f"Твой список избранного:\n\n{list_of_movies}"
                )


@bot.message_handler(commands=['month'])
def command_month(message: telebot.types.Message):
    release_month_data(message)
    bot.reply_to(
        message,
        'Если хочешь добавить фильм в список избранного - выбери команду /add в меню.',
    )


def release_month_data(message: telebot.types.Message):
    response = requests.get(urls.request_release_month, headers=api_header)
    data = response.json()
    release_list(message, data['docs'])


@bot.message_handler(commands=['year'])
def command_year(message: telebot.types.Message):
    release_year_data(message)
    bot.reply_to(
        message,
        'Если хочешь добавить фильм в список избранного - выбери команду /add в меню.',
    )


def release_year_data(message: telebot.types.Message):
    response = requests.get(urls.request_release_year, headers=api_header)
    data = response.json()
    release_list(message, data['docs'])


@bot.message_handler(commands=['show'])
def command_show(message: telebot.types.Message):
    movies = list_of_follows(message)
    if len(movies) == 0:
        bot.send_message(message.chat.id, "Твой список избранного пуст.")
    else:
        list_of_movies = '\n'.join(
            f'{index} - {movies[index]}' for index in sorted(movies)
        )
        bot.send_message(
            message.chat.id, f'Твой список избранного:\n\n{list_of_movies }'
        )


def list_of_follows(message: telebot.types.Message) -> dict:
    dict_to_user = {}
    with sqlalchemy.orm.Session(bind=engine, expire_on_commit=False) as session:
        movies = (
            session.query(models.Follows)
            .filter(models.Follows.user_telegram_id == message.from_user.id)
            .all()
        )
        for index, movie in enumerate(movies):
            dict_to_user[index + 1] = movie.movie_name
    return dict_to_user


def movie_id_request(message: telebot.types.Message) -> int:
    if message.text in dict_of_commands:
        exit_from_loop(message)
        return
    else:
        movie_name_decode = urllib.parse.quote_plus(message.text)
        request = requests.get(
            urls.request_id + str(movie_name_decode),
            headers=api_header,
        )
        respond = request.json()
        if request.status_code == 200 and len(respond['docs']) == 1:
            return respond['docs'][0]['id']
        elif request.status_code == 200 and len(respond['docs']) > 1:
            list_of_movies_ids = []
            dict_of_movies_ids = {}
            count = 0
            for item in range(len(respond['docs'])):
                name = (
                    respond['docs'][item]['name']
                    .capitalize()
                    .startswith(message.text.capitalize())
                )
                if name is True:
                    count += 1
                    data = (
                        str(count)
                        + ' - '
                        + respond['docs'][item]['name']
                        + ', Год: '
                        + str(respond['docs'][item]['year'])
                    )
                    list_of_movies_ids.append(data)
                    dict_of_movies_ids[count] = [
                        respond['docs'][item]['id'],
                        respond['docs'][item]['name'],
                    ]
            reply = '\n'.join(item for item in list_of_movies_ids)
            bot.reply_to(
                message,
                f'По запросу найдены следующие фильмы:\n\n{reply}\n\nВыбери номер нужного фильма.',
            )
            bot.register_next_step_handler_by_chat_id(
                chat_id=message.chat.id,
                callback=select_by_user,
                dict_of_movies_ids=dict_of_movies_ids,
                chat_description=message.chat.description,
            )
        else:
            bot.reply_to(
                message,
                'Не удалось найти информацию по этому фильму. Проверь введённое название и попробуй снова.',
            )


def release_list(message: telebot.types.Message, list_of_movies: list):
    for index in range(len(list_of_movies)):
        try:
            movie = classes.MovieInProduction.from_dict_in_production(
                list_of_movies[index]
            )
        except KeyError:
            continue
        if movie.name is None and movie.name_en is None:
            continue
        movie.premiere_date = (
            datetime.datetime.strptime(movie.premiere_date, '%Y-%m-%dT%H:%M:%S.%f%z')
            .date()
            .__format__('%d.%m.%Y')
        )
        text_to_render = (
            f'Фильм: {movie.name if movie.name is not None else movie.name_en}\n\n'
            f'Рейтинг ожидания: {movie.awaiting_rating} из 100 на основании '
            f'голосов {movie.awaiting_votes} пользователей\n\n'
            f'Дата выхода: {movie.premiere_date}\n\n'
            f'{movie.description if movie.description else ""}'
        )
        if movie.poster:
            bot.send_photo(
                chat_id=message.chat.id, photo=movie.poster, caption=text_to_render
            )
            time.sleep(1.5)
        else:
            bot.send_message(chat_id=message.chat.id, text=text_to_render)
            time.sleep(1.5)


def select_by_user(
    message: telebot.types.Message,
    dict_of_movies_ids: dict,
    chat_description: str,
):
    if message.text in dict_of_commands:
        exit_from_loop(message)
        return
    elif not message.text.isdigit() and message.text not in dict_of_commands:
        bot.reply_to(message, 'Некорректный номер. Введите число из списка.')
        bot.register_next_step_handler(
            message,
            lambda message: select_by_user(
                message, dict_of_movies_ids, chat_description
            ),
        )
        return
    try:
        selected_id = dict_of_movies_ids[int(message.text)][0]
        selected_name = dict_of_movies_ids[int(message.text)][1]
        if chat_description == 'info':
            get_movie_info(message=message, dict_of_movies_id=selected_id)
        elif chat_description == 'add':
            add_movie_to_db(
                message=message, selected_id=selected_id, selected_name=selected_name
            )
    except KeyError:
        bot.reply_to(message, 'Такого номера нет в списке, попробуй ещё раз')
        bot.register_next_step_handler(
            message,
            lambda message: select_by_user(
                message, dict_of_movies_ids, chat_description
            ),
        )


@bot.message_handler(commands=['drop'])
def command_drop(message: telebot.types.Message):
    command_show(message)
    bot.send_message(message.chat.id, "Для удаления списка избранного - набери 'Да'")
    bot.register_next_step_handler_by_chat_id(
        message.chat.id, callback=delete_table_follows
    )


def delete_table_follows(message: telebot.types.Message):
    if message.text in dict_of_commands:
        exit_from_loop(message)
        return
    elif message.text in ['Да', 'да']:
        with sqlalchemy.orm.Session(bind=engine, expire_on_commit=False) as session:
            follows = (
                session.query(models.Follows)
                .filter(models.Follows.user_telegram_id == message.from_user.id)
                .all()
            )
            for item in follows:
                session.delete(item)
            session.commit()
            bot.reply_to(message, 'Готово! Твой список избранного очищен')
    elif message.text not in dict_of_commands:
        bot.reply_to(message, "Для очистки списка избранного - набери 'Да'")
        bot.register_next_step_handler(callback=delete_table_follows, message=message)


@bot.message_handler(commands=['random'])
def command_random(message: telebot.types.Message):
    request = requests.get(
        urls.request_random,
        headers=api_header,
    )
    respond = request.json()
    movie = classes.MovieReleased.from_dict_released(respond)
    fee_str = str(movie.fees_value)[::-1]
    movie.fees_value = ' '.join(fee_str[i : i + 3] for i in range(0, len(fee_str), 3))[
        ::-1
    ]
    text_to_render = (
        f'Фильм: {movie.name}\n\n'
        f'Год релиза: {movie.released_year}\n'
        f'Рейтинг IMDB: {movie.rating_imdb if movie.rating_imdb else "отсутствует"}\n'
        f'Рейтинг Кинопоиск: {movie.rating_kp if movie.rating_kp else "отсутствует"}\n'
        f'Мировые сборы: {movie.fees_value if movie.fees_value  else "нет информации"} {movie.fees_currency}\n\n'
        f'{movie.description if movie.description else ""}'
    )
    if movie.poster:
        bot.send_photo(
            chat_id=message.chat.id, photo=movie.poster, caption=text_to_render
        )
    else:
        bot.send_message(chat_id=message.chat.id, text=text_to_render)


def exit_from_loop(message: telebot.types.Message):
    func = dict_of_commands[message.text]
    return func(message)


dict_of_commands = {
    '/info': command_info,
    '/add': command_add,
    '/del': command_del,
    '/show': command_show,
    '/drop': command_drop,
    '/month': release_month_data,
    '/year': release_year_data,
    '/random': command_random,
}


models.Base.metadata.create_all(bind=engine)

bot.infinity_polling()
