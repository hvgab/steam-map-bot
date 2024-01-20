import discord
import os
import workshop


# make a workshop embed from workshopid
def create_workshop_embed(workshopid):
    url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={workshopid}"
    workshop_data = workshop.get_published_file_details(workshopid)
    preview_url = workshop_data["preview_url"]
    title = workshop_data["title"]
    description = workshop_data["description"]
    description += "\n"

    embed = discord.Embed(
        color=None, title=title, url=url, description=description, timestamp=None
    )
    embed.set_image(url=preview_url)
    embed.add_field(name="Link", value=url, inline=False)
    embed.add_field(name="Workshop Id", value=workshopid, inline=False)
    embed.set_footer(text=f"Workshop Id: {workshopid}")

    return embed


# get_workshop_id_from_url
def get_workshop_id_from_url(url):
    workshopid = url.partition(
        "https://steamcommunity.com/sharedfiles/filedetails/?id="
    )[2]
    print(workshopid)
    workshopid = workshopid.partition("&")[0]
    workshopid.strip()
    print(workshopid)
    return workshopid


# Make a client
class MyClient(discord.Client):
    async def on_ready(self):
        print(f"Logged on as {self.user}!")

    async def on_message(self, message):
        print(f"Message from {message.author}: {message.content}")

        # If message is workshop url
        workshop_url = "https://steamcommunity.com/sharedfiles/filedetails/?id="
        if message.content.startswith(workshop_url):
            print(f"Message from {message.author}: {message.content} is a workshop url")

            message.channel.typing()

            workshopid = get_workshop_id_from_url(message.content)
            workshop_data = workshop.get_published_file_details(workshopid)

            thread_name = workshop_data["title"]

            existing_thread = discord.utils.get(message.guild.threads, name=thread_name)

            if existing_thread:
                # Get the embed that has been posted before
                # send thread link
                # send message that created thread
                #  tag user in thread
                #  delete all messages
                original_message = await existing_thread.parent.fetch_message(
                    existing_thread.id
                )

                replies = []
                replies.append(
                    await message.reply(f"Thread {existing_thread.mention} exists.")
                )
                replies.append(
                    await message.reply(
                        f"Original message: {original_message.jump_url} "
                    )
                )

                try:
                    author_is_in_thread = await existing_thread.fetch_member(
                        message.author.id
                    )
                    replies.append(
                        await message.reply(
                            f"{message.author.mention} you are already in the {existing_thread.jump_url} thread..."
                        )
                    )
                except discord.NotFound:
                    replies.append(await message.reply("Tagging you in thread..."))
                    await existing_thread.send(f"{message.author.mention}")

                # Delete conversation
                await message.delete(delay=5)
                for reply in replies:
                    await reply.delete(delay=5)

            if not existing_thread:
                # Create embed, send, add reactions, create thread, delete orignal message
                embed = create_workshop_embed(workshopid)
                embed_msg = await message.channel.send(embed=embed)

                await embed_msg.add_reaction("👍")
                await embed_msg.add_reaction("👎")
                await embed_msg.add_reaction("👩‍👦")
                await embed_msg.add_reaction("👨‍👩‍👧‍👦")

                thread = await embed_msg.create_thread(name=thread_name)

                await message.delete()


# Start the client
intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(os.getenv("discord_token"))
