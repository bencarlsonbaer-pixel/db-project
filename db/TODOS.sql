-- =========================
-- RESET (DROP in richtiger Reihenfolge)
-- =========================
DROP TABLE IF EXISTS donation_delivery;
DROP TABLE IF EXISTS delivery_item;
DROP TABLE IF EXISTS delivery_recipient;

DROP TABLE IF EXISTS donation;
DROP TABLE IF EXISTS delivery;
DROP TABLE IF EXISTS receiving_community;
DROP TABLE IF EXISTS campaign;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS fundraiser;
DROP TABLE IF EXISTS donor;

-- =========================
-- BASE TABLES
-- =========================

CREATE TABLE donor (
    donor_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE,                 -- Verknüpft mit users.id (für "Meine Spenden")
    name VARCHAR(120) NOT NULL,
    email VARCHAR(100),
    IBAN VARCHAR(34),
    length_minutes INT
);

CREATE TABLE fundraiser (
    fundraiser_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(100)
);

CREATE TABLE campaign (
    campaign_id INT PRIMARY KEY AUTO_INCREMENT,
    fundraiser_id INT,
    revenue_total INT,
    revenue_goal INT,
    purpose TEXT,
    CONSTRAINT fk_campaign_fundraiser
      FOREIGN KEY (fundraiser_id) REFERENCES fundraiser(fundraiser_id)
);

CREATE TABLE products (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    amount INT NOT NULL,
    cost_per_unit INT NOT NULL,
    type VARCHAR(120) NOT NULL
);

CREATE TABLE receiving_community (
    community_id INT PRIMARY KEY AUTO_INCREMENT,
    location VARCHAR(120) NOT NULL,
    deficit_of INT
);

CREATE TABLE delivery (
    delivery_id INT PRIMARY KEY AUTO_INCREMENT,
    community_id INT,
    destination VARCHAR(100),
    goods TEXT,
    CONSTRAINT fk_delivery_community
      FOREIGN KEY (community_id) REFERENCES receiving_community(community_id)
);

CREATE TABLE donation (
    donation_id INT PRIMARY KEY AUTO_INCREMENT,
    campaign_id INT,
    donor_id INT,
    product_id INT,
    amount INT NOT NULL,
    IBAN VARCHAR(34),
    date DATE,                          -- gleich als DATE
    CONSTRAINT fk_donation_campaign
      FOREIGN KEY (campaign_id) REFERENCES campaign(campaign_id),
    CONSTRAINT fk_donation_donor
      FOREIGN KEY (donor_id) REFERENCES donor(donor_id),
    CONSTRAINT fk_donation_product
      FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- =========================
-- JUNCTION TABLES (für Use Cases)
-- =========================

-- Welche Produkte sind in welcher Lieferung (mit Menge)
CREATE TABLE delivery_item (
  delivery_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity INT NOT NULL,
  PRIMARY KEY (delivery_id, product_id),
  CONSTRAINT fk_deliveryitem_delivery
    FOREIGN KEY (delivery_id) REFERENCES delivery(delivery_id),
  CONSTRAINT fk_deliveryitem_product
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Welche Spende hängt an welcher Lieferung (Spendenweg nachvollziehen)
CREATE TABLE donation_delivery (
  donation_id INT NOT NULL,
  delivery_id INT NOT NULL,
  PRIMARY KEY (donation_id, delivery_id),
  CONSTRAINT fk_donationdelivery_donation
    FOREIGN KEY (donation_id) REFERENCES donation(donation_id),
  CONSTRAINT fk_donationdelivery_delivery
    FOREIGN KEY (delivery_id) REFERENCES delivery(delivery_id)
);

-- OPTIONAL: Lieferung kann mehreren Communities zugeordnet werden
-- (Wenn ihr das wirklich braucht. Sonst weglassen und nur delivery.community_id nutzen.)
CREATE TABLE delivery_recipient (
  delivery_id INT NOT NULL,
  community_id INT NOT NULL,
  PRIMARY KEY (delivery_id, community_id),
  CONSTRAINT fk_deliveryrecipient_delivery
    FOREIGN KEY (delivery_id) REFERENCES delivery(delivery_id),
  CONSTRAINT fk_deliveryrecipient_community
    FOREIGN KEY (community_id) REFERENCES receiving_community(community_id)
);

-- =========================
-- FK: donor.user_id -> users.id
-- (users Tabelle muss bereits existieren!)
-- =========================
ALTER TABLE donor
ADD CONSTRAINT fk_donor_user
FOREIGN KEY (user_id) REFERENCES users(id);

-- =========================
-- OPTIONAL: Beispiel-Verknüpfung für euren Demo-User
-- (nur ausführen, wenn donor_id=1 wirklich existiert)
-- =========================
UPDATE donor
SET user_id = (SELECT id FROM users WHERE username='gwengurt')
WHERE donor_id = 1;
