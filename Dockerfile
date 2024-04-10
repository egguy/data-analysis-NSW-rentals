FROM python:3.12-slim

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN --mount=type=cache,target=/root/.cache pip install uv
RUN --mount=type=cache,target=/root/.cache uv pip install --system -r requirements.txt

COPY visualisation visualisation
COPY rentals.duckdb rentals.duckdb

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "visualisation/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
