#!/usr/bin/env python3
import psycopg2

# read your text file
with open('character_creation.txt', encoding='utf-8') as f:
    summary = f.read()

# connect & update
conn = psycopg2.connect(dbname='influence_rpg', user='postgres', password='postgres')
cur = conn.cursor()
cur.execute(
    "UPDATE rulesets SET char_creation = %s;",
    (summary,)
)
conn.commit()
cur.close()
conn.close()
print("Updated char_creation successfully.")
