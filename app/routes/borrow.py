from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.database import get_db
from app.models.models import Book, Reader, BorrowedBook
from app.schemas.schemas import BorrowRequest, ReturnRequest, BorrowedBookRead, ReaderCreate
from app.dependencies.dependencies import get_current_user

router = APIRouter()

@router.post("/borrow", response_model=BorrowedBookRead)
def borrow_book(request: BorrowRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    book = db.query(Book).filter(Book.id == request.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book.copies <= 0:
        raise HTTPException(status_code=400, detail="No copies available")

    reader = db.query(Reader).filter(Reader.id == request.reader_id).first()
    if not reader:
        raise HTTPException(status_code=404, detail="Reader not found")

    active_borrows = db.query(BorrowedBook).filter(
        BorrowedBook.reader_id == reader.id,
        BorrowedBook.return_date == None
    ).count()
    if active_borrows >= 3:
        raise HTTPException(status_code=400, detail="Reader has already borrowed 3 books")

    borrowed = BorrowedBook(
        book_id=book.id,
        reader_id=reader.id,
        borrow_date=datetime.now()
    )
    book.copies -= 1
    db.add(borrowed)
    db.commit()
    db.refresh(borrowed)
    return borrowed

@router.get("/borrow/{reader_id}", response_model=List[BorrowedBookRead])
def get_active_borrows_by_reader(reader_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    borrows = db.query(BorrowedBook).filter(
        BorrowedBook.reader_id == reader_id,
        BorrowedBook.return_date == None
    ).all()
    return borrows


@router.post("/return", response_model=BorrowedBookRead)
def return_book(request: ReturnRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if request.borrow_id:
        borrow = db.query(BorrowedBook).filter(BorrowedBook.id == request.borrow_id).first()
    elif request.book_id and request.reader_id:
        borrow = db.query(BorrowedBook).filter(
            BorrowedBook.book_id == request.book_id,
            BorrowedBook.reader_id == request.reader_id,
            BorrowedBook.return_date == None
        ).first()
    else:
        raise HTTPException(status_code=400, detail="Invalid return request")

    if not borrow or borrow.return_date is not None:
        raise HTTPException(status_code=404, detail="Borrow record not found or already returned")

    borrow.return_date = datetime.now()
    book = db.query(Book).filter(Book.id == borrow.book_id).first()
    if book:
        book.copies += 1
    db.commit()
    db.refresh(borrow)
    return borrow

@router.post("/readers")
def create_reader(reader: ReaderCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if db.query(Reader).filter(Reader.email == reader.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    db_reader = Reader(**reader.model_dump())
    db.add(db_reader)
    db.commit()
    db.refresh(db_reader)
    return db_reader