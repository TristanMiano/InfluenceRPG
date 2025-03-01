# Tabletop RPG of Influence & Strategic Command

## Overview
This project aims to create a revolutionary tabletop role-playing game (RPG) that fuses detailed character-driven narrative with expansive strategic simulation. Unlike traditional RPGs that focus solely on adventuring, our game places players in the roles of high-status figures—such as military leaders, political masterminds, corporate magnates, and cultural icons—who wield influence over vast social, economic, and military domains. Players will experience both the intricate personal development typical of RPGs and the large-scale decision-making found in strategy games.

## Table of Contents
- [Project Vision](#project-vision)
- [Game Mechanics](#game-mechanics)
  - [Military Mechanics](#military-mechanics)
  - [Character Attributes & Creation](#character-attributes--creation)
  - [Risk/Danger System](#riskdanger-system)
- [Procedural Generation & Architecture](#procedural-generation--architecture)
- [Classes & Archetypes](#classes--archetypes)
- [Reference Materials](#reference-materials)
- [Future Extensions](#future-extensions)
- [Development Roadmap](#development-roadmap)
- [Requirements](#requirements)

## Project Vision
The game is designed to merge intimate, character-driven role-playing with the high-stakes dynamics of strategic management. Players assume the roles of influential figures—from military commanders and political leaders to CEOs and even deities in fantasy or sci-fi settings—whose personal actions and grand strategic decisions shape the world around them. The core design emphasizes:
- **Dual Layer Gameplay:** Integrating personal narrative with large-scale strategic control.
- **Dynamic Storytelling:** Using AI and procedural generation to create immersive narratives that evolve with player decisions.
- **Modular Design:** A system built with flexibility in mind, allowing future expansion into multiple eras and domains of influence.

## Game Mechanics

### Military Mechanics
- **Hierarchical Command:** Characters begin as low-level officers and can rise to the rank of generals based on tactical acumen and successful command.
- **Dice-Based Combat Resolution:** Battles are resolved with dice rolls that incorporate factors such as terrain, weather, unit morale, and enemy tactics—ensuring that even the best plans are subject to the chaos of war.
- **Strategic Decision-Making:** Beyond individual encounters, players manage logistics, deploy resources, and plan entire campaigns that affect the broader narrative.

### Character Attributes & Creation
Characters are defined by six core attributes that capture the essence of personal influence:
1. **Stature:** The physical legacy and commanding presence of a character.
2. **Charisma:** Natural magnetism and persuasive power.
3. **Tactics:** The ability to devise and execute strategic plans.
4. **Gravitas:** Moral authority and ethical weight that influence social interactions.
5. **Resolve:** Mental toughness and determination under pressure.
6. **Ingenuity:** Creative problem-solving and adaptability.

Each attribute starts at a baseline score of **10**, with modifiers calculated as +1 for every 2 points above (or -1 for every 2 points below) the baseline. The character creation process combines backstory, point allocation, and potential dice-based or point-buy methods to ensure every influential persona is both unique and balanced.

### Risk/Danger System
Instead of traditional hitpoints, the game introduces a dynamic risk or danger system:
- **Risk Levels:** Characters are categorized into four risk states—Low-Risk, Normal, High-Risk, and Critical. If the risk level drops below Critical, the character dies.
- **Variable Check Intervals:** The frequency of risk checks depends on the current risk level (yearly for Low-Risk, monthly for Normal, weekly for High-Risk, and daily for Critical).
- **Outcome Determination:** A dice roll (modified by character attributes and situational factors) determines whether a positive event (improving risk) or a negative event (worsening risk) occurs. Each outcome is enriched by narrative descriptions generated by the game master or an AI module.
- **Player Agency:** Actions taken by players can immediately affect their risk level, integrating the risk system into both mechanical and narrative aspects of gameplay.

## Procedural Generation & Architecture
The project is built on a robust, modular architecture that leverages AI-driven procedural generation to manage a living, evolving game world:
- **Procedural Generation Engine (PGE):** Dynamically creates thousands of game objects (characters, items, locations, events) using modular templates and algorithmic randomness.
- **Object Repository & State Management:** A database system that stores each generated object and its evolving history, allowing for persistent and dynamic gameplay.
- **Simulation & Event Engine:** Processes complex simulations, including large-scale battles, by handling thousands of dice rolls and event ticks in parallel.
- **AI-Gamemaster Module:** Uses large language models (LLMs) to generate contextual narrative, dialogue, scene descriptions, and to assist in high-level decision making.
- **Player Interaction Layer:** A text-based interface (or API) through which players issue commands and receive descriptive, real-time updates.
- **Integration & Communication Bus:** An event-driven system (potentially using microservices) that enables seamless communication among the various components.

## Classes & Archetypes
Players choose from several broad classes that define their path to influence. Each class can be subdivided into more specific sub-classes and even customized further by players:
1. **Military Leader:** Focuses on strategic command and battlefield tactics.  
   *Sub-classes:* Army General, Naval Officer, Air Force Commander, Special Forces Operative.
2. **Political Leader:** Experts in negotiation, governance, and policy-making.  
   *Sub-classes:* Head of State, Legislator, Diplomat, Local Leader.
3. **Religious Leader:** Figures who wield spiritual and moral authority.  
   *Sub-classes:* Cleric, Cult Leader, Prophet, Mystical Advisor.
4. **Criminal Overlord:** Masters of the underworld who command through fear and resourcefulness.  
   *Sub-classes:* Mafia Boss, Gang Leader, Smuggling Kingpin, Crime Strategist.
5. **Corporate Magnate:** Titans of industry who shape economic landscapes.  
   *Sub-classes:* CEO, Industrialist, Venture Capitalist, Financial Tycoon.
6. **Innovator:** Pioneers of progress in science and technology.  
   *Sub-classes:* Scientist, Professor, Inventor, Tech Pioneer.
7. **Cultural Icon:** Influencers who shape trends in art, media, and public opinion.  
   *Sub-classes:* Celebrity, Media Mogul, Artist, Social Media Influencer.

## Reference Materials
The project incorporates extensive research and reference files to ensure historical and tactical authenticity:
- **Naval Assets:** Detailed ship specifications (e.g., HMS Victory) that provide technical data and gameplay attributes for large-scale naval engagements.
- **Historical & Tactical Research:** Documentation that informs realistic military structures, battle mechanics, and strategic doctrines.

## Future Extensions
While the initial focus is on modern military mechanics and high-level strategy, the system is designed to be extensible:
- **Multiple Eras & Genres:** Future versions may include settings spanning ancient, medieval, futuristic, fantasy, and science fiction themes.
- **Expanded Domains of Influence:** Beyond military command, upcoming modules could encompass political, economic, and cultural strategies.
- **Enhanced AI Integration:** Greater use of AI for narrative generation, procedural content creation, and even dynamic world-building in response to player actions.

## Development Roadmap
1. **Prototype Development:** Build a basic version of the Procedural Generation Engine and Object Repository.
2. **Integration Testing:** Establish robust communication between the simulation engine, AI-gamemaster, and player interface.
3. **Performance Benchmarking:** Simulate large-scale scenarios (e.g., naval battles, massive risk events) to ensure scalability.
4. **Iterative Refinement:** Use playtesting feedback to adjust thresholds, risk modifiers, narrative integration, and overall balance.
5. **Documentation Consolidation:** Replace initial iteration documents with this README.md as the single source of project truth.

## Requirements
- **Language & Environment:** Python is used for prototyping and system integration.
- **Dependencies:** Third-party libraries and modules will be managed via an auto-generated `requirements_autogenerated.txt` file.
- **AI Integration:** LLM APIs (e.g., Gemini or similar) for narrative and creative content generation.
- **Database:** A relational or NoSQL database for persistent state management.