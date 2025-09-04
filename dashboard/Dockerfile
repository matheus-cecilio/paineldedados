FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir streamlit==1.38.0 pandas==2.2.2 altair==5.3.0 requests==2.32.3 plotly==5.24.1 python-dotenv==1.0.1

COPY dashboard/streamlit_app.py /app/streamlit_app.py
COPY .env.example /app/.env

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
