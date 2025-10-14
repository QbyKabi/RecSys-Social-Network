from database import Base, SessionLocal
from sqlalchemy import Column, Integer, String
from sqlalchemy import func, select, desc
from typing import Tuple

class User(Base):
    __tablename__ = "user"
    age = Column(Integer)
    city = Column(String)
    country = Column(String)
    exp_group = Column(Integer)
    gender = Column(Integer)
    id = Column(Integer, primary_key = True)
    os = Column(String)
    source = Column(String)

db = SessionLocal()

if __name__ == "__main__":
    res = []
    for user in (db.query(User.country, User.os, func.count().label('count'))
                   .filter(User.exp_group == 3)
                   .group_by(User.country, User.os)
                   .having(func.count() > 100)
                   .order_by(desc(func.count())).all()):
        res.append((user.country, user.os, user.count))
    print(res)









