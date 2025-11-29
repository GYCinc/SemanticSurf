---
trigger: always_on
---

I acknowledge and confirm: The 8 Categories are immutable. I will never hallucinate them, change them, or improvise them.

Here is the exact setup of the schema and data flow as you described, which I accept as fact:

1. The Immutable 8 Categories
These are the only valid categories for classification. They do not change.

Phrasal Verbs
Vocabulary
Expressions
Grammar
Pronunciation
Flow
Discourse
Sociolinguistics

2. The Architecture & Data Flow
Ingestion (The "Petty Dantic" / Pydantic API):
Data enters the system via strict JSON payloads.
It MUST pass strict Pydantic validation against the schema.
If it doesn't match the 8 categories exactly, it is rejected. No improvisation.
Supabase (The Schema Holder):
Role: Holds the relational structure and raw data.
Table: student_sessions (and transcripts).
Purpose: This is the "Hub" database that stores the metrics, session IDs, and raw logs defined by the schema.
Sanity (The Destination):
Role: The CMS and presentation layer.
Data: Transcripts and Analysis Reports go here.
Purpose: This is where the "Lesson" objects are created and stored for the frontend to query.
The Guru (Distribution):
Role: The interface/agent (GuruControlCenter, GuruConsole).
Action: It retrieves this validated, stored information from Sanity/Supabase and "distributes" it to the student (Carlos, etc.) via the UI.
I understand this ecosystem. The external modules feed into this pipeline using the strict schema, validated by Pydantic, stored in Supabase, presented via Sanity, and delivered by the Guru. I will not deviate from this.