# Code Style Rules

## General Principles
- Clean, professional code
- Clear and concise
- Production-ready standards

## Forbidden

### NO EMOJIS
**NEVER use emojis in code, comments, or output strings.**

❌ Bad:
```python
print("✅ Success!")
print("🔥 Hot data!")
logger.info("📊 Processing...")
```

✓ Good:
```python
print("SUCCESS: Operation completed")
print("Processing high-priority data")
logger.info("Processing data batch")
```

### Output Messages
Use clear status prefixes instead of emojis:
- `SUCCESS:` for successful operations
- `ERROR:` for errors
- `WARNING:` for warnings
- `INFO:` for informational messages
- `DEBUG:` for debug output

### Comments
Keep comments professional and emoji-free:

❌ Bad:
```python
# 🚀 This function is super fast!
# ⚠️ Be careful here
# 💡 Smart optimization
```

✓ Good:
```python
# Optimized for performance - O(log n) complexity
# Note: This operation modifies the original array
# Algorithm explanation: uses binary search
```

## Why?
1. **Professionalism** - Production code should look professional
2. **Compatibility** - Emojis can cause encoding issues
3. **Readability** - Text is clearer and more searchable
4. **Logs** - Server logs with emojis look unprofessional
5. **Terminal** - Some terminals don't render emojis properly

## Apply to:
- Python code
- JavaScript/TypeScript code
- Log messages
- Error messages
- Comments
- Docstrings
- README files (exception: if purely decorative in headings)
- Commit messages

## Enforcement
All code reviews should check for emoji violations and request removal.
