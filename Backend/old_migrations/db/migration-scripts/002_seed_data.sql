-- 002_seed_data.sql

-- Inserting seed data into the user table
INSERT INTO "user" (username,email,"password",created_at) VALUES
	 ('shangwee','hoshangwee0911@gmail.com','pbkdf2:sha256:1000000$pBc89mE6oF7pIZCy$06acb5b318f76b0495d82ccfc9c346b4262e560e991a5d0826f6e0091e980f0e','2024-12-12 09:35:55.620198');

-- Inserting seed data into the entity table
INSERT INTO entity (name) VALUES
	 ('Tesla'),
	 ('TSMC'),
	 ('Apple'),
	 ('HSBC'),
	 ('Aramco');