from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from sqlalchemy import create_engine, or_, and_
from sqlalchemy.orm import sessionmaker, Session as SQLASession
from load_cca import (
    Base, CCA, CountyIncluded, CountyExcluded, CityIncluded, CityExcluded, ZipIncluded, ZipExcluded
)
import re
from rapidfuzz import fuzz

app = FastAPI()

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "cca")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class AddressRequest(BaseModel):
    address: str

class CCAResponse(BaseModel):
    cca_name: str
    signup_link: Optional[str]

@app.get("/")
def read_root():
    return {"message": "EcoTrove CCA API is running."}

@app.post("/eligible_ccas", response_model=List[CCAResponse])
def eligible_ccas(req: AddressRequest, db: SQLASession = Depends(get_db)):
    address = req.address.strip()
    zip_match = re.search(r"\b(\d{5})\b", address)
    zipcode = zip_match.group(1) if zip_match else None
    city_match = re.search(r"([A-Za-z\s]+),?\s*CA", address, re.IGNORECASE)
    city = city_match.group(1).strip() if city_match else None
    if not zipcode and not city:
        city = address.strip()
    ccas = db.query(CCA).all()
    eligible = []
    for cca in ccas:
        include = False
        exclude = False
        if zipcode:
            if db.query(ZipIncluded).filter_by(cca_id=cca.id, zipcode=zipcode).count() > 0:
                include = True
            if db.query(ZipExcluded).filter_by(cca_id=cca.id, zipcode=zipcode).count() > 0:
                exclude = True
        if city:
            if db.query(CityIncluded).filter(CityIncluded.cca_id==cca.id, CityIncluded.city.ilike(f"%{city}%")).count() > 0:
                include = True
            elif db.query(CityIncluded).filter(CityIncluded.cca_id==cca.id).count() > 0:
                db_cities = [row.city for row in db.query(CityIncluded).filter(CityIncluded.cca_id==cca.id)]
                for db_city in db_cities:
                    if fuzz.ratio(city.lower(), db_city.lower()) > 85:
                        include = True
                        break
            if db.query(CityExcluded).filter(CityExcluded.cca_id==cca.id, CityExcluded.city.ilike(f"%{city}%")).count() > 0:
                exclude = True
            elif db.query(CityExcluded).filter(CityExcluded.cca_id==cca.id).count() > 0:
                db_cities = [row.city for row in db.query(CityExcluded).filter(CityExcluded.cca_id==cca.id)]
                for db_city in db_cities:
                    if fuzz.ratio(city.lower(), db_city.lower()) > 85:
                        exclude = True
                        break
        if not zipcode and not city:
            continue
        if include and not exclude:
            eligible.append(CCAResponse(cca_name=cca.cca_name, signup_link=cca.signup_link))
    if not eligible:
        return []
    return eligible 