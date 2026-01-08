CREATE TABLE donor (
    donor_id INTEGER PRIMARY KEY,
    name TEXT,
    email VARCHAR(100),
    IBAN INTEGER, 
    length_minutes INTEGER
);

CREATE TABLE donation (
    donation_id INTEGER PRIMARY KEY,
    zweck TEXT,
    amount INTEGER,
    IBAN INTEGER, 
    date INTEGER
);

CREATE TABLE fundraiser (
    fundraiser_id INTEGER PRIMARY KEY,
    name TEXT,
    email VARCHAR(100)
);
   
CREATE TABLE community (
    community_id INTEGER PRIMARY KEY,
    location TEXT,
    deficit_of INTERGER
);
