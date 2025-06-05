from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime

# ==== Auth & User ==== #

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# ==== Books ==== #

class BookBase(BaseModel):
    title: str
    author: str
    publication_year: Optional[int] = None
    isbn: Optional[str] = None
    copies: int = Field(default=1, ge=0)

class BookCreate(BookBase):
    pass

class BookRead(BookBase):
    model_config = ConfigDict(from_attributes=True)

    id: int

# ==== Readers ==== #

class ReaderBase(BaseModel):
    name: str
    email: EmailStr

class ReaderCreate(ReaderBase):
    pass

class ReaderRead(ReaderBase):
    model_config = ConfigDict(from_attributes=True)

    id: int

# ==== Borrow/Return ==== #

class BorrowRequest(BaseModel):
    book_id: int
    reader_id: int

class ReturnRequest(BaseModel):
    borrow_id: Optional[int] = None
    book_id: Optional[int] = None
    reader_id: Optional[int] = None

class BorrowedBookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    reader_id: int
    borrow_date: datetime
    return_date: Optional[datetime] = None

