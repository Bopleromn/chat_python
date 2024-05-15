from src import db    
from src.table_models import Users
from fastapi import Depends
from sqlalchemy.orm import Session
import csv

database: Session = next(db.get_db())

with open('scripts/users.csv', 'a', newline='') as file:
    file.truncate(0)
    
    writer = csv.DictWriter(file, fieldnames=['id', 'email', 'password', 'name', 'age', 'photo', 'last_seen'])
    writer.writeheader()
    
    for user in database.query(Users).all():
        writer.writerow({
            'id': user.id,
            'email': user.email,
            'password': user.password,
            'name': user.name,
            'age': user.age,
            'photo': user.photo,
            'last_seen': user.last_seen
        })