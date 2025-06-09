from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    publication_year = Column(Integer)
    isbn = Column(String, unique=True)
    copies = Column(Integer, default=1)
    # second alembic migration addition
    description = Column(String, nullable=True)

    borrows = relationship("BorrowedBook", back_populates="book")


class Reader(Base):
    __tablename__ = "readers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)

    borrows = relationship("BorrowedBook", back_populates="reader")


class BorrowedBook(Base):
    __tablename__ = "borrowed_books"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index = True)
    reader_id = Column(Integer, ForeignKey("readers.id"), nullable=False, index = True)
    borrow_date = Column(DateTime(timezone=True), server_default=func.now())
    return_date = Column(DateTime(timezone=True), nullable=True)

    book = relationship("Book", back_populates="borrows")
    reader = relationship("Reader", back_populates="borrows")

    # Enforce "return_date" uq so that the same reader can borrow the same book multiple times
    __table_args__ = (
        UniqueConstraint('book_id', 'reader_id', 'return_date', name='uq_borrow_unique_active'),
    )