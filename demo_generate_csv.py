"""
Demo: shows a real Author -> Scribe run with a sample user story.
Run with: python demo_generate_csv.py
"""
import sys
import os

sys.path.append(os.path.join(os.getcwd(), "src"))

# --- Sample user story ---
SAMPLE_INPUT = """
Feature: User Login

Background:
  - The application has a login page with Username and Password fields.
  - Passwords must be at least 8 characters long.
  - After 3 consecutive failed attempts the account is locked for 15 minutes.

Acceptance Criteria:
  - Valid credentials log the user in and redirect to the Dashboard.
  - Invalid credentials show an error: "Invalid username or password."
  - Empty fields show a validation message: "This field is required."
  - A locked account shows: "Account locked. Try again in 15 minutes."

Scenarios:
  1. Login with valid username and password.
  2. Login with valid username but wrong password.
  3. Login with empty username field.
  4. Login with empty password field.
  5. Account lockout after 3 failed login attempts.
"""

print("=" * 60)
print("TRACE STLC Engine - Sample CSV Demo")
print("=" * 60)
print("\n[INPUT] User story loaded. Initiating Author agent...\n")

from agents.author import Author
from agents.scribe import Scribe

author = Author()
scribe = Scribe()

context = """
- Passwords must be at least 8 characters.
- After 3 failed attempts, account is locked for 15 minutes.
- Valid login redirects to the Dashboard.
- Error message on failure: "Invalid username or password."
- Locked account message: "Account locked. Try again in 15 minutes."
- Empty field validation: "This field is required."
"""

print("[Author] Writing test cases...\n")
draft = author.write(
    topic="""
1. Login with valid username and password.
2. Login with valid username but wrong password.
3. Login with empty username field.
4. Login with empty password field.
5. Account lockout after 3 failed login attempts.
""",
    context=context
)

def safe_print(text):
    """Print text, replacing non-cp1252 chars with ASCII equivalents."""
    replacements = {
        "→": "->", "←": "<-", "—": "-", "–": "-",
        "‘": "'", "’": "'", "“": '"', "”": '"',
        "•": "*", "…": "...", "·": "*",
    }
    for char, sub in replacements.items():
        text = text.replace(char, sub)
    print(text.encode("cp1252", errors="replace").decode("cp1252"))

print("\n[Author Output - Raw Test Cases]\n" + "-" * 40)
safe_print(draft)
print("-" * 40)

print("\n[Scribe] Formatting as CSV...\n")
result = scribe.save(draft)
print(f"\n[Scribe Result] {result}")

if result.startswith("Success"):
    filepath = result.split(": ", 1)[1].strip()
    print("\n[CSV File Contents]\n" + "=" * 60)
    with open(filepath, "r", encoding="utf-8") as f:
        safe_print(f.read())
    print("=" * 60)
    print(f"\nFile saved at: {filepath}")
