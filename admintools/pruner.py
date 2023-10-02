# import os
# import sys

# project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# sys.path.append(project_root)

# from api.db.users import UserManager

# manager = UserManager()

# async def update_credits(settings=None):
#     users = await manager.get_all_users()

#     if not settings:
#         await users.update_many({}, {'$inc': {'credits': 2500}})

#     else:
#         for key, value in settings.items():
#             await users.update_many(
#                 {'level': key}, {'$inc': {'credits': int(value)}})

# get_all_users = manager.get_all_users


# ###

# import os
# import time
# import aiohttp
# import pymongo
# import asyncio
# import autocredits

# from settings import roles
# from dotenv import load_dotenv

# load_dotenv()

# async def main():
#     await update_roles()
#     await autocredits.update_credits(roles)

# async def update_roles():
#     async with aiohttp.ClientSession() as session:
#         try:
#             async with session.get('http://0.0.0.0:3224/user_ids') as response:
#                 discord_users = await response.json()
#         except aiohttp.ClientError as e:
#             print(f'Error: {e}')
#             return

#     level_role_names = [f'lvl{lvl}' for lvl in range(10, 110, 10)]
#     users_doc = await autocredits.get_all_users()
#     users = users_doc.find({})
#     users = await users.to_list(length=None)


#     for user in users:
#         if not 'auth' in user:
#             continue

#         discord = str(user['auth']['discord'])

#         for user_id, role_names in discord_users.items():
#             if user_id == discord:
#                 for role in level_role_names:
#                     if role in role_names:
#                         users_doc.update_one(
#                             {'auth.discord': discord},
#                             {'$set': {'level': role}}
#                         )

#                         print(f'Updated {discord} to {role}')

#     return users

# def launch():
#     asyncio.run(main())

#     with open('rewards/last_update.txt', 'w', encoding='utf8') as f:
#         f.write(str(time.time()))

# # ====================================================================================

# if __name__ == '__main__':
#     launch()
