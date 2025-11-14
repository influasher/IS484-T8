-- run this file in SQL first to create the database before running the migrations to ensure the database exists  and connection is successful

CREATE DATABASE IF NOT EXISTS `SentiFinance` /*!40100 DEFAULT CHARACTER SET utf8mb4 */;


-- for testing purposes
CREATE USER test_user WITH PASSWORD 'test_password';
CREATE DATABASE test_db OWNER test_user;

GRANT ALL PRIVILEGES ON DATABASE test_db TO test_user;