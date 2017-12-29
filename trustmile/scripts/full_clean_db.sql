drop schema public cascade;
create schema public;

CREATE EXTENSION postgis;
-- use as such psql   -p 6432 trustmile_test -f scripts/full_clean_db.sql
