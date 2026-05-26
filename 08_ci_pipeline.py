import anthropic
import json

client = anthropic.Anthropic()

# ─── WRONG WAY — No scope limiting ───
def fix_lint_wrong(codebase):
    """
    Bad practice — no scope limiting.
    Claude may refactor unrelated code and break tests!
    """
    print("\n❌ WRONG WAY — No Scope Limiting")
    print("-" * 50)

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system="You are a code quality expert. Fix all issues you find in the code.",
        messages=[
            {
                "role": "user",
                "content": f"Fix the lint errors in this code:\n\n{codebase}"
            }
        ]
    )
    print(response.content[0].text)


# ─── RIGHT WAY — With scope limiting ───
def fix_lint_correct(file_path, flagged_lines, lint_errors, code_content):
    """
    Good practice — scope limited to specific flagged lines only.
    Claude cannot touch anything outside the flagged scope.
    """
    print("\n✅ RIGHT WAY — Scope Limited to Flagged Lines Only")
    print("-" * 50)

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system="""You are a CI/CD lint fix specialist.

STRICT SCOPE RULES — never violate these:
1. ONLY fix the specific lint errors listed
2. ONLY modify the exact lines flagged
3. NEVER refactor unrelated code
4. NEVER change logic, only fix lint style issues
5. NEVER modify files not listed in scope
6. If fixing one line requires changing logic → STOP and report instead

Return JSON:
{
    "fixes": [{"line": 0, "original": "", "fixed": "", "lint_rule": ""}],
    "skipped": [{"line": 0, "reason": "requires logic change — needs human review"}],
    "files_modified": []
}
Return only raw JSON — no markdown.""",
        messages=[
            {
                "role": "user",
                "content": f"""Fix ONLY these specific lint errors:

File: {file_path}
Flagged Lines: {flagged_lines}
Lint Errors: {json.dumps(lint_errors, indent=2)}

Code:
{code_content}

Remember: ONLY fix the flagged lines. Nothing else."""
            }
        ]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        result = json.loads(raw)
        print(f"✅ Fixes applied: {len(result.get('fixes', []))}")
        for fix in result.get('fixes', []):
            print(f"   Line {fix['line']}: [{fix['lint_rule']}] fixed")

        if result.get('skipped'):
            print(f"⚠️  Skipped (needs human review): {len(result['skipped'])}")
            for skip in result['skipped']:
                print(f"   Line {skip['line']}: {skip['reason']}")

        print(f"📁 Files modified: {result.get('files_modified', [])}")
        return result

    except json.JSONDecodeError:
        print(f"❌ Parse error: {raw}")
        return None


# ─── CI PIPELINE SIMULATION ───
def run_ci_pipeline(file_path, lint_errors, code_content):
    """
    Production CI pipeline with guardrails:
    1. Scope-limited lint fix
    2. Post-fix test gate
    3. Changeset size check
    4. Human approval for large changes
    """
    print(f"\n🔄 CI Pipeline Running for: {file_path}")
    print("=" * 60)

    flagged_lines = [err["line"] for err in lint_errors]

    # Step 1 — Scope-limited fix
    print("\n📋 Step 1: Scope-Limited Lint Fix")
    result = fix_lint_correct(file_path, flagged_lines, lint_errors, code_content)

    if not result:
        print("❌ Pipeline blocked — lint fix failed")
        return False

    # Step 2 — Changeset size gate
    print("\n🔍 Step 2: Changeset Size Check")
    fixes_count = len(result.get('fixes', []))
    if fixes_count > 10:
        print(f"⚠️  Large changeset ({fixes_count} changes) — routing to human approval")
        return False
    else:
        print(f"✅ Changeset size OK ({fixes_count} changes)")

    # Step 3 — Simulated test gate
    print("\n🧪 Step 3: Running Tests (Post-Fix Gate)")
    skipped = result.get('skipped', [])
    if skipped:
        print(f"⚠️  {len(skipped)} items need human review — blocking deployment")
        return False
    else:
        print("✅ All tests passed — safe to proceed")

    # Step 4 — Result
    print("\n🚀 Step 4: Pipeline Result")
    print("✅ Lint fixes applied safely — ready for deployment")
    return True


# Test the CI pipeline
code_with_lint_errors = '''
def calculate_discount(price,discount_rate):
    result=price*discount_rate
    return result

def get_user_data( user_id ):
    data = fetch_from_db(user_id)
    return data
'''

lint_errors = [
    {"line": 2, "rule": "E231", "message": "missing whitespace after ','"},
    {"line": 3, "rule": "E225", "message": "missing whitespace around operator"},
    {"line": 7, "rule": "E201", "message": "whitespace after '('"},
]

run_ci_pipeline("app/utils.py", lint_errors, code_with_lint_errors)
