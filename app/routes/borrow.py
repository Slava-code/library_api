from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.models import Book, Reader, BorrowedBook
from app.schemas.schemas import BorrowRequest, ReturnRequest, BorrowedBookRead
from app.dependencies.dependencies import get_current_user

router = APIRouter()

@router.post("/borrow", response_model=BorrowedBookRead)
def borrow_book(
    request: BorrowRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
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


@router.post("/return", response_model=BorrowedBookRead)
def return_book(
    request: ReturnRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
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

    if not borrow:
        raise HTTPException(status_code=404, detail="Borrow record not found or already returned")

    borrow.return_date = datetime.utcnow()
    book = db.query(Book).filter(Book.id == borrow.book_id).first()
    if book:
        book.copies += 1
    db.commit()
    db.refresh(borrow)
    return borrow
