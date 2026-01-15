-- ============================================================
-- 0) RESET: Drop in richtiger Reihenfolge (wegen Foreign Keys)
-- ============================================================
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

-- ============================================================
-- 1) BASE TABLES
-- ============================================================

CREATE TABLE donor (
    donor_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE,                 -- Link zu users.id (für "Meine Spenden")
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
    date DATE,
    CONSTRAINT fk_donation_campaign
      FOREIGN KEY (campaign_id) REFERENCES campaign(campaign_id),
    CONSTRAINT fk_donation_donor
      FOREIGN KEY (donor_id) REFERENCES donor(donor_id),
    CONSTRAINT fk_donation_product
      FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- ============================================================
-- 2) JUNCTION TABLES (für Use Cases)
-- ============================================================

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

-- OPTIONAL (n:m Empfänger). Falls ihr nur delivery.community_id nutzt, könnt ihr das weglassen.
CREATE TABLE delivery_recipient (
  delivery_id INT NOT NULL,
  community_id INT NOT NULL,
  PRIMARY KEY (delivery_id, community_id),
  CONSTRAINT fk_deliveryrecipient_delivery
    FOREIGN KEY (delivery_id) REFERENCES delivery(delivery_id),
  CONSTRAINT fk_deliveryrecipient_community
    FOREIGN KEY (community_id) REFERENCES receiving_community(community_id)
);

-- ============================================================
-- 3) FK donor.user_id -> users.id  (users muss existieren!)
-- ============================================================
ALTER TABLE donor
ADD CONSTRAINT fk_donor_user
FOREIGN KEY (user_id) REFERENCES users(id);

-- ============================================================
-- 4) TESTDATEN (Fundraiser, Campaigns, Products, Communities, Deliveries, Donors, Donations)
-- ============================================================

-- Fundraiser
INSERT INTO fundraiser (fundraiser_id, name, email) VALUES
(1, 'Team RedRelief Zürich', 'zurich@redrelief.org'),
(2, 'Team RedRelief Genf',   'geneva@redrelief.org');

-- Campaigns (Werbekampagnen / Zwecke)
INSERT INTO campaign (campaign_id, fundraiser_id, revenue_total, revenue_goal, purpose) VALUES
(1, 1, 0, 50000, 'Erdbebenhilfe Türkei'),
(2, 1, 0, 30000, 'Winterpakete Ukraine'),
(3, 2, 0, 20000, 'Wasserfilter Sudan');

-- Products (Hilfsgüter)
INSERT INTO products (product_id, amount, cost_per_unit, type) VALUES
(1, 500, 50,  'Erste-Hilfe-Kit'),
(2, 800, 30,  'Wasserfilter'),
(3, 300, 120, 'Winterpaket'),
(4, 1000, 20, 'Hygiene-Set');

-- Receiving communities
INSERT INTO receiving_community (community_id, location, deficit_of) VALUES
(1, 'Gaziantep (TR)', 200),
(2, 'Lviv (UA)',      150),
(3, 'Khartum (SD)',   400);

-- Deliveries
INSERT INTO delivery (delivery_id, community_id, destination, goods) VALUES
(1, 1, 'Gaziantep Logistics Hub', 'Erste-Hilfe & Hygiene'),
(2, 2, 'Lviv Warehouse',          'Winterpakete'),
(3, 3, 'Khartum Distribution',    'Wasserfilter');

-- Delivery items (welche Produkte sind drin)
INSERT INTO delivery_item (delivery_id, product_id, quantity) VALUES
(1, 1, 80),   -- 80 Erste-Hilfe-Kits nach TR
(1, 4, 200),  -- 200 Hygiene-Sets nach TR
(2, 3, 60),   -- 60 Winterpakete nach UA
(3, 2, 150);  -- 150 Wasserfilter nach SD

-- Donors (Spender)
INSERT INTO donor (donor_id, user_id, name, email, IBAN, length_minutes) VALUES
(1, NULL, 'Gwen Gurt',      'gwen@example.com', 'CH9300762011623852957', 10),
(2, NULL, 'Tim Ydroid',     'tim@example.com',  'CH5604835012345678009', 5),
(3, NULL, 'Lina Muster',    'lina@example.com', 'CH2400123400000000000', 15),
(4, NULL, 'Noah Beispiel',  'noah@example.com', 'CH1200000000000000000', 7);

-- Donations (Spenden) + Kampagne + Produkt
-- Hinweis: amount = Geldbetrag (CHF in eurer UI)
INSERT INTO donation (donation_id, campaign_id, donor_id, product_id, amount, IBAN, date) VALUES
(1, 1, 1, 1, 100, 'CH9300762011623852957', '2026-01-05'),  -- Gwen -> Erdbebenhilfe -> Erste-Hilfe
(2, 1, 2, 4, 60,  'CH5604835012345678009', '2026-01-07'),  -- Tim  -> Erdbebenhilfe -> Hygiene
(3, 2, 3, 3, 240, 'CH2400123400000000000', '2026-01-10'),  -- Lina -> Winterpakete  -> Winterpaket
(4, 3, 4, 2, 90,  'CH1200000000000000000', '2026-01-12'),  -- Noah -> Wasserfilter  -> Wasserfilter
(5, 2, 1, 3, 120, 'CH9300762011623852957', '2026-01-14'),  -- Gwen -> Winterpakete  -> Winterpaket (noch nicht geliefert)
(6, 1, 1, 4, 40,  'CH9300762011623852957', '2026-01-15');  -- Gwen -> Erdbebenhilfe -> Hygiene (geliefert)

-- Donation -> Delivery Mapping (Spendenweg bis Lieferung)
-- Spende 5 bleibt absichtlich OHNE Lieferung => "In Vorbereitung"
INSERT INTO donation_delivery (donation_id, delivery_id) VALUES
(1, 1),
(2, 1),
(3, 2),
(4, 3),
(6, 1);

-- OPTIONAL: delivery_recipient (nur falls ihr n:m wirklich nutzt)
INSERT INTO delivery_recipient (delivery_id, community_id) VALUES
(1, 1),
(2, 2),
(3, 3);

-- ============================================================
-- 5) OPTIONAL: donor.user_id mit users verknüpfen (nur wenn User existiert!)
--    -> erst ausführen, wenn users.username wirklich existiert.
-- ============================================================

-- UPDATE donor
-- SET user_id = (SELECT id FROM users WHERE username='gwengurt')
-- WHERE donor_id = 1;

-- ============================================================
-- 6) QUERIES für donors.html (Top / Recent / Meine Spenden)
-- ============================================================

-- 6.1 TOP DONORS (Rangliste)
SELECT
  d.donor_id,
  d.name,
  COALESCE(SUM(dn.amount), 0) AS total_amount,
  COUNT(dn.donation_id) AS donation_count
FROM donor d
LEFT JOIN donation dn ON dn.donor_id = d.donor_id
GROUP BY d.donor_id, d.name
ORDER BY total_amount DESC
LIMIT 10;

-- 6.2 NEUSTE SPENDEN (mit Kampagne)
SELECT
  dn.date,
  d.name AS donor_name,
  dn.amount,
  COALESCE(c.purpose, '-') AS campaign_purpose
FROM donation dn
JOIN donor d ON d.donor_id = dn.donor_id
LEFT JOIN campaign c ON c.campaign_id = dn.campaign_id
ORDER BY dn.date DESC, dn.donation_id DESC
LIMIT 10;

-- 6.3 MEINE SPENDEN BIS ZUR LIEFERUNG (Use Case 1)
-- In Flask: WHERE d.user_id = %s  (current_user.id)
SELECT
  dn.donation_id,
  dn.date,
  dn.amount,
  COALESCE(c.purpose, '-') AS campaign_purpose,
  p.type AS product_type,
  dd.delivery_id,
  del.destination,
  rc.location AS receiver_location,
  CASE
    WHEN dd.delivery_id IS NULL THEN 'In Vorbereitung'
    ELSE 'Geliefert'
  END AS delivery_status
FROM donation dn
JOIN donor d ON d.donor_id = dn.donor_id
LEFT JOIN campaign c ON c.campaign_id = dn.campaign_id
LEFT JOIN products p ON p.product_id = dn.product_id
LEFT JOIN donation_delivery dd ON dd.donation_id = dn.donation_id
LEFT JOIN delivery del ON del.delivery_id = dd.delivery_id
LEFT JOIN receiving_community rc ON rc.community_id = del.community_id
WHERE d.user_id = 12345
ORDER BY dn.date DESC, dn.donation_id DESC;
