import os
import pandas as pd
import ast
import re
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "cca")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

Base = declarative_base()

class CCA(Base):
    __tablename__ = 'cca'
    id = Column(Integer, primary_key=True)
    cca_name = Column(Text, nullable=False)
    is_cca = Column(Boolean, nullable=False)
    is_incumbent_utility = Column(Boolean, nullable=False)
    state = Column(Text, nullable=False)
    signup_link = Column(Text)

class CountyIncluded(Base):
    __tablename__ = 'cca_county_included'
    id = Column(Integer, primary_key=True)
    cca_id = Column(Integer, ForeignKey('cca.id', ondelete='CASCADE'))
    county = Column(Text, nullable=False)

class CountyExcluded(Base):
    __tablename__ = 'cca_county_excluded'
    id = Column(Integer, primary_key=True)
    cca_id = Column(Integer, ForeignKey('cca.id', ondelete='CASCADE'))
    county = Column(Text, nullable=False)

class CityIncluded(Base):
    __tablename__ = 'cca_city_included'
    id = Column(Integer, primary_key=True)
    cca_id = Column(Integer, ForeignKey('cca.id', ondelete='CASCADE'))
    city = Column(Text, nullable=False)

class CityExcluded(Base):
    __tablename__ = 'cca_city_excluded'
    id = Column(Integer, primary_key=True)
    cca_id = Column(Integer, ForeignKey('cca.id', ondelete='CASCADE'))
    city = Column(Text, nullable=False)

class ZipIncluded(Base):
    __tablename__ = 'cca_zip_included'
    id = Column(Integer, primary_key=True)
    cca_id = Column(Integer, ForeignKey('cca.id', ondelete='CASCADE'))
    zipcode = Column(Text, nullable=False)

class ZipExcluded(Base):
    __tablename__ = 'cca_zip_excluded'
    id = Column(Integer, primary_key=True)
    cca_id = Column(Integer, ForeignKey('cca.id', ondelete='CASCADE'))
    zipcode = Column(Text, nullable=False)

def parse_list(val):
    """Parse inconsistent JSON arrays and various formats from CSV"""
    if pd.isna(val) or val == '' or val is None:
        return []
    val = str(val).strip()
    if not val:
        return []
    # Handle single items (not in array format)
    if not val.startswith('[') and not val.endswith(']'):
        # If comma in value, split
        if ',' in val:
            return [item.strip() for item in val.split(',') if item.strip()]
        return [val.strip()]
    # Fix malformed quotes (¨ instead of ")
    val = val.replace('¨', '"')
    # Handle cases where the entire string is wrapped in quotes but contains comma-separated values
    if val.startswith('"') and val.endswith('"') and ',' in val and not val.startswith('["'):
        content = val[1:-1]
        items = [item.strip() for item in content.split(',')]
        return [item for item in items if item]
    # Handle unquoted items in brackets like [Escalon, Lodi, Manteca, Mountain House, Ripon]
    if re.match(r'^\[[^\"]+(?:,\s*[^\"]+)*\]$', val):
        content = val[1:-1]
        items = [item.strip() for item in content.split(',')]
        return [item for item in items if item]
    # Try to fix common JSON issues
    val = re.sub(r'""+', '"', val)
    val = re.sub(r'\["([^\"]*)"\s*,\s*"([^\"]*)"', r'["\1", "\2"', val)
    # Handle cases like [Apple Valley] -> ["Apple Valley"]
    if re.match(r'^\[[^\"]+\]$', val):
        item = val[1:-1].strip()
        return [item] if item else []
    try:
        fixed_val = val
        fixed_val = re.sub(r',\s*([^",\]]+)(?=,|\])', r', "\1"', fixed_val)
        fixed_val = re.sub(r'^\["([^\"]+)"', r'["\1"', fixed_val)
        result = ast.literal_eval(fixed_val)
        if isinstance(result, list):
            return [str(item).strip() for item in result if str(item).strip()]
        else:
            return [str(result).strip()]
    except (ValueError, SyntaxError):
        pass
    try:
        content = val.strip('[]')
        items = [item.strip().strip('"\'') for item in content.split(',')]
        return [item for item in items if item]
    except:
        return []

def main():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create tables if not exist
    Base.metadata.create_all(engine)

    df = pd.read_csv("cca_coverage.csv")
    for _, row in df.iterrows():
        cca = CCA(
            cca_name=row.get('cca_name'),
            is_cca=str(row.get('is_cca')).strip().upper() == 'TRUE',
            is_incumbent_utility=str(row.get('is_incumbent_utility')).strip().upper() == 'TRUE',
            state=row.get('state'),
            signup_link=row.get('signup_link')
        )
        session.add(cca)
        session.flush()  # get cca.id

        for county in parse_list(row.get('counties_included', '')):
            session.add(CountyIncluded(cca_id=cca.id, county=county))
        for county in parse_list(row.get('counties_excluded', '')):
            session.add(CountyExcluded(cca_id=cca.id, county=county))
        for city in parse_list(row.get('cities_included', '')):
            session.add(CityIncluded(cca_id=cca.id, city=city))
        for city in parse_list(row.get('cities_excluded', '')):
            session.add(CityExcluded(cca_id=cca.id, city=city))
        for zipcode in parse_list(row.get('zipcodes_included', '')):
            session.add(ZipIncluded(cca_id=cca.id, zipcode=zipcode))
        for zipcode in parse_list(row.get('zipcodes_excluded', '')):
            session.add(ZipExcluded(cca_id=cca.id, zipcode=zipcode))

    session.commit()
    session.close()
    print("Ingestion complete.")

if __name__ == "__main__":
    main() 