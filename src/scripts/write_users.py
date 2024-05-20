import db
from table_models import Users
from fastapi import Depends
from sqlalchemy.orm import Session
import csv

database: Session = next(db.get_db())

with open('scripts/users.csv', 'r') as file:
    reader = csv.DictReader(file)

    for row in reader:
        user = Users(**row)
        database.add(user)

    database.commit()
