"""
Schema reference for `users` collection.

{
  "_id": ObjectId,
  "username": str,
  "hashed_password": str,
  "role": str,   # "admin" | "soc_analyst"
  "created_at": datetime,
}
"""
