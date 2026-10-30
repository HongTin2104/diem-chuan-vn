FROM python:3.12-slim

RUN useradd -m app
WORKDIR /home/app/diem-chuan-vn
COPY --chown=app pyproject.toml README.md ./
COPY --chown=app src ./src
RUN pip install --no-cache-dir ".[app]"
COPY --chown=app data ./data
COPY --chown=app app ./app
COPY --chown=app .streamlit ./.streamlit

USER app
ENV DIEM_CHUAN_DATA=/home/app/diem-chuan-vn/data
EXPOSE 8501
CMD ["streamlit", "run", "app/app.py", "--server.address=0.0.0.0", "--server.headless=true"]
