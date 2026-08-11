FROM python:3.12 AS base

ENV VIRTUAL_ENV=/app/.venv \
  PATH="/app/.venv/bin:$PATH"


FROM base AS runtime

ENV POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_IN_PROJECT=1 \
  POETRY_VIRTUALENVS_CREATE=1 \
  POETRY_CACHE_DIR=/tmp/poetry_cache

# Install system dependencies if needed
RUN apt-get update \
  && apt-get install -y --no-install-recommends curl build-essential \
  && rm -rf /var/lib/apt/lists/*

# Install Poetry
WORKDIR /app
RUN pip install --no-cache-dir poetry==2.4.1
# Install packages
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root && \
  rm -rf ${POETRY_CACHE_DIR} 

# Copy the application code
COPY . .

# Expose the port your app runs on
ENV PORT=8080
EXPOSE $PORT

# Healthcheck!
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run the app
ENTRYPOINT ["poetry", "run", "streamlit", "run", "./website.py", "--server.port=8080", "--server.address=0.0.0.0"]
