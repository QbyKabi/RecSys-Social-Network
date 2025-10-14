from database import Base, SessionLocal
from sqlalchemy import Column, Integer, String, desc


class Post(Base):
    __tablename__ = "post"
    id = Column(Integer, primary_key = True)
    text = Column(String)
    topic = Column(String)


if __name__ == "__main__":
    db = SessionLocal()
    result = []
    for post in (db.query(Post).filter(Post.topic == "business").order_by(Post.id.desc()).limit(10).all()):
        result.append(post.id)
    print(result)
