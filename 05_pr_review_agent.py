import anthropic
import json

client = anthropic.Anthropic()

# Shared system prompt — enforced at integration layer
# This ensures ALL developers get consistent PR reviews
SHARED_SYSTEM_PROMPT = """You are an expert code reviewer. Review every PR with the same structure:

1. SECURITY: Identify any security vulnerabilities (SQL injection, XSS, hardcoded secrets)
2. PERFORMANCE: Flag performance issues (N+1 queries, inefficient loops, memory leaks)
3. CODE QUALITY: Check naming, readability, and best practices
4. BUGS: Identify logical errors or edge cases not handled
5. SUGGESTION: One key improvement recommendation

Always return your review as JSON in this exact format:
{
    "security": {"issues": [], "severity": "none|low|medium|high"},
    "performance": {"issues": [], "severity": "none|low|medium|high"},
    "code_quality": {"issues": [], "severity": "none|low|medium|high"},
    "bugs": {"issues": [], "severity": "none|low|medium|high"},
    "suggestion": "",
    "overall_rating": "approve|request_changes|reject"
}"""

def review_pr(developer_name, code_diff):
    """
    Reviews a PR — same quality regardless of which developer submits.
    System prompt enforced at integration layer, not left to developer.
    """
    print(f"\n👨‍💻 Developer: {developer_name}")
    print(f"📝 Reviewing code diff...")
    print("-" * 50)

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=SHARED_SYSTEM_PROMPT,  # Always applied — developer can't override
        messages=[
            {
                "role": "user",
                "content": f"Review this code change:\n\n{code_diff}"
            }
        ]
    )

    raw = response.content[0].text

    # Strip markdown if present
    if raw.strip().startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        review = json.loads(raw)
        print(f"🔒 Security    : {review['security']['severity'].upper()}")
        print(f"⚡ Performance : {review['performance']['severity'].upper()}")
        print(f"📖 Code Quality: {review['code_quality']['severity'].upper()}")
        print(f"🐛 Bugs        : {review['bugs']['severity'].upper()}")
        print(f"💡 Suggestion  : {review['suggestion']}")
        print(f"✅ Decision    : {review['overall_rating'].upper()}")

        if review['security']['issues']:
            print(f"\n⚠️  Security Issues:")
            for issue in review['security']['issues']:
                print(f"   - {issue}")

    except json.JSONDecodeError:
        print("❌ Review parsing failed")
        print(raw)

# Simulate two developers submitting PRs
# Both get same quality review regardless of their prompting skills

# Developer 1 — submits good code
review_pr("Alice", """
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
""")

# Developer 2 — submits code with issues
review_pr("Bob", """
def calculate_total(items):
    total = 0
    for item in items:
        product = db.get_product(item.id)  # DB call in loop!
        total += product.price * item.quantity
    return total
""")