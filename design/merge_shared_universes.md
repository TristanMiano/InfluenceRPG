Here’s a sketch of how you might architect “instance”-level streams that can later be merged into a shared-universe timeline—with automatic canon-tagging, conflict detection, and configurable merge triggers.

---

## 1. Model everything as **events** with rich metadata

Treat every GM or player action as an append-only event in an event store.  Each event carries:

* **Instance ID** (which “branch” it came from)
* **World timestamp** (in-game or real-time)
* **Entity references** (NPCs, locations, props)
* **Event type** (dialogue, combat, location change, item acquisition…)
* **Automatically-computed hash/ID** (for deduplication)
* **Canonicity flag** (default = “canon”; toggled off only if involved in a merge conflict)

By centralizing on events, you can replay or project any instance into a global state, or selectively filter by instance.

---

## 2. Detecting merge conflicts

When you try to merge two event-streams (A & B) into the master timeline, look for:

1. **Entity-level conflicts**: two events that modify the same property of the same entity (e.g. “Dragon’s HP set to 0” vs. “Dragon still alive”)
2. **Contradictory state changes**: e.g. A loots the “Sword of Light” at time T, B destroys that same sword at time T+Δ
3. **Duplicate IDs**: two different events accidentally generated the same unique ID (sign of a bug)

Flag any conflicting event pairs for resolution.  All non-conflicting events simply get slotted into the merged timeline in ascending world-time order.

---

## 3. Canon resolution strategies

Once you’ve identified conflicts, you can choose among:

* **Automatic heuristics**

  * **Last-write-wins** (whichever event has the later world-timestamp)
  * **Priority by instance** (e.g. “campaign A > campaign B”)
* **Human-in-the-loop**

  * Present conflict pairs in a UI; let the lead GM pick which to keep or rewrite
  * Enable a “consensus vote” among instance GMs or even players
* **Narrative fallback**

  * If unresolved, spin off a new branch/universe (“what if both happened?”)
  * Tag both events non-canon and require a follow-up session to reconcile

After resolution, mark the chosen event(s) “canon,” and the discarded one(s) become side-stories or “alternate timeline” events.

---

## 4. When and how to **trigger** merges

You can make merges **automatic** or **manual**.  Some ideas:

| Trigger type        | How it works                                                             |
| ------------------- | ------------------------------------------------------------------------ |
| **Scheduled**       | e.g. every 5 sessions or once a month you auto-merge new events          |
| **Milestone-based** | on completing a major arc (“defeat the Lich King”), then merge           |
| **Event-driven**    | when two instances reference the same PSA (place, NPC, artifact)         |
| **Player-invoked**  | a “cross-over” GM command: `/merge-with instance-xyz`                    |
| **Conditional**     | when instance A reaches world-time X, pull in all events from B before X |

You could also maintain a **merge “window”**—e.g. only merge events that occurred more than 24 hours ago, to let late edits surface before finalizing.

---

## 5. Implementation patterns

* **Event Sourcing + CRDTs**

  * If many events are commutative (just “✎ text additions”), you can model them as a CRDT log—merging is then inherently conflict-free except for real state mutations.
* **Git-style branching**

  * Treat each instance as a Git branch; “commits” are events; merging invokes standard three-way diff/merge tooling to flag conflicts.
* **Saga orchestration**

  * Use sagas to coordinate multi-instance “quests”: each participant instance emits events, the saga engine watches for completion and then merges outcomes.

---

### Putting it all together

1. **Emit** every GM/player action as a timestamped, instance-tagged event.
2. **Periodically** (or on demand) **collect** new events from each instance and **sort** them by world time.
3. **Detect** conflicts (same entity, contradictory changes).
4. **Resolve** via auto-heuristic or GM/UI-driven choice; re-tag events’ canonicity.
5. **Publish** the merged, conflict-free timeline to all participants or to a global “world state” view.

With this event-driven, metadata-rich approach you get full audit trails, flexible conflict handling, and clear hooks for both automated and human-mediated resolutions.

## Architect Decision

Main author (Tristan's) thoughts: One thing I'll add right now is that one way to merge when a conflict is detected (two instances in an overlapping situation) is to merge the two instances into one instance. 
Secondly, in a shared universe, major events might be published to the database - the more major the event, the more widely shared this news is, but GMs of an instance within the radius of the news source will have access to this information. 
This won't mean instances need to be merged yet, per se. But it would be a lot like if the characters in a story literally did read the newspaper in their fictional universe and saw that something happened - e.g. "King X died" - and this will drive the generation loop of the GM.

### o4-mini-high's diagram

flowchart LR
  subgraph Instances
    A[Instance A] -->|events| E[Event Store]
    B[Instance B] -->|events| E
    C[Instance C]
  end

  E -->|scan for conflicts| ConflictDetector
  ConflictDetector -->|hard conflict| Merger
  Merger --> C
  E -->|extract major events| Publisher
  Publisher -->|publish by radius| NewsBus
  NewsBus --> A
  NewsBus --> B
  NewsBus --> any GM instance
