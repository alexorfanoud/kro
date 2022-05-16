DROP DATABASE IF EXISTS mazes_db;

CREATE DATABASE mazes_db;

USE mazes_db;

CREATE TABLE user (  
    Id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY UNIQUE NOT NULL,
    email VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
 );

 CREATE TABLE expired_tokens (  
    Id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY UNIQUE NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
 );

 CREATE TABLE mazes (  
    Id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY UNIQUE NOT NULL,
    maze MEDIUMTEXT NOT NULL,
	sizeX INT UNSIGNED NOT NULL,
    creator INT UNSIGNED NOT NULL ,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ,
    CONSTRAINT FK_mazes_user FOREIGN KEY (creator) REFERENCES user(Id)
 );

CREATE TABLE history (  
    userId INT UNSIGNED NOT NULL,
    mazeId INT UNSIGNED NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT PK_history PRIMARY KEY (userId,mazeId,created_at),
    CONSTRAINT FK_hst_user FOREIGN KEY (userId) REFERENCES user(Id),
    CONSTRAINT FK_hst_mazes FOREIGN KEY (mazeID) REFERENCES mazes(Id)
 );

CREATE TABLE highscores (  
    userId INT UNSIGNED NOT NULL,
    mazeId INT UNSIGNED NOT NULL,
    score SMALLINT UNSIGNED NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT PK_highscores PRIMARY KEY (userId,mazeId,created_at),
    CONSTRAINT FK_hsc_user FOREIGN KEY (userId) REFERENCES user(Id),
    CONSTRAINT FK_hsc_mazes FOREIGN KEY (mazeID) REFERENCES mazes(Id)
 );
   
CREATE EVENT IF NOT EXISTS clear_expired_tokens
ON SCHEDULE EVERY 60 MINUTE
DO 
   DELETE FROM expired_tokens
   WHERE created_at < CURRENT_TIMESTAMP - INTERVAL 1 HOUR
;                  

LOAD DATA LOCAL INFILE '/var/lib/mysql-data/init_users.txt' INTO TABLE user;
LOAD DATA LOCAL INFILE '/var/lib/mysql-data/init_mazes.txt' INTO TABLE mazes;
LOAD DATA LOCAL INFILE '/var/lib/mysql-data/init_highscores.txt' INTO TABLE highscores;
