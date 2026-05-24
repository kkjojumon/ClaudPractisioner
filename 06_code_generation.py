import anthropic
import json

client = anthropic.Anthropic()

# ─── WRONG WAY (No schema context) ───
def generate_migration_wrong(requirement):
    """
    Bad practice — no schema context provided.
    Claude has to guess the schema — may silently drop columns!
    """
    print("\n❌ WRONG WAY — No Schema Context")
    print("-" * 50)

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system="You are a database migration expert. Generate PostgreSQL migration scripts.",
        messages=[
            {
                "role": "user",
                "content": requirement
            }
        ]
    )
    print(response.content[0].text)


# ─── RIGHT WAY (With schema context + explicit constraints) ───
def generate_migration_correct(requirement):
    """
    Good practice — full schema context + explicit constraints.
    Claude knows exactly what exists and what must be preserved.
    """
    print("\n✅ RIGHT WAY — With Schema Context & Constraints")
    print("-" * 50)

    # Full current schema provided as context
    current_schema = """
    Current table: users
    Columns:
    - id: SERIAL PRIMARY KEY
    - email: VARCHAR(255) NOT NULL UNIQUE
    - name: VARCHAR(100) NOT NULL
    - phone: VARCHAR(20) NULLABLE        ← must be preserved!
    - bio: TEXT NULLABLE                 ← must be preserved!
    - created_at: TIMESTAMP DEFAULT NOW()
    - deleted_at: TIMESTAMP NULLABLE     ← soft delete column, must be preserved!
    
    Indexes:
    - idx_users_email (email)
    - idx_users_created_at (created_at)
    """

    explicit_constraints = """
    STRICT RULES — never violate these:
    1. NEVER drop any existing column
    2. NEVER change existing column data types
    3. ALWAYS preserve all NULLABLE columns
    4. ALWAYS preserve all existing indexes
    5. Only ADD new columns or indexes — never remove
    6. Make migration idempotent (use IF NOT EXISTS)
    7. Include a rollback section
    """

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        system=f"""You are a database migration expert for PostgreSQL.
        
Current Schema:
{current_schema}

{explicit_constraints}

Always structure output as:
-- MIGRATION UP
[migration SQL here]

-- MIGRATION DOWN (rollback)
[rollback SQL here]

-- VERIFICATION
[SQL to verify migration succeeded]""",
        messages=[
            {
                "role": "user",
                "content": requirement
            }
        ]
    )
    print(response.content[0].text)


# ─── PLAN MODE SIMULATION ───
def generate_migration_with_plan(requirement):
    """
    Best practice — generate plan first, then migration.
    Human reviews plan before any changes are made.
    """
    print("\n🎯 BEST PRACTICE — Plan Mode First")
    print("-" * 50)

    current_schema = """
    Current table: users
    Columns: id, email, name, phone (nullable), bio (nullable), 
             created_at, deleted_at (nullable)
    """

    # Step 1 — Generate plan first
    plan_response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system="You are a database migration expert.",
        messages=[
            {
                "role": "user",
                "content": f"""Before writing any SQL, create a migration PLAN only.
                
Current schema: {current_schema}
Requirement: {requirement}

List exactly:
1. What columns will be ADDED
2. What columns will be MODIFIED  
3. What columns will be REMOVED
4. What indexes will change
5. Estimated risk level: LOW/MEDIUM/HIGH

Do NOT write SQL yet — plan only."""
            }
        ]
    )

    print("📋 MIGRATION PLAN (review before executing):")
    print(plan_response.content[0].text)
    print("\n⚠️  Human review required before proceeding!")


# Run all three approaches
requirement = "Add a username column and a last_login timestamp to the users table"

generate_migration_wrong(requirement)
generate_migration_correct(requirement)
generate_migration_with_plan(requirement)
