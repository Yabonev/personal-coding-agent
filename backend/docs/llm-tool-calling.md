# LLM Tool Calling API

## What You Send

### Messages

Array of message objects. Each has a `role` and `content`.

```
role: "system"    → Instructions for the model
role: "user"      → User input
role: "assistant" → Model's previous responses
role: "tool"      → Result of a tool execution
```

Assistant messages can also contain `tool_calls` (when the model invoked tools).

### Tools

Array of tool definitions. Each tool has:

```
name        → Identifier the model uses to call it
description → What the tool does (helps model decide when to use it)
parameters  → JSON Schema defining accepted arguments
```

### Tool Choice

Controls tool usage:

```
"auto"     → Model decides whether to use tools
"none"     → Model cannot use tools
"required" → Model must use at least one tool
{name: X}  → Model must use specific tool X
```

---

## What You Receive

The model responds with either:

1. **Content** - Text response
2. **Tool calls** - Array of tools to execute

Tool call structure:

```
id        → Unique identifier for this call
name      → Which tool to run
arguments → JSON string of parameters
```

The model can return multiple tool calls in one response.

---

## What You Feed Back

After executing tools, add results to message history:

```
role: "tool"
tool_call_id: <id from the tool call>
content: <string result or error message>
```

Then call the API again. The model sees the results and either:

- Responds with content (done)
- Requests more tool calls (loop continues)

---

## The Loop

```
User input
    ↓
Send messages + tools to API
    ↓
Model returns content OR tool_calls
    ↓
If tool_calls:
    Execute each tool
    Add results as "tool" messages
    Go to step 2
Else:
    Done
```

---

## Error Handling

Tool errors go in the `content` field of the tool result message. The model sees error text and can retry or inform the user.

Effective error format: `[What failed]. [What to do].`

Examples:

- `File '/foo.py' not found. Check the path exists.`
- `Invalid timezone 'XYZ'. Use IANA format like 'UTC'.`

---

## Where the Magic Happens

The API structure (messages, tools, roles) is just plumbing. The real leverage is in **content** - the text inside messages.

All context flows through:

- System message content (agent behavior, capabilities, constraints)
- User message content (intent, attached files, environment state)
- Tool result content (data + optional metadata)

### Tool Output as Context

Tools return strings. Smart tools add frontmatter to help the model:

```
[file: /src/main.py]
[lines: 1-50 of 200]
[language: python]

def main():
    ...
```

```
[command: git status]
[exit_code: 0]
[cwd: /project]

On branch main
nothing to commit
```

This metadata costs tokens but possible improves model decisions. The tool controls what context is worth providing.
