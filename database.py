from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# SQLALCHEMY_DATABASE_URL = 'mysql+pymysql://root:123456@127.0.0.1:3306/tododatabase'
SQLALCHEMY_DATABASE_URL = 'sqlite:///./todosapp.db'

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
'''
This is the **parent class** all your database models (tables) will inherit from.
 When you create a `Todo` table later, you'll write `class Todo(Base)` — this is where
that `Base` comes from.
---
### 🗺️ The Big Picture
Your Python Code
      ↓
  SessionLocal  ←── your workspace for DB operations
      ↓
    Engine      ←── the actual connection
      ↓
   todos.db     ←── your SQLite database file
'''