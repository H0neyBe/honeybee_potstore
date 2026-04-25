FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HONEYBEE_POT_ID=webtrap-01 \
    HONEYBEE_HOST=127.0.0.1 \
    HONEYBEE_PORT=9100 \
    WEBTRAP_BIND_HOST=0.0.0.0 \
    WEBTRAP_BIND_PORT=8088

WORKDIR /opt/webtrap

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY webtrap ./webtrap
COPY standalone.py config.yaml ./

RUN mkdir -p /opt/webtrap/logs /opt/webtrap/captured_uploads \
    && useradd --system --uid 1001 webtrap \
    && chown -R webtrap:webtrap /opt/webtrap
USER webtrap

EXPOSE 8088

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8088", "--access-logfile", "-", "webtrap:create_app()"]
