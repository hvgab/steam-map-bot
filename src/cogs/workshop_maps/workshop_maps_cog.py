import os

import discord
from discord import commands

import cogs.workshop_maps.workshop_api as workshop_api
from tabulate import tabulate

import asyncio

WORKSHOP_CONTRIBUTER_ROLE = "🪖 Workshop Contributer!"


class WorkshopCog(discord.Cog, name="Workshop Cog"):
    def __init__(self, bot):
        self.bot = bot
        self.CHANNEL_NAME = "🤖-workshop-maps"
        self.WORKSHOP_URLS = [
            "https://steamcommunity.com/sharedfiles/filedetails/?id=",
            "https://steamcommunity.com/workshop/filedetails/?id=",
        ]

    # Listeners
    @discord.Cog.listener()
    async def on_ready(self):
        # Set channel topic for WORKSHOP_CHANNEL_NAME in all guilds.
        print(f"Setting #{self.CHANNEL_NAME} topic...")
        await self._set_channel_topic()

        # Loop all messages in #workshop-maps and do work on all those.
        # https://docs.pycord.dev/en/stable/api/models.html#discord.TextChannel.history

        await self._fix_missed_messages()

        await self._delete_threads_without_original_message()

        await self._add_missing_threads()

    @discord.Cog.listener()
    async def on_message(self, message):
        print(f"#{message.channel} - {message.author}: {message.content}")

        # Do not handle messages from bot.
        if message.author == self.bot.user:
            return

        # if message is in a thread...?
        # check if there is a thread and embed in workshop-maps channels.
        # Add embed to channel
        # Add links to than embed and thread, but do not delete, just reply to the comment with the info. And tag the user in that thread.
        # Remove embed from link, message.edit(embed=None, embeds=[])

        if type(message.channel) == discord.DMChannel:
            workshopid = self._get_workshop_id_from_url(message.content)
            embed = self._create_workshop_embed(workshopid)
            embed_msg = await message.reply(embed=embed)
            return

        # If message is in bot's channel delete if not workshop link.
        if message.channel.name == self.CHANNEL_NAME and not self._is_workshop_url(
            message
        ):
            await self._remove_workshop_channel_message(message)

        # If message is workshop url
        if self._is_workshop_url(message):
            print(f"Message from {message.author}: {message.content} is a workshop url")
            await self._handle_workshop_url(message)

        # TODO: If someone makes a comment on a map, add all users to thread? Add a comment i channel to hightlight message in thread?

    # Commands
    @commands.slash_command()
    async def show_voting_table(self, ctx):
        table = []

        workshop_channel = discord.utils.get(ctx.guild.channels, name=self.CHANNEL_NAME)
        async for message in workshop_channel.history(oldest_first=True):
            if len(message.embeds) == 0:
                continue

            row = {}
            row["Map"] = message.embeds[0].title

            # Reactions
            row["ThumbsUp"] = 0
            row["ThumbsDown"] = 0
            print(f"Embed {message.embeds[0].title} reactions:")
            print(message.reactions)
            for reaction in message.reactions:
                # Thumbsup
                if reaction.emoji == "👍":
                    row["ThumbsUp"] = reaction.count - 1
                # Thumbsdown
                if reaction.emoji == "👎":
                    row["ThumbsDown"] = reaction.count - 1

            # Rating
            row["Rating"] = 0
            if row["ThumbsDown"] > 0:
                row["Rating"] = float(row["ThumbsUp"]) / float(row["ThumbsDown"])
            if row["ThumbsUp"] > 0 and row["ThumbsDown"] == 0:
                row["Rating"] = 1
            # row["Rating"] = f'{row["Rating"]*100}%'

            row["Workshop Id"] = ""
            for field in message.embeds[0].fields:
                if field.name == "Workshop Id":
                    row["Workshop Id"] = field.value

            # row["Workshop Link"] = ""
            # for field in message.embeds[0].fields:
            #     if field.name == "Workshop Link" or field.name == "Link":
            #         row["Workshop Link"] = field.value

            table.append(row)

        # Sort
        table = sorted(table, key=lambda r: r["Rating"], reverse=True)

        # headers = {
        #     "Map": "Map",
        #     "ThumbsUp": ":thumbsup:",
        #     "ThumbsDown": ":thumbsdown:",
        #     "Rating": "Rating",
        #     "Workshop Id": "Workshop Id",
        # }

        tabu = tabulate(table, headers="keys")
        tabu2 = tabulate(table, headers="keys", tablefmt="simple_outline")

        print("\ntabu\n")
        print(tabu)
        print("\ntabu2\n")
        print(tabu2)

        # await asyncio.gather(
        # ctx.send(f"tabu\n```{tabu}```"),
        # ctx.send(f"tabu2\n```{tabu2}```"),
        # )

    # Other functions
    async def _fix_missed_messages(self):
        print("\n # Fixing missed messages... \n")
        for guild in self.bot.guilds:
            print(guild)
            workshop_map_channel = discord.utils.get(
                guild.channels, name=self.CHANNEL_NAME
            )

            if not workshop_map_channel:
                print("Could not get workshop channel")
                print("workshop_map_channel")
                print(workshop_map_channel)

            async for message in workshop_map_channel.history(oldest_first=True):
                # Skip messages by the bot.
                if message.author == self.bot.user:
                    continue

                # Remove text messages
                if not self._is_workshop_url(message):
                    await self._remove_workshop_channel_message(message)

                # Handle workshop urls
                if self._is_workshop_url(message):
                    await self._handle_workshop_url(message)

    async def _delete_threads_without_original_message(self):
        # Delete all threads without first message.
        print("\n # Delete threads without original message \n")
        for guild in self.bot.guilds:
            print(f"Guild '{guild.name}'")
            channel = discord.utils.get(guild.channels, name=self.CHANNEL_NAME)
            for thread in channel.threads:
                try:
                    original_message = await channel.fetch_message(thread.id)
                except discord.NotFound:
                    await thread.delete()

    async def _add_missing_threads(self):
        # Add missing threads for BotMessages that are embeds.
        print("\n # Adding missing threads \n")
        for guild in self.bot.guilds:
            print(f"Guild '{guild}'")
            workshop_channel = discord.utils.get(guild.channels, name=self.CHANNEL_NAME)
            async for message in workshop_channel.history(oldest_first=True):
                if message.author != self.bot.user:
                    continue

                if not message.embeds:
                    continue

                embed = message.embeds[0]

                thread = workshop_channel.get_thread(message.id)

                print("Thread:")
                print(thread)

                if not thread:
                    try:
                        thread = await message.create_thread(name=embed.title)
                    except discord.errors.HTTPException as e:
                        if (
                            e.text
                            == "A thread has already been created for this message"
                        ):
                            print(e.text)
                            pass
                        else:
                            print("thread error")
                            print(e)
                            print("e.text")
                            print(e.text)
                            raise

    def _create_workshop_embed(self, workshopid):
        url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={workshopid}"
        workshop_data = workshop_api.get_published_file_details(workshopid)
        preview_url = workshop_data["preview_url"]
        title = workshop_data["title"]
        description = workshop_data["description"]
        description += "\n"

        embed = discord.Embed(
            title=title, url=url, description=description, timestamp=None
        )
        embed.set_image(url=preview_url)
        embed.add_field(name="Workshop Link", value=url, inline=False)
        embed.add_field(name="Workshop Id", value=workshopid, inline=False)
        embed.set_footer(text=f"Workshop Id: {workshopid}")

        return embed

    def _get_workshop_id_from_url(self, url):
        for workshop_base_url in self.WORKSHOP_URLS:
            if url.startswith(workshop_base_url):
                workshopid = url.partition(workshop_base_url)[2]
        print(workshopid)
        workshopid = workshopid.partition("&")[0]
        workshopid.strip()
        print(workshopid)
        return workshopid

    def _is_workshop_url(self, message):
        print(message.content)

        for workshop_url in self.WORKSHOP_URLS:
            print(workshop_url)
            if message.content.strip().lower().startswith(workshop_url):
                return True
        return False

    async def _set_channel_topic(self):
        # Get workshop-map channel in all guild
        description = ""
        description += "This channel is just for workshop links. The bot will clean up the channel for all other messages. "
        description += "Each map has it's own thread for discussions. "
        description += "Use the thumbs up to vote for maps. Use the family emojis to say if the map is best for less than or more than 5 players. "
        description += "Workshop Link https://steamcommunity.com/app/730/workshop/ "
        description = description.strip()

        for guild in self.bot.guilds:
            print(f"Checking '{guild.name}' for channel topic")
            workshop_channel = discord.utils.get(guild.channels, name=self.CHANNEL_NAME)
            print("workshop_channel")
            print(workshop_channel)

            if not workshop_channel:
                print("Could not find workshop channel.")
                # TODO: Create channel?
                return

            print("workshop_channel.topic")
            print(workshop_channel.topic)

            if workshop_channel.topic is None or workshop_channel.topic != description:
                # Add/Edit description of channel
                print(f"Editing '{guild.name}' '#{workshop_channel.name}' topic")
                print()
                print(workshop_channel.topic)
                print()
                print(description)
                await workshop_channel.edit(topic=description)

    async def _handle_workshop_url(self, message):
        message.channel.typing()

        workshopid = self._get_workshop_id_from_url(message.content)
        workshop_data = workshop_api.get_published_file_details(workshopid)

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
            embed = self._create_workshop_embed(workshopid)
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

    async def _remove_workshop_channel_message(self, message):
        reply = await message.reply(
            f"{message.author.mention} Only workshop links in this channel. Deleting message in 10 sec.\nFor map discussions please use the map threads."
        )
        await message.delete(delay=10)
        await reply.delete(delay=10)


def setup(bot):
    bot.add_cog(WorkshopCog(bot))


def teardown(bot):
    bot.remove_cog("WorkshopCog")
