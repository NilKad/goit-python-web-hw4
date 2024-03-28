# Docker-команда FROM вказує базовий образ контейнера
# Наш базовий образ - це Linux з попередньо встановленим python
FROM python:3.12-slim

RUN pip install poetry

# Встановимо змінну середовища
ENV APP_HOME /app

# Встановимо робочу директорію всередині контейнера
WORKDIR $APP_HOME

COPY pyproject.toml poetry.lock /app/

# Устанавливаем зависимости с помощью Poetry
# RUN poetry install --no-dev
RUN poetry config virtualenvs.create false && poetry install --only main

# Скопіюємо інші файли в робочу директорію контейнера
COPY . /app

# Встановимо залежності всередині контейнера
# RUN pip install -r requirements.txt

# Позначимо порт, де працює застосунок всередині контейнера
EXPOSE 3000
# Запустимо наш застосунок всередині контейнера
CMD ["python", "main.py"]