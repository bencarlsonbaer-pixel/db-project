CREATE TABLE donor (
    donor_id INTEGER PRIMARY KEY,
    name TEXT,
    email TEXT,
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
   
