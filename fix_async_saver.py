#!/usr/bin/env python3
"""Script to fix the AsyncPostgresSaver initialization"""
import re

file_path = "/home/chris/PAT02/ai-services/langgraph/graphs/conversation_graph.py"

with open(file_path, 'r') as f:
    content = f.read()

# Find and replace the problematic initialization pattern
old_pattern = r'''            # Configurar checkpointer con PostgreSQL
            self.checkpointer = AsyncPostgresSaver.from_conn_string\(self.database_url\)
            async with self.checkpointer as checkpointer:
                await checkpointer.setup\(\)'''

new_code = '''            # Configurar checkpointer con PostgreSQL
            # from_conn_string returns an async context manager, we need to enter it once
            # and keep it alive for the application lifetime
            checkpointer_cm = AsyncPostgresSaver.from_conn_string(self.database_url)
            self.checkpointer = await checkpointer_cm.__aenter__()
            # Store the context manager so we can properly exit it during cleanup
            self._checkpointer_cm = checkpointer_cm
            await self.checkpointer.setup()'''

content = re.sub(old_pattern, new_code, content)

# Also need to update the cleanup method to properly exit the context manager
cleanup_old = r'            # Limpiar checkpointer\r\n            if self.checkpointer:\r\n                # El checkpointer se limpia automáticamente\r\n                pass'

cleanup_new = '''            # Limpiar checkpointer
            if self.checkpointer and hasattr(self, '_checkpointer_cm'):
                try:
                    await self._checkpointer_cm.__aexit__(None, None, None)
                except Exception:
                    pass'''

content = re.sub(cleanup_old, cleanup_new, content)

with open(file_path, 'w') as f:
    f.write(content)

print("File updated successfully")
