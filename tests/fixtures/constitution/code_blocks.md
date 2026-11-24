# Document with Code Blocks

This document has content inside code blocks that should be ignored.

## Regular Content

This line mentions AI correctly.

## Code Examples

```python
# This should NOT trigger a violation - it's in a code block
def claude_integration():
    """Integration with Claude API."""
    return "claude"
```

```javascript
// Also should NOT trigger - code block
const cursorRules = {
    enabled: true
};
```

## After Code Blocks

This line also mentions AI correctly.

## Inline Code

The variable `claude_config` should not trigger because it's inline code.
But this text about Claude should trigger a violation.

## Another Code Block

```markdown
# Nested markdown example
Use Claude for best results.
```

This text after the code block should be scanned normally.
The AI assistant helps with development.
