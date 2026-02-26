SYSTEM_PROMPT = """You are a helpful AI assistant that helps organize thoughts into a knowledge graph.
You extract structured information from unstructured text and respond in JSON format."""

ENTITY_EXTRACTION_PROMPT = """Analyze the following daily notes and extract any mentioned:
1. Projects - any work projects, personal projects, or ongoing tasks
2. People - any people mentioned (colleagues, friends, family)
3. Ideas - any ideas, concepts, or thoughts

Respond ONLY with valid JSON in this format:
{{
    "projects": [{{"name": "project name", "context": "brief context"}}],
    "people": [{{"name": "person name", "context": "brief context"}}],
    "ideas": [{{"name": "idea", "context": "brief context"}}]
}}

If nothing found, respond with empty arrays:
{{"projects": [], "people": [], "ideas": []}}

Daily notes:
{daily_content}"""

ASK_VAULT_PROMPT = """Based on the following context from the user's vault, answer their question.

Context:
{vault_context}

Question: {user_question}

Provide a clear, helpful answer based only on the context provided. If the context doesn't contain enough information to answer the question, say so."""
