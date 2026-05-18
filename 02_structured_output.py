import anthropic

import json



client = anthropic.Anthropic()



message = client.messages.create(

    model="claude-sonnet-4-20250514",

    max_tokens=1024,

    messages=[

        {

            "role": "user",

            "content": """Extract the following information from this text and return ONLY a JSON object:



Text: John Smith is a 35 year old software engineer from Chennai, India. His email is john@example.com.



Return this exact JSON format:

{

    "name": "",

    "age": 0,

    "occupation": "",

    "city": "",

    "country": "",

    "email": ""

}"""

        }

    ]

)



raw = message.content[0].text

print("Raw response:")

print(raw)



parsed = json.loads(raw)

print("\nParsed values:")

print(f"Name: {parsed['name']}")

print(f"Age: {parsed['age']}")

print(f"City: {parsed['city']}")