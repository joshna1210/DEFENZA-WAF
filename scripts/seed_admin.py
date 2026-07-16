"""
Convenience script to create the first admin user directly, without going
through the frontend registration form.

Usage (from backend/ with its venv active):
    python ../scripts/seed_admin.py admin_username admin_password
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services import auth_service  # noqa: E402


async def main():
    if len(sys.argv) != 3:
        print("Usage: python seed_admin.py <username> <password>")
        sys.exit(1)
    username, password = sys.argv[1], sys.argv[2]
    user_id = await auth_service.create_user(username, password, role="admin")
    print(f"Created admin user '{username}' ({user_id})")


if __name__ == "__main__":
    asyncio.run(main())
