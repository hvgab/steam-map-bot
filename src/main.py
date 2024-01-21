import discord
import os
import workshop

WORKSHOP_URLS = [
    "https://steamcommunity.com/sharedfiles/filedetails/?id=",
    "https://steamcommunity.com/workshop/filedetails/?id=",
]


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
    for workshop_base_url in WORKSHOP_URLS:
        if url.startswith(workshop_base_url):
            workshopid = url.partition(workshop_base_url)[2]
    print(workshopid)
    workshopid = workshopid.partition("&")[0]
    workshopid.strip()
    print(workshopid)
    return workshopid


# Make a client
class MyClient(discord.Client):
    async def init_channel_topic(self):
        # Get workshop-map channel in all guild
        self.WORKSHOP_CHANNEL_NAME = "workshop-maps"
        description = ""
        description += "This channel is just for workshop links. The bot will clean up the channel for all other messages. \n"
        description += "Each map has it's own thread for discussions. \n"
        description += "Use the thumbs up to vote for maps. Use the family emojis to say if the map is best for less than or more than 5 players. \n"
        description += "Workshop Link https://steamcommunity.com/app/730/workshop/ \n"

        for guild in self.guilds:
            print(f"Checking {guild.name} for channel topic")
            workshop_channel = discord.utils.get(
                guild.channels, name=self.WORKSHOP_CHANNEL_NAME
            )
            if workshop_channel.topic != description:
                # Add/Edit description of channel
                print(f"Editing {guild.name}#{workshop_channel.name} topic")
                await workshop_channel.edit(topic=description)

    async def on_ready(self):
        print(f"Logged on as {self.user}!")

        # Set channel topic for WORKSHOP_CHANNEL_NAME in all guilds.
        await self.init_channel_topic()

        for guild in self.guilds:
            print(f"--- {guild} ---")
            for member in guild.members:
                print(member)
            print("\n\n")

    async def on_message(self, message):
        print(f"#{message.channel} - {message.author}: {message.content}")

        # Do not handle messages from bot.
        if message.author == self.user:
            return

        def is_workshop_url(message):
            print(message.content)

            for workshop_url in WORKSHOP_URLS:
                print(workshop_url)
                if message.content.strip().lower().startswith(workshop_url):
                    return True
            return False

        if type(message.channel) == discord.DMChannel:
            workshopid = get_workshop_id_from_url(message.content)
            embed = create_workshop_embed(workshopid)
            embed_msg = await message.reply(embed=embed)
            return

        # If message is in bot's channel delete if not workshop link.
        if message.channel.name == "workshop-maps" and not is_workshop_url(message):
            await self.remove_workshop_channel_message(message)

        # If message is workshop url
        if is_workshop_url(message):
            print(f"Message from {message.author}: {message.content} is a workshop url")
            await self.handle_workshop_url(message)

        # TODO: If someone makes a comment on a map, add all users to thread? Add a comment i channel to hightlight message in thread?

    async def handle_workshop_url(self, message):
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

            # Get the message that started a thread
            original_message = await existing_thread.parent.fetch_message(
                existing_thread.id
            )

            # Save all replies in a list to remove them later
            replies = []

            # If the author is already in the thread, just link.
            # If the author is not in the thread, tag them in it.
            reply_text = ""
            reply_text += f'Workshop map "{thread_name}" ({workshopid}) has already been posted. \n'
            reply_text += f"Original message: {original_message.jump_url}. \n"
            reply_text += f"Thread: {existing_thread.mention}. \n"
            try:
                author = await existing_thread.fetch_member(message.author.id)
                author_is_in_thread = True
                # replies.append(
                #     await message.reply(
                #         f"{message.author.mention} you are already in the {existing_thread.jump_url} thread..."
                #     )
                # )
                # reply_text += f"{message.author.mention} you are already in the {existing_thread.jump_url} thread..."
            except discord.NotFound:
                # replies.append(await message.reply("Tagging you in thread..."))
                reply_text += (
                    f"{message.author.mention} I'm tagging you in the thread. \n"
                )
                await existing_thread.send(f"{message.author.mention}")

            # suppress embeds to avoid discord link embed.
            replies.append(await message.reply(reply_text, suppress_embeds=True))

            # Delete conversation
            await message.delete(delay=15)
            for reply in replies:
                await reply.delete(delay=15)

        if not existing_thread:
            # Create embed, send, add reactions, create thread, delete orignal message

            # Create embed
            embed = create_workshop_embed(workshopid)
            embed_msg = await message.channel.send(embed=embed)

            await embed_msg.add_reaction("👍")
            await embed_msg.add_reaction("👎")
            await embed_msg.add_reaction("👩‍👦")
            await embed_msg.add_reaction("👨‍👩‍👧‍👦")

            # Start thread
            thread = await embed_msg.create_thread(name=thread_name)

            await thread.add_user(message.author)

            # Delete conversation
            await message.delete()

    async def remove_workshop_channel_message(self, message):
        reply = await message.reply(
            f"{message.author.mention} Only workshop links in this channel. Deleting message in 10 sec."
        )
        await message.delete(delay=10)
        await reply.delete(delay=10)


# Start the client
intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(os.getenv("discord_token"))
