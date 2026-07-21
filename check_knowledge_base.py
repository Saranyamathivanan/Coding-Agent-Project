"""
Quick helper to peek inside the vector database used by coding_agent.py.

Run this any time you want to see how many error/fix pairs have been stored
so far, and a short preview of each one.

Run:
    python check_knowledge_base.py
"""

from __future__ import annotations

from coding_agent import get_collection


def main() -> None:
    """Print how many entries are stored and a short preview of each one."""
    collection = get_collection()
    count = collection.count()

    print(f"Entries in the knowledge base: {count}")

    if count == 0:
        print("Nothing stored yet -- run coding_agent.py on a task that fails")
        print("and then gets fixed, and an entry will be added.")
        return

    all_entries = collection.get()
    for i, (entry_id, error_text) in enumerate(
        zip(all_entries["ids"], all_entries["documents"]), start=1
    ):
        preview = error_text.strip().replace("\n", " ")[:120]
        print(f"\n{i}. [{entry_id}]")
        print(f"   error: {preview}...")


if __name__ == "__main__":
    main()
