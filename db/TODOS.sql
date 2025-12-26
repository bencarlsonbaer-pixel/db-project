
CREATE TABLE donor (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(250) NOT NULL,
    email VARCHAR(250) NOT NULL UNIQUE,
    password VARCHAR(250) NOT NULL,
    iban VARCHAR(50)
);

CREATE TABLE fundraiser (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(250) NOT NULL,
    zielbetrag DECIMAL(10, 2)
);

CREATE TABLE lieferung (
    id INT AUTO_INCREMENT PRIMARY KEY,
    destination VARCHAR(250),
    status VARCHAR(50) DEFAULT 'In Vorbereitung'
);

CREATE TABLE produkte (
    id INT AUTO_INCREMENT PRIMARY KEY,
    art VARCHAR(100),
    kosten DECIMAL(10, 2),
    anzahl INT,
    lieferung_id INT,
    FOREIGN KEY (lieferung_id) REFERENCES lieferung(id)
);

CREATE TABLE spende (
    id INT AUTO_INCREMENT PRIMARY KEY,
    donor_id INT NOT NULL,
    fundraiser_id INT,
    betrag DECIMAL(10, 2) NOT NULL,
    datum DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (donor_id) REFERENCES donor(id),
    FOREIGN KEY (fundraiser_id) REFERENCES fundraiser(id)
);

-- Verknüpfungstabelle für Use Case 1 (n:m Beziehung)
CREATE TABLE spende_finanziert_produkt (
    spende_id INT NOT NULL,
    produkt_id INT NOT NULL,
    PRIMARY KEY (spende_id, produkt_id),
    FOREIGN KEY (spende_id) REFERENCES spende(id),
    FOREIGN KEY (produkt_id) REFERENCES produkte(id)
);


