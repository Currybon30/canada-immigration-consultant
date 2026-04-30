async def get_all_users(user_collection, include_superadmin=False):
    """
    This function returns all the users from the database.
    """
    users = []
    if include_superadmin:
        async for user in user_collection.find():
            user["_id"] = str(user["_id"])
            users.append(user)
    else:
        async for user in user_collection.find({"is_super_admin": False}):
            user["_id"] = str(user["_id"])
            users.append(user)
    return users

async def get_user_by_username(user_collection, username):
    """
    This function returns the user with the given username.
    """
    user = await user_collection.find_one({"username": username})
    if user:
        user["_id"] = str(user["_id"])
    return user


async def update_user_password(user_collection, username, password):
    """
    This function updates the password of the user with the given username.
    """
    await user_collection.update_one({"username": username}, {"$set": {"hashed_password": password}})
    return {"message": f"Password updated successfully."}

async def delete_user(user_collection, username):
    """
    This function deletes the user with the given username.
    """
    await user_collection.delete_one({"username": username})
    return {"message": f"User {username} deleted successfully."}