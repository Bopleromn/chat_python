FROM python

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

VOLUME [ "DataBase.db" ]

CMD ["python3", "src/main.py"]