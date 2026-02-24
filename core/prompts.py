SUMMARY_SYSTEM_PROMPT = """You are an AI assistant that processes raw thought stream data.
Your task is to analyze unstructured daily thoughts and extract structured information.
Be concise and organized in your output."""


SUMMARY_PROMPT_TEMPLATE = """Analyze the following raw thought stream from my day.
Extract and organize the information into these categories:

1. **Journal Entries** - Key thoughts, reflections, or discussions
2. **Action Items** - Tasks, todo items, or things I need to do
3. **Technical Ideas** - Technical concepts, code ideas, or learnings

Format your response as clean Markdown.

Raw thought stream:
```
{content}
```

Provide a structured summary:"""


ACTION_ITEMS_PROMPT_TEMPLATE = """From the following thought stream, extract ONLY the action items/tasks.
Return them as a bullet list. If none exist, say "No action items found."

Thought stream:
```
{content}
```
"""


TECHNICAL_IDEAS_PROMPT_TEMPLATE = """From the following thought stream, extract ONLY technical ideas, concepts, or code-related thoughts.
Return them as a bullet list. If none exist, say "No technical ideas found."

Thought stream:
```
{content}
```
"""


def get_summary_prompt(content: str) -> str:
    """Generate summary prompt with content."""
    return SUMMARY_PROMPT_TEMPLATE.format(content=content)


def get_action_items_prompt(content: str) -> str:
    """Generate action items extraction prompt."""
    return ACTION_ITEMS_PROMPT_TEMPLATE.format(content=content)


def get_technical_ideas_prompt(content: str) -> str:
    """Generate technical ideas extraction prompt."""
    return TECHNICAL_IDEAS_PROMPT_TEMPLATE.format(content=content)
