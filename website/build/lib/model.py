from typing import List
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src import db
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    email: Mapped[str] = mapped_column(db.String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(db.String, unique=True, nullable=False)

    def __repr__(self):
        return '<User {}>'.format(self.email)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Pasta(db.Model):
    __tablename__ = 'pasta'
    pasta_id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    brand: Mapped[str] = mapped_column(db.String, nullable=False)
    specific_pasta: Mapped[int] = mapped_column(db.Integer, nullable=False)
    
    # One-to-many relationship with SalesRecord
    sales_records: Mapped[List['SalesRecord']] = relationship("SalesRecord", back_populates="pasta")


class SalesRecord(db.Model):
    __tablename__ = 'sales_record'
    sales_id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    date: Mapped[db.Date] = mapped_column(db.Date, nullable=False)
    quantity: Mapped[int] = mapped_column(db.Integer, nullable=False)
    is_promotion: Mapped[int] = mapped_column(db.Integer, nullable=False)
    season: Mapped[str] = mapped_column(db.String, nullable=False)
    pasta_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('pasta.pasta_id'), nullable=False)

    # Many-to-one relationship with Pasta
    pasta: Mapped[Pasta] = relationship("Pasta", back_populates="sales_records")    

    