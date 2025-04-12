# Game Plan for Influence RPG: Roadmap to a Minimum Viable Playable Game

## Overview
This document outlines the strategic and tactical steps required to evolve the Influence RPG project into a minimum viable playable game. We will pursue development on two parallel branches:
1. **Web-Based Implementation:** Building the backend services, API endpoints, real-time chat, and database integration.
2. **Rule-Book & Game Design:** Refining and documenting the gameplay mechanics, narrative elements, and rules, with an eye toward flexible rule-system integration.

The goal is to reach a stage where we can pause, review our accomplishments, and update the plan based on feedback and playtesting results.

## Goals and Priorities
- **Achieve a Minimum Viable Playable Game (MVP):** 
  - Core functionality for user login, character creation, game joining, and communication.
  - Basic integration of Game Master (GM) narrative responses via LLM.
- **Parallel Development Branches:**
  - **Web-Based Implementation:** Robust server-side, real-time communication, and DB-driven interactions.
  - **Rule-Book & Game Design:** Detailed documentation of game mechanics (e.g., character attributes, risk/danger system) and narrative structures.
- **Advanced GM LLM Prompt Construction:**
  - Develop a RAG-style solution to assemble extensive context for GM prompts—combining a full rule-book, game instance setup, and conversation history.
- **Database and Persistent State Management:**
  - Define and iterate on the DB schema to store actions, events, chat history, and dynamic object states.
- **In-Game Objects and Asset Management:**
  - Establish clear protocols for creating, updating, and managing state changes for maps and in-game assets, integrated with GM LLM monitoring.

## Implementation Plan

### 1. Web-Based Implementation

#### 1.1. Core Backend Services
- **User & Character Management:**
  - Finalize and test user authentication endpoints.
  - Improve character creation/listing endpoints with robust error handling.
- **Game Services:**
  - Refine endpoints for game creation, joining, and state retrieval.
  - Integrate WebSocket channels for real-time chat and game events.
- **Database Schema Review:**
  - Evaluate and enhance the existing SQL schemas (users, characters, games, chat messages).
  - Plan updates to support dynamic logging of GM actions and game state transitions.

#### 1.2. Real-Time Communication Enhancements
- **WebSocket Improvements:**
  - Validate and stress-test chat and game chat modules.
  - Add event triggers to route player actions and GM interactions (e.g., state updates on in-game object changes).
- **Server Infrastructure:**
  - Streamline the server control scripts and ensure smooth deployment (consider containerization for consistency).

### 2. Rule-Book & Game Design

#### 2.1. Documentation and Rule Refinement
- **Core Rule-Book Development:**
  - Expand and refine documentation for character creation, risk/danger mechanics, and combat resolution.
  - Incorporate detailed examples and narrative guides to support gameplay.
- **Gameplay Scenario Planning:**
  - Develop sample play scenarios that test both strategic decision-making and personal narrative progression.
  - Ensure that rules are clear enough to be integrated with various possible software implementations.

#### 2.2. GM LLM Prompt & RAG Integration
- **Advanced Prompt Construction:**
  - Design a system that dynamically aggregates game context including the rule-book, initial setup data, and historical conversation logs.
  - Evaluate methods to summarize and compress context to fit within LLM context window constraints.
- **Configuration Enhancements:**
  - Update the GM LLM client configurations (e.g., in `llm_client.py` and `gm_llm.py`) to support flexible prompt building and context injection.

#### 2.3. In-Game Object and Asset Management
- **Dynamic State Management:**
  - Define how objects (e.g., maps, items) are represented and updated in-memory.
  - Determine how GM commands are processed to change object states, with updates synchronized to the DB.
- **Interaction Flow:**
  - Map out workflows for player interactions that trigger state changes and narrative updates via the GM LLM.

### 3. Iterative Milestones and Testing

#### Milestone 1: Core Functionality Prototype (Weeks 1–3)
- User login, character creation, game joining, and basic chat functionality.
- Initial integration of GM LLM responses to provide narrative context.

#### Milestone 2: Integrated Rule-Book and RAG-Style Prompting (Weeks 4–6)
- Prototype for advanced GM prompt construction that combines static rule-book data with dynamic in-game context.
- Enhancements to DB schemas to log game events, actions, and conversation history.

#### Milestone 3: Dynamic Game State and Object Management (Weeks 7–9)
- Implement mechanisms to manage in-game objects (e.g., maps, dynamic assets) with real-time state updates.
- Comprehensive playtesting to validate mechanics, adjust thresholds, and refine narrative integrations.

### 4. Additional Considerations
- **Modularity & Future Expansion:** 
  - Keep the software flexible to support different rule-book systems if necessary.
- **Scalability and Performance:**
  - Ensure backend services and prompt construction methods are optimized to handle extended context windows and heavy usage.
- **Collaboration & Documentation:**
  - Continuously update project documentation to reflect changes in design and implementation for all team members.

## Conclusion
This game plan sets out a clear, phased approach to reach a minimum viable playable version of the Influence RPG. By addressing both the technical backend and the underlying game design concurrently, we lay a robust foundation that will allow us to iterate further, gather playtesting feedback, and prepare detailed revisions in our subsequent planning cycles.

---

*Review and update this plan regularly as development progresses and priorities evolve.*