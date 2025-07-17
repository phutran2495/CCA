from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from sqlalchemy import create_engine, or_, and_
from sqlalchemy.orm import sessionmaker, Session as SQLASession
from load_cca import (
    Base,
    CCA,
    CountyIncluded,
    CountyExcluded,
    CityIncluded,
    CityExcluded,
    ZipIncluded,
    ZipExcluded,
)
import re
from rapidfuzz import fuzz
import csv
from functools import lru_cache

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


USCITIES_CSV_PATH = os.path.join(os.path.dirname(__file__), "uscities.csv")


@lru_cache(maxsize=1)
def load_city_zip_mappings():
    city_state_to_zips = {}
    zip_to_city_state = {}
    with open(USCITIES_CSV_PATH, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            city = row["city_ascii"].strip()
            state = row["state_id"].strip()
            zips = row["zips"].strip().split()
            key = (city.lower(), state)
            if key not in city_state_to_zips:
                city_state_to_zips[key] = set()
            city_state_to_zips[key].update(zips)
            for z in zips:
                zip_to_city_state[z] = (city, state)
    return city_state_to_zips, zip_to_city_state


def get_zips_for_city_state(city, state):
    city_state_to_zips, _ = load_city_zip_mappings()
    return city_state_to_zips.get((city.lower(), state), set())


def get_city_state_for_zip(zipcode):
    _, zip_to_city_state = load_city_zip_mappings()
    return zip_to_city_state.get(zipcode)


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
    state = "CA"  # Default for now, can be improved for other states
    # If only a ZIP is provided, try to get city/state from mapping
    if zipcode and not city:
        city_state = get_city_state_for_zip(zipcode)
        if city_state:
            city, state = city_state
    # If only a city is provided, try to get ZIPs from mapping
    if city and not zipcode:
        zips = get_zips_for_city_state(city, state)
        # Use the first ZIP as a proxy for matching, or all for inclusion
        zipcode = next(iter(zips), None) if zips else None
    if not zipcode and not city:
        city = address.strip()
    ccas = db.query(CCA).all()
    eligible = []
    for cca in ccas:
        include = False
        exclude = False
        if zipcode:
            if (
                db.query(ZipIncluded).filter_by(cca_id=cca.id, zipcode=zipcode).count()
                > 0
            ):
                include = True
            if (
                db.query(ZipExcluded).filter_by(cca_id=cca.id, zipcode=zipcode).count()
                > 0
            ):
                exclude = True
        if city:
            if (
                db.query(CityIncluded)
                .filter(
                    CityIncluded.cca_id == cca.id, CityIncluded.city.ilike(f"%{city}%")
                )
                .count()
                > 0
            ):
                include = True
            elif (
                db.query(CityIncluded).filter(CityIncluded.cca_id == cca.id).count() > 0
            ):
                db_cities = [
                    row.city
                    for row in db.query(CityIncluded).filter(
                        CityIncluded.cca_id == cca.id
                    )
                ]
                for db_city in db_cities:
                    if fuzz.ratio(city.lower(), db_city.lower()) > 85:
                        include = True
                        break
            if (
                db.query(CityExcluded)
                .filter(
                    CityExcluded.cca_id == cca.id, CityExcluded.city.ilike(f"%{city}%")
                )
                .count()
                > 0
            ):
                exclude = True
            elif (
                db.query(CityExcluded).filter(CityExcluded.cca_id == cca.id).count() > 0
            ):
                db_cities = [
                    row.city
                    for row in db.query(CityExcluded).filter(
                        CityExcluded.cca_id == cca.id
                    )
                ]
                for db_city in db_cities:
                    if fuzz.ratio(city.lower(), db_city.lower()) > 85:
                        exclude = True
                        break
        if not zipcode and not city:
            continue
        if include and not exclude:
            eligible.append(
                CCAResponse(cca_name=cca.cca_name, signup_link=cca.signup_link)
            )
    if not eligible:
        return []
    return eligible
