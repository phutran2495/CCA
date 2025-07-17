import os
import tempfile
import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from load_cca import Base, CCA, CountyIncluded, CityIncluded, ZipIncluded, parse_list

def test_parse_list_handles_json_and_csv():
    assert parse_list('["A", "B"]') == ["A", "B"]
    assert parse_list('A,B') == ["A", "B"]
    assert parse_list('') == []
    assert parse_list(None) == []
    assert parse_list('[1,2]') == ["1", "2"]  # Expect strings

def test_ingestion_creates_cca_and_relations():
    # Use a temp SQLite DB
    db_fd, db_path = tempfile.mkstemp()
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    # Simulate a row
    cca = CCA(cca_name="Test CCA", is_cca=True, is_incumbent_utility=False, state="CA", signup_link="http://test.com")
    session.add(cca)
    session.flush()
    session.add(CountyIncluded(cca_id=cca.id, county="Test County"))
    session.add(CityIncluded(cca_id=cca.id, city="Test City"))
    session.add(ZipIncluded(cca_id=cca.id, zipcode="12345"))
    session.commit()
    assert session.query(CCA).count() == 1
    assert session.query(CountyIncluded).count() == 1
    assert session.query(CityIncluded).count() == 1
    assert session.query(ZipIncluded).count() == 1
    session.close()
    os.close(db_fd)
    os.unlink(db_path) 