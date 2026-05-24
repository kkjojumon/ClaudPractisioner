import anthropic
import json

client = anthropic.Anthropic()

# Define tools the support agent can use
tools = [
    {
        "name": "lookup_account",
        "description": "Look up customer account details by email",
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "Customer email address"
                }
            },
            "required": ["email"]
        }
    },
    {
        "name": "process_refund",
        "description": "Process a refund for a customer order",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order ID to refund"
                },
                "amount": {
                    "type": "number",
                    "description": "Refund amount in USD"
                }
            },
            "required": ["order_id", "amount"]
        }
    },
    {
        "name": "escalate_to_human",
        "description": "Escalate the conversation to a human agent",
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Reason for escalation"
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Escalation priority"
                }
            },
            "required": ["reason", "priority"]
        }
    }
]

# Simulate tool execution
def execute_tool(tool_name, tool_input):
    if tool_name == "lookup_account":
        return {
            "email": tool_input["email"],
            "name": "Jojumon K",
            "account_status": "active",
            "orders": [{"order_id": "ORD-2026-001", "amount": 149.99, "status": "delivered"}]
        }
    elif tool_name == "process_refund":
        return {
            "success": True,
            "order_id": tool_input["order_id"],
            "amount_refunded": tool_input["amount"],
            "message": "Refund processed successfully"
        }
    elif tool_name == "escalate_to_human":
        return {
            "escalated": True,
            "reason": tool_input["reason"],
            "priority": tool_input["priority"],
            "ticket_id": "TKT-9876"
        }

# Agentic loop
def run_support_agent(customer_query):
    print(f"\n👤 Customer: {customer_query}")
    print("-" * 50)

    messages = [{"role": "user", "content": customer_query}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            system="""You are a customer support agent. You have access to tools to:
1. Look up customer accounts
2. Process refunds for delivered orders under $200
3. Escalate to human for complex issues or amounts over $200

Always look up the account first before taking any action.
Escalate if: customer is angry, issue is complex, or refund > $200.""",
            tools=tools,
            messages=messages
        )

        # Check stop reason
        if response.stop_reason == "end_turn":
            # Extract final text response
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"\n🤖 Agent: {block.text}")
            break

        elif response.stop_reason == "tool_use":
            # Process tool calls
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"\n🔧 Using tool: {block.name}")
                    print(f"   Input: {json.dumps(block.input, indent=2)}")

                    result = execute_tool(block.name, block.input)
                    print(f"   Result: {json.dumps(result, indent=2)}")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result)
                    })

            messages.append({"role": "user", "content": tool_results})

# Test the agent
# run_support_agent("Hi, I need a refund for my recent order. My email is jojumon@example.com")
run_support_agent("I am extremely angry! I want a refund of $500 immediately! Email: jojumon@example.com")
