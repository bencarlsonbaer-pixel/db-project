DROP TABLE donor;
DROP TABLE donation;
DROP TABLE fundraiser;
DROP TABLE receiving_community;
DROP TABLE campaign;
DROP TABLE delivery;
DROP TABLE products;

CREATE TABLE donor (
    donor_id INTEGER PRIMARY KEY,
    donation_id INTEGER,
    fundraiser_id INTEGER,
    name TEXT,
    email VARCHAR(100),
    IBAN INTEGER, 
    length_minutes INTEGER,
    FOREIGN KEY (donation_id) REFERENCES donation(donation_id),
    FOREIGN KEY (fundraiser_id) REFERENCES fundraiser(fundraiser_id)
    
);

CREATE TABLE donation (
    donation_id INTEGER PRIMARY KEY,
    campaign_id INTEGER,
    donor_id INTEGER,
    product_id INTEGER,
    amount INTEGER,
    IBAN INTEGER, 
    date INTEGER,
    FOREIGN KEY (campaign_id) REFERENCES campaign(campaign_id),
    FOREIGN KEY (donor_id) REFERENCES donor(donor_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE fundraiser (
    fundraiser_id INTEGER PRIMARY KEY,
    name TEXT,
    donor_id INTEGER,
    campaign_id INTEGER,
    email VARCHAR(100),
    FOREIGN KEY (donor_id) REFERENCES donor(donor_id),
    FOREIGN KEY (campaign_id) REFERENCES campaign(campaign_id)
);
   
CREATE TABLE receiving_community (
    community_id INTEGER PRIMARY KEY,
    product_id INTEGER,
    delivery_id INTEGER,
    location TEXT,
    deficit_of INTERGER,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (delivery_id) REFERENCES delivery(delivery_id)
);

CREATE TABLE campaign (
    campaign_id INTEGER PRIMARY KEY,
    fundraiser_id INTEGER,
    revenue_total INTEGER,
    revenue_goal INTEGER,
    purpose TEXT,
    FOREIGN KEY (fundraiser_id) REFERENCES fundraiser(fundraiser_id)
);

CREATE TABLE delivery (
    delivery_id INTEGER PRIMARY KEY,
    product_id INTEGER,
    community_id INTEGER,
    destination VARCHAR(100),
    goods TEXT,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (community_id) REFERENCES receiving_community(community_id)
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    community_id INTEGER,
    delivery_id INTEGER,
    amount INTEGER,
    cost_per_unit INTEGER,
    type TEXT,
    FOREIGN KEY (community_id) REFERENCES receiving_community(community_id),
    FOREIGN KEY (delivery_id) REFERENCES delivery(delivery_id)
);
