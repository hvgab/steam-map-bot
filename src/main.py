import discord
import os
import workshop

WORKSHOP_URLS = [
    "https://steamcommunity.com/sharedfiles/filedetails/?id=",
    "https://steamcommunity.com/workshop/filedetails/?id=",
]

CHANNEL_NAME = "workshop-maps"

WORKSHOP_CONTRIBUTER_ROLE = "🪖 Workshop Contributer!"


# make a workshop embed from workshopid
def create_workshop_embed(workshopid):
    url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={workshopid}"
    workshop_data = workshop.get_published_file_details(workshopid)
    preview_url = workshop_data["preview_url"]
    title = workshop_data["title"]
    description = workshop_data["description"]
    description += "\n"

    embed = discord.Embed(title=title, url=url, description=description, timestamp=None)
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
    def is_workshop_url(self, message):
        print(message.content)

        for workshop_url in WORKSHOP_URLS:
            print(workshop_url)
            if message.content.strip().lower().startswith(workshop_url):
                return True
        return False

    async def init_channel_topic(self):
        # Get workshop-map channel in all guild
        self.WORKSHOP_CHANNEL_NAME = "workshop-maps"
        description = ""
        description += "This channel is just for workshop links. The bot will clean up the channel for all other messages. "
        description += "Each map has it's own thread for discussions. "
        description += "Use the thumbs up to vote for maps. Use the family emojis to say if the map is best for less than or more than 5 players. "
        description += "Workshop Link https://steamcommunity.com/app/730/workshop/ "
        description = description.strip()

        for guild in self.guilds:
            print(f"Checking '{guild.name}' for channel topic")
            workshop_channel = discord.utils.get(
                guild.channels, name=self.WORKSHOP_CHANNEL_NAME
            )
            if workshop_channel.topic != description:
                # Add/Edit description of channel
                print(f"Editing '{guild.name}' '#{workshop_channel.name}' topic")
                print()
                print(workshop_channel.topic)
                print()
                print(description)
                await workshop_channel.edit(topic=description)

    async def on_ready(self):
        print(f"Logged on as {self.user}!")

        print(f"Guilds for {self.user}:")
        for guild in self.guilds:
            print(f"- {guild}")
        print()

        # Set channel topic for WORKSHOP_CHANNEL_NAME in all guilds.
        print(f"Setting #{CHANNEL_NAME} topic...")
        await self.init_channel_topic()

        # Loop all messages in #workshop-maps and do work on all those.
        # https://docs.pycord.dev/en/stable/api/models.html#discord.TextChannel.history

        print("\n # Fixing missed messages... \n")
        for guild in self.guilds:
            print(guild)
            workshop_map_channel = discord.utils.get(guild.channels, name=CHANNEL_NAME)
            print(workshop_map_channel)

            async for message in workshop_map_channel.history(oldest_first=True):
                print(
                    f"{message.guild.name}#{message.channel.name}: {message.author.name}: {message.content}"
                )

                if message.author == self.user:
                    continue

                if not self.is_workshop_url(message):
                    await self.remove_workshop_channel_message(message)

                if self.is_workshop_url(message):
                    await self.handle_workshop_url(message)

        # Delete all threads without first message.
        print("\n # Delete threads without original message \n")
        for guild in self.guilds:
            print(f"Guild '{guild.name}'")
            channel = discord.utils.get(guild.channels, name=CHANNEL_NAME)
            print(f"Channel '{channel.name}'")
            for thread in channel.threads:
                print(f"Thread '{thread.name}'")

                try:
                    original_message = await channel.fetch_message(thread.id)
                    print(f"Original message : {original_message.content}")
                except discord.NotFound:
                    print("❗Original message not found!")
                    print("Deleting thread...")
                    await thread.delete()

        # Add missing threads for BotMessages that are embeds.
        print("\n # Adding missing threads \n")
        for guild in self.guilds:
            print(f"Guild '{guild}'")
            workshop_channel = discord.utils.get(guild.channels, name=CHANNEL_NAME)
            print(f"Channel '{channel}'")
            async for message in workshop_channel.history(oldest_first=True):
                print(f"Message '{message.content}'")
                if message.author != self.user:
                    continue

                if not message.embeds:
                    continue

                embed = message.embeds[0]
                print(embed)
                print(embed.title)

                # Try to get thread with embed name
                thread = channel.get_thread(message.id)
                if thread:
                    print(f"Message has thread: {thread}")
                else:
                    print("❗Message does not have a thread!")
                    print("Adding thread...")
                    thread = await message.create_thread(name=embed.title)

    async def on_message(self, message):
        print(f"#{message.channel} - {message.author}: {message.content}")

        # Do not handle messages from bot.
        if message.author == self.user:
            return

        # if message is in a thread...?
        # check if there is a thread and embed in workshop-maps channels.
        # Add embed to channel
        # Add links to than embed and thread, but do not delete, just reply to the comment with the info. And tag the user in that thread.
        # Remove embed from link, message.edit(embed=None, embeds=[])

        if type(message.channel) == discord.DMChannel:
            workshopid = get_workshop_id_from_url(message.content)
            embed = create_workshop_embed(workshopid)
            embed_msg = await message.reply(embed=embed)
            return

        # If message is in bot's channel delete if not workshop link.
        if message.channel.name == "workshop-maps" and not self.is_workshop_url(
            message
        ):
            await self.remove_workshop_channel_message(message)

        # If message is workshop url
        if self.is_workshop_url(message):
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
            author_is_in_thread = False

            print("members in thread:")
            print(existing_thread.members)

            print("fetching members")
            await existing_thread.fetch_members()
            print("members in thread:")
            print(existing_thread.members)

            print("author_in_thread FIND")
            author_in_thread = discord.utils.find(
                lambda m: m.id == message.author.id, existing_thread.members
            )
            print("author_in_thread")
            print(author_in_thread)

            # print("author_in_thread GET")
            # author_in_thread = discord.utils.get(
            #     existing_thread.members, id=message.author.id
            # )
            # print("author_in_thread")
            # print(author_in_thread)

            if not author_in_thread:
                reply_text += (
                    f"{message.author.mention} I'm tagging you in the thread. \n"
                )
                await existing_thread.send(f"{message.author.mention}")
            else:
                reply_text += f"{message.author.mention} You are already in the existing thread. \n"

            # suppress embeds to avoid discord link embed.
            replies.append(await message.reply(reply_text, suppress=True))

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
intents.members = True

client = MyClient(intents=intents)
client.run(os.getenv("discord_token"))
