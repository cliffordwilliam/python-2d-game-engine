# options: dev, prod
ARG BUILD_DEPENDENCIES=dev
ARG BUILD_PYTHON_VERSION=3.12.3

# Base image for production
FROM python:${BUILD_PYTHON_VERSION}-slim as base-prod

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install --no-install-recommends --no-install-suggests -y \
    build-essential \
    curl \
    git \
    python3-dev \
    libglib2.0-0 \
    libx11-6 \
    libxext6 \
    libxi6 \
    libsm6 \
    libxrender1 \
    libxrandr2 \
    x11-xserver-utils \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /var/cache/apt/*

# set up poetry
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

# install poetry
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH" \
    POETRY_VERSION=1.8.3 \
    POETRY_DYNAMIC_VERSIONING_PLUGIN_VERSION=1.2.0 \
    POETRY_DYNAMIC_VERSIONING_COMMANDS=version,build,publish

ARG BUILD_POETRY_CACHE_DIR=/cache/.pypoetry
RUN mkdir -p "$POETRY_HOME" "$PYSETUP_PATH" "$BUILD_POETRY_CACHE_DIR" \
    && curl -sSL https://install.python-poetry.org | python - \
    && poetry config virtualenvs.create false \
    && poetry config cache-dir $BUILD_POETRY_CACHE_DIR \
    && python -m pip install --upgrade pip wheel setuptools \
    && poetry self add "poetry-dynamic-versioning[plugin]=$POETRY_DYNAMIC_VERSIONING_PLUGIN_VERSION" \
    && poetry self add keyrings.google-artifactregistry-auth

# Set the working directory in the container
WORKDIR /app

COPY pyproject.toml poetry.lock ./

# install main dependencies
RUN --mount=type=cache,target=/cache/poetry \
    poetry install --no-root --only main --all-extras

# Base image for development
FROM base-prod as base-dev

# install dev dependencies
RUN --mount=type=cache,target=/cache/poetry \
    poetry install --no-root --all-extras

# Select the final stage based on BUILD_DEPENDENCIES argument
FROM base-${BUILD_DEPENDENCIES} as final

# Copy the entire project into the container at /app
COPY . .

# Set the display environment variable for X11 forwarding
ENV DISPLAY=:0

ARG POETRY_DYNAMIC_VERSIONING_BYPASS

RUN poetry dynamic-versioning && poetry install --only-root --all-extras

