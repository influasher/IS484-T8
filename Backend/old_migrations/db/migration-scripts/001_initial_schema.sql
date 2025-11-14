-- 001_initial_schema.sql

-- Table: user
CREATE TABLE "user" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: news
CREATE TABLE "news" (
    id SERIAL PRIMARY KEY,
    publisher VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    published_date TIMESTAMP NOT NULL,
    title VARCHAR(255) NOT NULL,
    url TEXT NOT NULL UNIQUE,
    entities TEXT[],
    sentiment VARCHAR(50)
);

-- Table: entity
CREATE TABLE "entity" (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);
