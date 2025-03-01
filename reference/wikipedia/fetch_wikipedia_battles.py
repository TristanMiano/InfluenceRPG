#!/usr/bin/env python3
"""
fetch_wikipedia_battles.py

This script fetches and extracts text content from Wikipedia articles for a list of historical battles.
The content of each battle's Wikipedia page is saved as a text file in the 'wikipedia_battles' directory,
which is designed to be parseable by the object template generation script.

Usage:
  python fetch_wikipedia_battles.py --battles "Battle of Austerlitz" "Battle of Waterloo"
  or
  python fetch_wikipedia_battles.py --file battles.txt

Dependencies:
  - wikipedia (install via pip: pip install wikipedia)
"""

import os
import argparse
import wikipedia
import re
from pathlib import Path

def sanitize_filename(name):
    """
    Sanitize the battle name to create a valid filename.
    """
    filename = re.sub(r'[\\/*?:"<>|]', "", name)
    filename = filename.replace(" ", "_")
    return filename

def fetch_battle_content(battle_name, lang="en"):
    """
    Fetch the Wikipedia article content for a given battle.
    If the battle name is ambiguous, try the first option.
    """
    wikipedia.set_lang(lang)
    try:
        page = wikipedia.page(battle_name)
        return page.content
    except wikipedia.DisambiguationError as e:
        print(f"Disambiguation error for '{battle_name}': {e.options}. Trying first option.")
        try:
            page = wikipedia.page(e.options[0])
            return page.content
        except Exception as ex:
            print(f"Failed to fetch content for '{battle_name}' from disambiguation option: {ex}")
            return None
    except wikipedia.PageError as e:
        print(f"Page not found for '{battle_name}': {e}")
        return None
    except Exception as e:
        print(f"Error fetching '{battle_name}': {e}")
        return None

def main():
    parser = argparse.ArgumentParser(
        description="Fetch Wikipedia content for historical battles and save as text files."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--battles", nargs="+", help="List of battle names to fetch.")
    group.add_argument("--file", type=str, help="Path to a text file containing battle names (one per line).")
    parser.add_argument("--lang", type=str, default="en", help="Wikipedia language (default: en).")
    parser.add_argument("--output_dir", type=str, default="battles", help="Directory to save text files.")
    args = parser.parse_args()

    battles = []
    if args.battles:
        battles = args.battles
    elif args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                battles = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"Error reading file {args.file}: {e}")
            return

    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)

    for battle in battles:
        print(f"Fetching Wikipedia content for: {battle}")
        content = fetch_battle_content(battle, lang=args.lang)
        if content:
            filename = sanitize_filename(battle) + ".txt"
            file_path = output_dir / filename
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Saved content to {file_path}")
            except Exception as e:
                print(f"Error writing to {file_path}: {e}")
        else:
            print(f"Skipping battle '{battle}' due to errors.")

if __name__ == "__main__":
    main()
