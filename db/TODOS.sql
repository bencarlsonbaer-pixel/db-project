DROP TABLE IF EXISTS donation;
DROP TABLE IF EXISTS delivery;
DROP TABLE IF EXISTS receiving_community;
DROP TABLE IF EXISTS campaign;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS fundraiser;
DROP TABLE IF EXISTS donor;

CREATE TABLE donor (
    donor_id INTEGER PRIMARY KEY,
    name TEXT,
    email VARCHAR(100),
    IBAN VARCHAR(34),
    length_minutes INTEGER
);

CREATE TABLE fundraiser (
    fundraiser_id INTEGER PRIMARY KEY,
    name TEXT,
    email VARCHAR(100)
);

CREATE TABLE campaign (
    campaign_id INTEGER PRIMARY KEY,
    fundraiser_id INTEGER,
    revenue_total INTEGER,
    revenue_goal INTEGER,
    purpose TEXT,
    FOREIGN KEY (fundraiser_id) REFERENCES fundraiser(fundraiser_id)
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    amount INTEGER,
    cost_per_unit INTEGER,
    type TEXT
);

CREATE TABLE receiving_community (
    community_id INTEGER PRIMARY KEY,
    location TEXT,
    deficit_of INTEGER
);

CREATE TABLE delivery (
    delivery_id INTEGER PRIMARY KEY,
    community_id INTEGER,
    destination VARCHAR(100),
    goods TEXT,
    FOREIGN KEY (community_id) REFERENCES receiving_community(community_id)
);

CREATE TABLE donation (
    donation_id INTEGER PRIMARY KEY,
    campaign_id INTEGER,
    donor_id INTEGER,
    product_id INTEGER,
    amount INTEGER,
    IBAN VARCHAR(34),
    date INTEGER,
    FOREIGN KEY (campaign_id) REFERENCES campaign(campaign_id),
    FOREIGN KEY (donor_id) REFERENCES donor(donor_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
