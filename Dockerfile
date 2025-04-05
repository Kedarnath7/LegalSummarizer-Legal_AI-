FROM python:3.9

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000 8501

CMD ["bash", "-c", "python app.py & streamlit run testing.py --server.port 8501 --server.address 0.0.0.0"]
