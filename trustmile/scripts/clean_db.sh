#!/usr/bin/env bash

psql -h pgbouncer -p 6432 $1 -f scripts/full_clean_db.sql

#python -c "from app import db; db.create_all()"
