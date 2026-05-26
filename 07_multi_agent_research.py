import anthropic
import json

client = anthropic.Anthropic()

def run_specialist_agent(agent_name, task, context=""):
    """Each specialist agent handles one focused research task."""
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=f"""You are a specialist research agent: {agent_name}.
Focus only on your specialty. Be concise and factual.
Return your findings as JSON with these fields:
{{"findings": "your research findings", "confidence": "high|medium|low", "sources_needed": ["list of source types consulted"]}}
Return only raw JSON — no markdown.""",
        messages=[
            {"role": "user", "content": f"Task: {task}\nContext: {context}"}
        ]
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"findings": raw, "confidence": "low", "sources_needed": []}


def reconcile_findings(findings_list):
    """
    Orchestrator reconciles conflicting data from specialist agents.
    This is the key exam concept — NOT last-write-wins!
    """
    findings_text = json.dumps(findings_list, indent=2)

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system="""You are a research orchestrator. Your job is to reconcile findings from multiple specialist agents.

CRITICAL RULES:
1. If agents AGREE — report the consensus finding
2. If agents DISAGREE — flag the conflict explicitly, don't pick one arbitrarily
3. If confidence is LOW — mark as needing verification
4. Never use last-write-wins — always verify conflicts

Return JSON:
{"consensus": {}, "conflicts": [], "needs_verification": [], "final_summary": ""}
Return only raw JSON — no markdown.""",
        messages=[
            {
                "role": "user",
                "content": f"Reconcile these specialist findings:\n{findings_text}"
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
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"final_summary": raw}


def run_multi_agent_research(topic):
    """
    Multi-agent research pipeline:
    1. Specialist agents research in parallel
    2. Orchestrator reconciles findings
    3. Conflicts flagged — not silently resolved
    """
    print(f"\n🔍 Research Topic: {topic}")
    print("=" * 60)

    # Step 1 — Specialist agents research in parallel
    print("\n📊 Step 1: Specialist Agents Researching...")

    market_findings = run_specialist_agent(
        "Market Research Specialist",
        f"Research market size and growth trends for: {topic}"
    )
    print(f"✅ Market Agent: confidence={market_findings.get('confidence')}")

    technical_findings = run_specialist_agent(
        "Technical Research Specialist",
        f"Research technical capabilities and limitations for: {topic}"
    )
    print(f"✅ Technical Agent: confidence={technical_findings.get('confidence')}")

    risk_findings = run_specialist_agent(
        "Risk Assessment Specialist",
        f"Research risks and challenges for: {topic}"
    )
    print(f"✅ Risk Agent: confidence={risk_findings.get('confidence')}")

    # Step 2 — Orchestrator reconciles findings
    print("\n🔄 Step 2: Orchestrator Reconciling Findings...")
    all_findings = {
        "market_research": market_findings,
        "technical_research": technical_findings,
        "risk_assessment": risk_findings
    }

    reconciled = reconcile_findings(all_findings)

    # Step 3 — Report results
    print("\n📋 Step 3: Final Research Report")
    print("-" * 40)

    if reconciled.get("conflicts"):
        print(f"⚠️  Conflicts Found: {len(reconciled['conflicts'])}")
        for conflict in reconciled["conflicts"]:
            print(f"   → {conflict}")

    if reconciled.get("needs_verification"):
        print(f"🔎 Needs Verification: {reconciled['needs_verification']}")

    print(f"\n📝 Summary: {reconciled.get('final_summary', 'No summary available')}")


# Run the multi-agent research system
run_multi_agent_research("AI-powered customer service chatbots for banking sector")
