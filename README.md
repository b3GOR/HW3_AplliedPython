## Описание API

Данный сервис призван сокращать ссылки. 

Сервис развернут на удаленном хосте с помощью **docker-compose**


![](https://github.com/b3GOR/HW3_AplliedPython/blob/main/img/deploy.png)


## Функционал

1. **Создание / удаление / изменение / получение информации по короткой ссылке:**
  - `POST /links/shorten` – создает короткую ссылку.
  - `GET /links/{short_code}` – перенаправляет на оригинальный URL.
  - `DELETE /links/{short_code}` – удаляет связь.
  - `PUT /links/{short_code}` – обновляет короткую ссылку.
2. **Статистика по ссылке:**
  - `GET /links/{short_code}/stats`
  - Отображает оригинальный URL, возвращает дату создания, количество переходов, дату последнего использования.
3. **Создание кастомных ссылок (уникальный alias):**
  - `POST /links/shorten` (с передачей `custom_alias`).
  - `alias` проверяется на уникальность.
4. **Указание времени жизни ссылки:**
  - `POST /links/shorten` (создается с параметром `expires_at` в формате даты).
5. **Регистрация**

Создана ручка регистрации и авторизации пользователей при помощи **fastapi.security** , **passlib.context**  и **jose**


## Инструкция по запуску

Клонируйте репозиторий к себе на ПК
```sh
git clone https://github.com/b3GOR/HW3_AplliedPython.git
```
### Запуск через через docker-контейнер
Зайдите в терминал, в папке проекта и запустите следующую команду

```sh
docker compose up  --build -d
```

API  работает по адресу http://0.0.0.0:8001/docs

### Запуск через main.py

Поставьте виртуальное окружение и активируйте его

```sh
python -m venv .venv
```

* Также установите PostgreSQL и Redis

Скачайте необходимые зависимости 

```sh
pip install -r requirements.txt
```

Для начала работы веб-сервиса с API, запустите файл **main.py**
API  работает по адресу http://127.0.0.1:8000/docs

## Описание БД
База данный состоит из **PostgreSQL** (для основного хранения) и **Redis** (кэширование наиболее часто используемых ссылок, для более быстрого доступа к ним) 

###  PostgreSQL

Взаимодействие с БД происходить через **SQLAlchemy** при помощи **psycopg2**.
Всего в БД 3 таблицы:

![](https://github.com/b3GOR/HW3_AplliedPython/blob/main/img/db.png)

* **links** - здесь храняться ссылки и их укороченная версия
    * *short_code* - укороченная часть ссылки
    * *original_url* - оригинальная ссылка, которую пользователь захотел преобразовать в короткую версию
    * *created_at* - дата и время создание укороченной ссылки
    * *expires_at* - время сущестовоания ссылки (после него укороченная и оригинальная ссылка удаляются из БД)
    * *user_id* - id пользователя (нужен для првоерки прав работы с ссылкой (может ли он ее изменять/удалять или нет))
* **links_stats** - хранение статистики использование ссылок
    * *short_link* - укороченная часть ссылки
    * *access_count* - количество раз, когда ссылка использовалась (нужно для добавление в Redis)
    * *last_access* -  дата и время, когда ссылка последний раз использовалась
* **users** - хранение данных о зарегистрировавшихся пользователях
    * *email* - электронная почта пользователя
    * *username* - имя, выбранное пользователем
    * *hashed_password* - значение, которое получается при хэшировании пароля пользователя
    * *is_active* - существование учетной записи пользователя (удалена или нет)

### Redis

В кэше храняться 5 наиболее используемых ссылок (количество переходов по ним). С помощью **APScheduler** реализовано периодическое обновление кэша, а также удаление ссылок с истекшим сроком жизни



