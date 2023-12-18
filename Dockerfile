FROM python:3.9-slim

RUN pip install "fastapi[all]"
RUN pip install fastapi-slackeventsapi
RUN pip install slack_sdk
RUN pip install requests

RUN apt-get update -y
RUN apt-get install wget -y

COPY bot.py ./
COPY scripts/* ./scripts/

ARG SLACK_BOT_TOKEN
ARG SLACK_SIGNING_SECRET
ARG WIKI_TOKEN


ENV SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN
ENV SLACK_SIGNING_SECRET=$SLACK_SIGNING_SECRET
ENV WIKI_TOKEN=$WIKI_TOKEN

ENV WIKI_GRAPHQL="https://wiki.#######.com/graphql"
ENV WIKI_REST="https://wiki.#######.com/u"
ENV WIKI_URL="https://wiki.#######.com"

ENV PYTHONUNBUFFERED=0

EXPOSE 8000:8000
CMD uvicorn bot:app --host 0.0.0.0
