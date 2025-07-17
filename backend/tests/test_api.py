import pytest
from fastapi.testclient import TestClient
from app import app, get_db
from load_cca import Base, CCA, CityIncluded, ZipIncluded
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

client = TestClient(app)

@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(
        'sqlite:///:memory:',
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture(autouse=True)
def override_get_db(db_engine):
    TestingSessionLocal = sessionmaker(bind=db_engine)
    session = TestingSessionLocal()
    session.query(ZipIncluded).delete()
    session.query(CityIncluded).delete()
    session.query(CCA).delete()
    cca = CCA(cca_name="Test CCA", is_cca=True, is_incumbent_utility=False, state="CA", signup_link="http://test.com")
    session.add(cca)
    session.flush()
    session.add(ZipIncluded(cca_id=cca.id, zipcode="95032"))
    session.add(CityIncluded(cca_id=cca.id, city="San Rafael"))
    cca2 = CCA(cca_name="No Link CCA", is_cca=True, is_incumbent_utility=False, state="CA", signup_link=None)
    session.add(cca2)
    session.flush()
    session.add(CityIncluded(cca_id=cca2.id, city="Santa Cruz"))
    session.commit()
    session.close()

    def _get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.clear()

def test_zip_match():
    response = client.post("/eligible_ccas", json={"address": "95032"})
    assert response.status_code == 200
    result = response.json()
    assert len(result) > 0
    assert any("Test CCA" in cca["cca_name"] for cca in result)

def test_city_typo_match():
    response = client.post("/eligible_ccas", json={"address": "San Rafel, CA"})
    assert response.status_code == 200
    result = response.json()
    assert len(result) > 0
    assert any("Test CCA" in cca["cca_name"] for cca in result)

def test_missing_signup_link():
    response = client.post("/eligible_ccas", json={"address": "Santa Cruz, CA"})
    assert response.status_code == 200
    result = response.json()
    assert len(result) > 0
    assert any(cca["cca_name"] == "No Link CCA" for cca in result) 