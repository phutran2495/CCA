-- Main CCA table
CREATE TABLE cca (
    id SERIAL PRIMARY KEY,
    cca_name TEXT NOT NULL,
    is_cca BOOLEAN NOT NULL,
    is_incumbent_utility BOOLEAN NOT NULL,
    state TEXT NOT NULL,
    signup_link TEXT
);

-- Included/Excluded Counties
CREATE TABLE cca_county_included (
    id SERIAL PRIMARY KEY,
    cca_id INTEGER REFERENCES cca(id) ON DELETE CASCADE,
    county TEXT NOT NULL
);

CREATE TABLE cca_county_excluded (
    id SERIAL PRIMARY KEY,
    cca_id INTEGER REFERENCES cca(id) ON DELETE CASCADE,
    county TEXT NOT NULL
);

-- Included/Excluded Cities
CREATE TABLE cca_city_included (
    id SERIAL PRIMARY KEY,
    cca_id INTEGER REFERENCES cca(id) ON DELETE CASCADE,
    city TEXT NOT NULL
);

CREATE TABLE cca_city_excluded (
    id SERIAL PRIMARY KEY,
    cca_id INTEGER REFERENCES cca(id) ON DELETE CASCADE,
    city TEXT NOT NULL
);

-- Included/Excluded Zipcodes
CREATE TABLE cca_zip_included (
    id SERIAL PRIMARY KEY,
    cca_id INTEGER REFERENCES cca(id) ON DELETE CASCADE,
    zipcode TEXT NOT NULL
);

CREATE TABLE cca_zip_excluded (
    id SERIAL PRIMARY KEY,
    cca_id INTEGER REFERENCES cca(id) ON DELETE CASCADE,
    zipcode TEXT NOT NULL
); 