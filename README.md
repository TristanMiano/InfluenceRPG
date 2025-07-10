# Tabletop RPG of Influence & Strategic Command

## Overview
This project aims to create a revolutionary tabletop role-playing game (RPG) that fuses detailed character-driven narrative with expansive strategic simulation. Unlike traditional RPGs that focus solely on adventuring, our game places players in the roles of high-status figures—such as military leaders, political masterminds, corporate magnates, and cultural icons—who wield influence over vast social, economic, and military domains. Players will experience both the intricate personal development typical of RPGs and the large-scale decision-making found in strategy games.

## Table of Contents
- [Game Format](#game-format)
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

## Game Format
This game is played entirely online. Players connect through a web browser and share a single game instance managed by an AI gamemaster powered by large language models. The system supports multiple players at once, and the AI handles scene narration, NPC dialogue, and dice rolls. While there's no physical table, you still create characters, cooperate with other players, and experience a collaborative story much like a traditional tabletop RPG.

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
- **Outcome Determination:** A dice roll (modified by character attributes and situational factors) determines whether a positive event (improving risk) or a negative event (worsening risk) occurs.
- **Narrative Integration:** Each outcome is enriched with narrative descriptions, blending mechanical events with creative storytelling.

## Procedural Generation & Architecture
The project is built on a robust, modular architecture that leverages AI-driven procedural generation to manage a living, evolving game world:
- **Procedural Generation Engine (PGE):** Dynamically creates game objects (characters, items, locations, events) using modular templates and algorithmic randomness.
- **Object Repository & State Management:** A database system stores each generated object and its evolving history, ensuring persistent and dynamic gameplay.
- **Simulation & Event Engine:** Processes complex simulations—including large-scale battles—by handling numerous dice rolls and event ticks in parallel.
- **AI-Gamemaster Module:** Uses large language models (LLMs) to generate contextual narrative, dialogue, and scene descriptions.
- **Player Interaction Layer:** A text-based interface (or API) through which players issue commands and receive real-time updates.
- **Integration Bus:** An event-driven system, potentially using microservices, for seamless communication among various project components.

## Classes & Archetypes
Players choose from several broad classes that define their path to influence. Each class can be further customized:
1. **Military Leader:** Focuses on battlefield tactics and strategic command.
2. **Political Leader:** Excels in negotiation, governance, and policy-making.
3. **Religious Leader:** Wields spiritual authority and moral influence.
4. **Criminal Overlord:** Commands the underworld with resourcefulness and ruthlessness.
5. **Corporate Magnate:** Dominates industries and economic landscapes.
6. **Innovator:** Drives progress with creative problem-solving and technological breakthroughs.
7. **Cultural Icon:** Influences public opinion and cultural trends.

## Reference Materials
Extensive research and reference files ensure historical and tactical authenticity. These include:
- Detailed naval specifications (e.g., HMS Victory).
- Historical and tactical documents.
- Various drafts and templates for character creation and narrative development.

## Future Extensions
While the initial focus is on modern military mechanics and high-level strategy, future versions will expand the game to include:
- Multiple eras and genres.
- Expanded domains of influence (political, economic, cultural).
- Enhanced AI integration for dynamic storytelling and procedural content generation.

## Development Roadmap
1. **Prototype Development:** Build a basic version of the Procedural Generation Engine and Object Repository.
2. **Integration Testing:** Ensure robust communication between simulation engine, AI-gamemaster, and player interface.
3. **Performance Benchmarking:** Simulate large-scale scenarios to validate scalability.
4. **Iterative Refinement:** Use playtesting feedback to adjust mechanics, thresholds, and narrative integration.
5. **Documentation Consolidation:** Transition to using this README.md as the single source of project truth.

## Requirements
- **Language & Environment:** Python is used for prototyping and system integration.
- **Dependencies:** Managed via the auto-generated `requirements_autogenerated.txt`.
- **AI Integration:** Uses LLM APIs (e.g., Google Gemini) for narrative generation.
- **Database:** A relational or NoSQL database for persistent state management.

