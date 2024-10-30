FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y git && \
    pip install pipenv

COPY Pipfile* ./

RUN pipenv sync --dev --system

WORKDIR /sourcecode
RUN apt-get clean
RUN git config --global --add safe.directory /sourcecode
CMD ["pre-commit", "run", "--all-files"]
