-- =====================================================
-- COMPLETE UUID MIGRATION SCRIPT (FIXED)
-- This will convert all your tables to use UUID for IDs
-- =====================================================

-- Enable UUID extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Step 1: Drop all foreign key constraints first
-- (We'll recreate them later with UUID types)

-- Drop foreign key from sentiment_history to entity
ALTER TABLE sentiment_history DROP CONSTRAINT IF EXISTS fk_sentiment_history_entity;

-- Drop foreign key from feedback to user
ALTER TABLE feedback DROP CONSTRAINT IF EXISTS fk_feedback_user;

-- Drop foreign key from feedback to news
ALTER TABLE feedback DROP CONSTRAINT IF EXISTS fk_feedback_news;

-- Step 2: Create mapping tables to preserve relationships
-- This stores the old integer IDs and new UUIDs for each table

CREATE TEMP TABLE entity_id_mapping (
    old_id INTEGER,
    new_id UUID DEFAULT gen_random_uuid()
);

CREATE TEMP TABLE user_id_mapping (
    old_id INTEGER, 
    new_id UUID DEFAULT gen_random_uuid()
);

CREATE TEMP TABLE news_id_mapping (
    old_id INTEGER,
    new_id UUID DEFAULT gen_random_uuid()
);

CREATE TEMP TABLE feedback_id_mapping (
    old_id INTEGER,
    new_id UUID DEFAULT gen_random_uuid()
);

CREATE TEMP TABLE sentiment_history_id_mapping (
    old_id INTEGER,
    new_id UUID DEFAULT gen_random_uuid()
);

-- Step 3: Populate mapping tables with current IDs
INSERT INTO entity_id_mapping (old_id) SELECT id FROM entity;
INSERT INTO user_id_mapping (old_id) SELECT id FROM "user";
INSERT INTO news_id_mapping (old_id) SELECT id FROM news;
INSERT INTO feedback_id_mapping (old_id) SELECT id FROM feedback;
INSERT INTO sentiment_history_id_mapping (old_id) SELECT id FROM sentiment_history;

-- Step 4: Add new UUID columns to all tables

-- Entity table
ALTER TABLE entity ADD COLUMN new_id UUID;
UPDATE entity SET new_id = (SELECT new_id FROM entity_id_mapping WHERE entity_id_mapping.old_id = entity.id);

-- User table  
ALTER TABLE "user" ADD COLUMN new_id UUID;
UPDATE "user" SET new_id = (SELECT new_id FROM user_id_mapping WHERE user_id_mapping.old_id = "user".id);

-- News table
ALTER TABLE news ADD COLUMN new_id UUID;
UPDATE news SET new_id = (SELECT new_id FROM news_id_mapping WHERE news_id_mapping.old_id = news.id);

-- Feedback table
ALTER TABLE feedback ADD COLUMN new_id UUID;
UPDATE feedback SET new_id = (SELECT new_id FROM feedback_id_mapping WHERE feedback_id_mapping.old_id = feedback.id);

-- Sentiment_history table
ALTER TABLE sentiment_history ADD COLUMN new_id UUID;
UPDATE sentiment_history SET new_id = (SELECT new_id FROM sentiment_history_id_mapping WHERE sentiment_history_id_mapping.old_id = sentiment_history.id);

-- Step 5: Update foreign key columns

-- Update sentiment_history.entity_id to use the new UUID
ALTER TABLE sentiment_history ADD COLUMN new_entity_id UUID;
UPDATE sentiment_history 
SET new_entity_id = (
    SELECT entity_id_mapping.new_id 
    FROM entity_id_mapping 
    WHERE entity_id_mapping.old_id = sentiment_history.entity_id
);

-- Update feedback.userID to use the new UUID (NOTE: Quoted column name)
ALTER TABLE feedback ADD COLUMN "new_userID" UUID;
UPDATE feedback 
SET "new_userID" = (
    SELECT user_id_mapping.new_id 
    FROM user_id_mapping 
    WHERE user_id_mapping.old_id = feedback."userID"
);

-- Update feedback.newsID to use the new UUID (NOTE: Quoted column name)
ALTER TABLE feedback ADD COLUMN "new_newsID" UUID;
UPDATE feedback 
SET "new_newsID" = (
    SELECT news_id_mapping.new_id 
    FROM news_id_mapping 
    WHERE news_id_mapping.old_id = feedback."newsID"
);

-- Step 6: Drop old columns and rename new ones

-- Entity table
ALTER TABLE entity DROP COLUMN id CASCADE;
ALTER TABLE entity RENAME COLUMN new_id TO id;
ALTER TABLE entity ADD PRIMARY KEY (id);
ALTER TABLE entity ALTER COLUMN id SET DEFAULT gen_random_uuid();

-- User table
ALTER TABLE "user" DROP COLUMN id CASCADE;
ALTER TABLE "user" RENAME COLUMN new_id TO id;
ALTER TABLE "user" ADD PRIMARY KEY (id);
ALTER TABLE "user" ALTER COLUMN id SET DEFAULT gen_random_uuid();

-- News table
ALTER TABLE news DROP COLUMN id CASCADE;
ALTER TABLE news RENAME COLUMN new_id TO id;
ALTER TABLE news ADD PRIMARY KEY (id);
ALTER TABLE news ALTER COLUMN id SET DEFAULT gen_random_uuid();

-- Feedback table
ALTER TABLE feedback DROP COLUMN id CASCADE;
ALTER TABLE feedback RENAME COLUMN new_id TO id;
ALTER TABLE feedback ADD PRIMARY KEY (id);
ALTER TABLE feedback ALTER COLUMN id SET DEFAULT gen_random_uuid();

-- Sentiment_history table
ALTER TABLE sentiment_history DROP COLUMN id CASCADE;
ALTER TABLE sentiment_history RENAME COLUMN new_id TO id;
ALTER TABLE sentiment_history ADD PRIMARY KEY (id);
ALTER TABLE sentiment_history ALTER COLUMN id SET DEFAULT gen_random_uuid();

-- Step 7: Update foreign key columns
-- Sentiment_history entity_id
ALTER TABLE sentiment_history DROP COLUMN entity_id;
ALTER TABLE sentiment_history RENAME COLUMN new_entity_id TO entity_id;

-- Feedback userID (NOTE: Quoted column names)
ALTER TABLE feedback DROP COLUMN "userID";
ALTER TABLE feedback RENAME COLUMN "new_userID" TO "userID";

-- Feedback newsID (NOTE: Quoted column names)
ALTER TABLE feedback DROP COLUMN "newsID";
ALTER TABLE feedback RENAME COLUMN "new_newsID" TO "newsID";

-- Step 8: Recreate foreign key constraints
ALTER TABLE sentiment_history 
ADD CONSTRAINT fk_sentiment_history_entity 
FOREIGN KEY (entity_id) REFERENCES entity(id);

ALTER TABLE feedback 
ADD CONSTRAINT fk_feedback_user 
FOREIGN KEY ("userID") REFERENCES "user"(id);

ALTER TABLE feedback 
ADD CONSTRAINT fk_feedback_news 
FOREIGN KEY ("newsID") REFERENCES news(id);

-- Step 9: Clean up - Drop temporary mapping tables
DROP TABLE IF EXISTS entity_id_mapping;
DROP TABLE IF EXISTS user_id_mapping;
DROP TABLE IF EXISTS news_id_mapping;
DROP TABLE IF EXISTS feedback_id_mapping;
DROP TABLE IF EXISTS sentiment_history_id_mapping;

-- Verification queries - Check column types from system catalog
-- This will show the data type of the id column for each table
SELECT 
    t.table_name,
    c.column_name,
    c.data_type,
    c.is_nullable,
    c.column_default
FROM information_schema.tables t
JOIN information_schema.columns c ON t.table_name = c.table_name
WHERE t.table_schema = 'public' 
    AND t.table_name IN ('entity', 'user', 'news', 'feedback', 'sentiment_history')
    AND c.column_name = 'id'
ORDER BY t.table_name;

-- Also check foreign key column types
SELECT 
    t.table_name,
    c.column_name,
    c.data_type
FROM information_schema.tables t
JOIN information_schema.columns c ON t.table_name = c.table_name
WHERE t.table_schema = 'public' 
    AND (
        (t.table_name = 'sentiment_history' AND c.column_name = 'entity_id') OR
        (t.table_name = 'feedback' AND c.column_name IN ('userID', 'newsID'))
    )
ORDER BY t.table_name, c.column_name;