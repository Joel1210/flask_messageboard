select database();

CREATE DATABASE IF NOT EXISTS user_lr;

USE user_lr;

select database();

-- DROP TABLE users

CREATE TABLE IF NOT EXISTS users (
	id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    firstname VARCHAR(255) NULL,
	lastname VARCHAR(255) NULL,
    email VARCHAR(255) NULL,
    password VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT now(),
    modified_at DATETIME NOT NULL DEFAULT now() ON UPDATE now()
);

