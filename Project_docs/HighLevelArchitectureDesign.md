# High-Level Design (HLD): The Architecture
The system is designed as a Retrieval-Augmented Generation (RAG) pipeline. It sits between the User (QA) and the Output (Test Management System).

## Core Components
### The Interface Layer:
Input: Accepts **User Stories + List of Scenarios.**
Output: A CSV/Excel file ready for import into Azure DevOps (ADO).

### The Knowledge Engine (The "Brain"):
Source A (Legacy Data): A CSV export of your existing Test Repository. This acts as both the "Duplicate Checker" and the "Style Guide."
Source B (Documentation): Parsed Requirements (PDFs/Text) that provide the Source of Truth for business logic.
Vector Engine: A semantic search layer (embedding model) that understands the meaning of a scenario, not just keywords.

### The Agent Logic Layer:
The Orchestrator: Manages the workflow state.
The Detective (Search): Decides if a test exists or needs creation.
The Drafter (GenAI): Creates content using specific templates.
The Reviewer (QA): Validates against Acceptance Criteria.