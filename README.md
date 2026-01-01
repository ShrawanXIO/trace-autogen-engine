# trace-autogen-engine
TRACE (Test Requirements &amp; AI Case Engine) 

Architecture Type: Multi-Agent System (Microsoft AutoGen) 

Goal: Automated generation of high-quality, non-redundant test cases using Retrieval-Augmented Generation (RAG).

The Flow: Story + Scenario -> Search/Draft -> Review -> Output.


trace-stlc-engine/
│
├── data/
│   ├── legacy_knowledge_base.xlsx  # THE GOLD STANDARD (Your reviewed tests)
│   ├── requirements_docs/          # PDFs (The Logic)
│   └── output_test_cases.xlsx      # The Result
│
├── src/
│   ├── agents/
│   │   ├── archivist.py            # Retrieval (Logic + Style)
│   │   ├── author.py               # Drafting (Mimics the Style)
│   │   ├── auditor.py              # Review (Sanity Check)
│   │   └── scribe.py               # Excel Writer
│   │
│   ├── tools/
│   │   ├── vector_db.py            # ChromaDB setup for Excel rows
│   │   └── excel_handler.py        # Read/Write Ops
│   │
│   └── app.py                      # Main AutoGen Flow
│
├── config/
│   ├── prompts.py                  # System Prompts
│   └── settings.json
│
└── README.md


# TRACE: Test Requirements & AI Case Engine

**TRACE** is an AI-driven Quality Assurance assistant designed to automate the drafting of test cases within our STLC (Software Testing Life Cycle).

## 🎯 The Philosophy
We do not want AI to guess. We want it to **replicate our existing quality standards**.
TRACE uses **Retrieval-Augmented Generation (RAG)** to treat our existing, peer-reviewed test cases as "Few-Shot Examples."

**Input:** User Story + QA-Drafted Scenarios.
**Process:**
1.  **Retrieve:** Finds a similar existing test case to use as a "Style Template."
2.  **Draft:** Applies that style (Preconditions, Steps, Cleanup) to the new scenario.
3.  **Review:** Validates against Acceptance Criteria.
**Output:** Production-ready Test Cases in Excel.

## 🏗 System Architecture
- **Framework:** Microsoft AutoGen (Multi-Agent System).
- **Knowledge Base:**
    - `Legacy Tests`: Source of "Experience" (Structure, Cleanup habits).
    - `Requirements`: Source of "Truth" (Business Logic).

## 🚀 Workflow
1.  **PO (Tracy)** provides the Story.
2.  **QA (Shrawan)** defines the Scenarios.
3.  **TRACE Agent** takes the Scenarios and:
    - Checks for duplicates.
    - Retrieves the best matching "Golden Example" from history.
    - Generates the new test case with full depth (Pre-reqs -> Steps -> Cleanup).
4.  **Reviewer** validates the output.

## 🛠 Tech Stack
- **Python 3.10+**
- **AutoGen** (Agent Orchestration)
- **ChromaDB** (Vector Search for finding templates)
- **Pandas** (Excel I/O)

## 📦 Setup
1.  Place your "Gold Standard" test cases in `data/legacy_knowledge_base.xlsx`.
2.  Run `pip install -r requirements.txt`.
3.  Execute `python src/app.py`.