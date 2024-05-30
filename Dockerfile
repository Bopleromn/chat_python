FROM python

WORKDIR /app

COPY requirements.txt .
COPY src/DataBase.db .

RUN pip install -r requirements.txt

COPY . .

VOLUME [ "DataBase.db" ]

CMD ["python3", "src/main.py"]