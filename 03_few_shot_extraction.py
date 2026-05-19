import anthropic
import json

client = anthropic.Anthropic()

# Few-shot examples teach Claude different invoice layouts
few_shot_examples = """
Example 1 - Standard Layout:
Invoice Text: "INVOICE #INV-001 | Vendor: ABC Supplies | Date: 01/05/2026 | Amount Due: $1,250.00"
Output: {"invoice_number": "INV-001", "vendor": "ABC Supplies", "date": "01/05/2026", "amount": 1250.00}

Example 2 - Free Form Layout:
Invoice Text: "Bill from XYZ Corp dated March 3 2026. Total payable: rupees 45000. Ref: XYZ/2026/789"
Output: {"invoice_number": "XYZ/2026/789", "vendor": "XYZ Corp", "date": "03/03/2026", "amount": 45000.00}

Example 3 - Missing Field:
Invoice Text: "Supplier: Tech Parts Ltd | Amount: $890 | Invoice Ref: TP-456"
Output: {"invoice_number": "TP-456", "vendor": "Tech Parts Ltd", "date": null, "amount": 890.00}
"""

# Real invoice to extract
invoice_text = """
From: Global Traders Inc
Invoice No: GT/MAY/2026/1042
Issued: 19th May 2026
Total Amount Payable: USD 3,750.50
"""

message = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    system="You are an invoice extraction specialist. Return only raw JSON. No markdown. No explanation.",
    messages=[
        {
            "role": "user",
            "content": f"""Extract invoice fields from the text below.
Use these examples as guidance:

{few_shot_examples}

Now extract from this invoice:
{invoice_text}

Return JSON with these fields:
{{"invoice_number": "", "vendor": "", "date": "", "amount": 0.0}}

Use null for any missing fields."""
        }
    ]
)



raw = message.content[0].text.strip()
if raw.startswith("```"):
    raw = raw.split("```")[1]
    if raw.startswith("json"):
        raw = raw[4:]
    raw = raw.strip()

print("Raw response:")
print(raw)

# Validate and parse
try:
    parsed = json.loads(raw)
    print("\n✅ Extraction successful!")
    print(f"Invoice Number : {parsed['invoice_number']}")
    print(f"Vendor         : {parsed['vendor']}")
    print(f"Date           : {parsed['date']}")
    print(f"Amount         : {parsed['amount']}")
except json.JSONDecodeError as e:
    print(f"\n❌ JSON parsing failed: {e}")
    print("→ Would trigger retry loop in production")
    