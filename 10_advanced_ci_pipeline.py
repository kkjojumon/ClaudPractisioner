import anthropic
import json
import os

client = anthropic.Anthropic()

# ─── ALLOWLIST — Security by default ───
ALLOWED_FILES = ["src/utils.py", "src/helpers.py", "tests/test_utils.py"]
SENSITIVE_FILES = [".env", "config/secrets.yml", "deployment/keys/"]

def is_allowed(file_path):
    """Allowlist check — Claude can ONLY touch permitted files."""
    for allowed in ALLOWED_FILES:
        if file_path == allowed or file_path.startswith(allowed):
            return True
    return False


# ─── PRE-HOOK: Validate scope before Claude acts ───
def pre_hook_validate_scope(files_to_modify):
    """
    Pre-hook: runs BEFORE Claude modifies files.
    Blocks if any file is outside allowlist.
    """
    print("\n🔍 Pre-Hook: Validating scope...")
    violations = []
    for f in files_to_modify:
        if not is_allowed(f):
            violations.append(f)

    if violations:
        print(f"❌ Pre-Hook BLOCKED — files outside allowlist: {violations}")
        return False

    print(f"✅ Pre-Hook passed — all files in allowlist")
    return True


# ─── POST-HOOK: Run tests after Claude modifies files ───
def post_hook_run_tests(modified_files):
    """
    Post-hook: runs AFTER Claude modifies files.
    Simulates test execution — blocks if tests fail.
    """
    print("\n🧪 Post-Hook: Running tests...")
    # Simulate test results
    test_results = {
        "src/utils.py": True,   # tests pass
        "src/helpers.py": False, # tests fail!
        "tests/test_utils.py": True
    }

    failed = []
    for f in modified_files:
        if f in test_results and not test_results[f]:
            failed.append(f)

    if failed:
        print(f"❌ Post-Hook BLOCKED — tests failed for: {failed}")
        print("🔄 Triggering git rollback...")
        return False

    print("✅ Post-Hook passed — all tests passing")
    return True


# ─── IDEMPOTENT LINT FIXER ───
def fix_lint_idempotent(file_path, code, lint_errors):
    """
    Idempotent lint fixer — running multiple times gives same result.
    Only fixes what's flagged — never improves already-correct code.
    """
    print(f"\n🔧 Fixing lint errors in: {file_path}")
    print(f"   Errors to fix: {[e['rule'] for e in lint_errors]}")

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system="""You are an idempotent lint fixer for CI/CD pipelines.

IDEMPOTENCY RULES:
1. ONLY fix the specific lint errors listed — nothing else
2. If code already follows the rule → make NO change
3. Never 'improve' code that isn't flagged
4. Running this twice should give identical output

Return JSON only:
{
    "fixed_code": "corrected code here",
    "changes_made": ["description of each change"],
    "already_correct": ["rules that were already satisfied"]
}
No markdown.""",
        messages=[{
            "role": "user",
            "content": f"""File: {file_path}
Lint errors to fix: {json.dumps(lint_errors)}
Code:
{code}"""
        }]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        result = json.loads(raw)
        print(f"   ✅ Changes: {result.get('changes_made', [])}")
        if result.get('already_correct'):
            print(f"   ℹ️  Already correct: {result.get('already_correct', [])}")
        return result
    except json.JSONDecodeError:
        print(f"   ❌ Parse error")
        return None


# ─── FULL CI PIPELINE WITH ALL GUARDRAILS ───
def run_ci_pipeline_advanced(pipeline_name, files_to_fix):
    """
    Production CI pipeline:
    Stage 1: Pre-hook scope validation
    Stage 2: Idempotent lint fixing
    Stage 3: Post-hook test gate
    Stage 4: Changeset size check
    Stage 5: Deploy gate
    """
    print(f"\n{'='*60}")
    print(f"🚀 CI Pipeline: {pipeline_name}")
    print(f"{'='*60}")

    completed_stages = []
    pipeline_blocked = False
    block_reason = ""

    # ── Stage 1: Pre-hook validation ──
    print("\n📋 Stage 1: Pre-Hook Scope Validation")
    file_paths = [f["path"] for f in files_to_fix]
    if not pre_hook_validate_scope(file_paths):
        pipeline_blocked = True
        block_reason = "Files outside allowlist"
    else:
        completed_stages.append("Stage 1: Scope Validation ✅")

    if pipeline_blocked:
        print(f"\n🚫 Pipeline BLOCKED at Stage 1: {block_reason}")
        return False

    # ── Stage 2: Idempotent lint fixing ──
    print("\n📋 Stage 2: Idempotent Lint Fixing")
    fix_results = []
    for file_info in files_to_fix:
        result = fix_lint_idempotent(
            file_info["path"],
            file_info["code"],
            file_info["lint_errors"]
        )
        if result:
            fix_results.append({
                "path": file_info["path"],
                "result": result
            })
    completed_stages.append("Stage 2: Lint Fixing ✅")

    # ── Stage 3: Post-hook test gate ──
    print("\n📋 Stage 3: Post-Hook Test Gate")
    modified_files = [f["path"] for f in files_to_fix]
    if not post_hook_run_tests(modified_files):
        pipeline_blocked = True
        block_reason = "Tests failed after lint fixes"
        completed_stages.append("Stage 3: Test Gate ❌")
    else:
        completed_stages.append("Stage 3: Test Gate ✅")

    # ── Stage 4: Changeset size check ──
    print("\n📋 Stage 4: Changeset Size Check")
    if not pipeline_blocked:
        total_changes = sum(
            len(r["result"].get("changes_made", []))
            for r in fix_results
        )
        if total_changes > 10:
            print(f"⚠️  Large changeset ({total_changes}) — requires human approval")
            pipeline_blocked = True
            block_reason = "Changeset too large"
        else:
            print(f"✅ Changeset size OK ({total_changes} changes)")
            completed_stages.append("Stage 4: Changeset Check ✅")

    # ── Stage 5: Deploy gate ──
    print("\n📋 Stage 5: Deploy Gate")
    if pipeline_blocked:
        print(f"🚫 Deploy BLOCKED — {block_reason}")
        print(f"\n📊 Completed stages preserved:")
        for stage in completed_stages:
            print(f"   {stage}")
        return False
    else:
        print("✅ All gates passed — ready to deploy!")
        completed_stages.append("Stage 5: Deploy ✅")

    print(f"\n📊 Pipeline Summary:")
    for stage in completed_stages:
        print(f"   {stage}")
    return True


# ─── TEST THE PIPELINE ───

# Test 1 — Normal pipeline (src/utils.py passes tests)
run_ci_pipeline_advanced("Normal Lint Fix", [
    {
        "path": "src/utils.py",
        "code": "def calculate(x,y):\n    result=x+y\n    return result",
        "lint_errors": [
            {"rule": "E231", "line": 1, "message": "missing whitespace after ','"},
            {"rule": "E225", "line": 2, "message": "missing whitespace around operator"}
        ]
    }
])

# Test 2 — Security violation (sensitive file in scope)
run_ci_pipeline_advanced("Security Violation Test", [
    {
        "path": ".env",
        "code": "API_KEY=secret123",
        "lint_errors": []
    }
])
