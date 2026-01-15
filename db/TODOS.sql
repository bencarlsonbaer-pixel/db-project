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
CREATE TABLE delivery_item (
  delivery_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity INT NOT NULL,
  PRIMARY KEY (delivery_id, product_id),
  FOREIGN KEY (delivery_id) REFERENCES delivery(delivery_id),
  FOREIGN KEY (product_id) REFERENCES products(product_id)
);
CREATE TABLE donation_delivery (
  donation_id INT NOT NULL,
  delivery_id INT NOT NULL,
  PRIMARY KEY (donation_id, delivery_id),
  FOREIGN KEY (donation_id) REFERENCES donation(donation_id),
  FOREIGN KEY (delivery_id) REFERENCES delivery(delivery_id)
);
CREATE TABLE delivery_recipient (
  delivery_id INT NOT NULL,
  community_id INT NOT NULL,
  PRIMARY KEY (delivery_id, community_id),
  FOREIGN KEY (delivery_id) REFERENCES delivery(delivery_id),
  FOREIGN KEY (community_id) REFERENCES receiving_community(community_id)
);
ALTER TABLE donor
ADD COLUMN user_id INT UNIQUE;
ALTER TABLE donor
ADD CONSTRAINT fk_donor_user
FOREIGN KEY (user_id) REFERENCES users(id);
ALTER TABLE donation MODIFY date DATE;

ALTER TABLE donor
ADD COLUMN user_id INT UNIQUE;

ALTER TABLE donor
ADD CONSTRAINT fk_donor_user
FOREIGN KEY (user_id) REFERENCES users(id);

CREATE TABLE IF NOT EXISTS delivery_product (
  delivery_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity INT NOT NULL,
  PRIMARY KEY (delivery_id, product_id),
  FOREIGN KEY (delivery_id) REFERENCES delivery(delivery_id),
  FOREIGN KEY (product_id) REFERENCES products(product_id)
);
UPDATE donor
SET user_id = (SELECT id FROM users WHERE username='gwengurt')
WHERE donor_id = 1;
