import requests
from bs4 import BeautifulSoup
import discord
import json
import re
from discord.ext import task
from datetime import datetime as dt
from tabulate import tabulate 

maps = [
    {
        "id": 1,
        "name": "Dust2",
        "category": 1
    },
    {
        "id": 2,
        "name": "Inferno",
        "category": 1
    },
    {
        "id": 3,
        "name": "Nuke",
        "category": 1
    },
    {
        "id": 4,
        "name": "Overpass",
        "category": 1
    },
    {
        "id": 5,
        "name": "Mirage",
        "category": 1
    },
    {
        "id": 6,
        "name": "Cache",
        "category": 2
    },
    {
        "id": 7,
        "name": "Cobblestone",
        "category": 2
    },
    {
        "id": 8,
        "name": "Train",
        "category": 1
    },
    {
        "id": 9,
        "name": "Tuscan",
        "category": 2
    },
    {
        "id": 10,
        "name": "Season",
        "category": 2
    },
    {
        "id": 11,
        "name": "Santorini",
        "category": 2
    },
    {
        "id": 12,
        "name": "Aztec",
        "category": 3
    },
    {
        "id": 13,
        "name": "Dust",
        "category": 3
    },
    {
        "id": 14,
        "name": "Fire",
        "category": 3
    },
    {
        "id": 15,
        "name": "Mill",
        "category": 3
    },
    {
        "id": 16,
        "name": "Prodigy",
        "category": 3
    },
    {
        "id": 17,
        "name": "Piranesi",
        "category": 3
    },
    {
        "id": 18,
        "name": "Vertigo",
        "category": 1
    },
    {
        "id": 19,
        "name": "Dust2 (old)",
        "category": 4
    },
    {
        "id": 20,
        "name": "Inferno (old)",
        "category": 4
    },
    {
        "id": 21,
        "name": "Nuke (old)",
        "category": 4
    },
    {
        "id": 22,
        "name": "Cobblestone (old)",
        "category": 4
    },
    {
        "id": 23,
        "name": "Train (old)",
        "category": 4
    },
    {
        "id": 24,
        "name": "Office",
        "category": 5
    },
    {
        "id": 25,
        "name": "Assault (1.6)",
        "category": 5
    },
    {
        "id": 26,
        "name": "Italy",
        "category": 5
    },
    {
        "id": 27,
        "name": "Insertion",
        "category": 5
    },
    {
        "id": 28,
        "name": "Agency",
        "category": 5
    },
    {
        "id": 29,
        "name": "Militia",
        "category": 5
    },
    {
        "id": 30,
        "name": "Estate (1.6)",
        "category": 5
    },
    {
        "id": 31,
        "name": "Subzero",
        "category": 2
    },
    {
        "id": 32,
        "name": "Cache (workshop)",
        "category": 2
    },
    {
        "id": 33,
        "name": "Aim map",
        "category": 6
    },
    {
        "id": 34,
        "name": "Ancient",
        "category": 1
    },
    {
        "id": 35,
        "name": "Dr Pepper Wingman",
        "category": 7
    },
    {
        "id": 36,
        "name": "Aim Esportal",
        "category": 6
    },
    {
        "id": 37,
        "name": "Aim Monster",
        "category": 6
    },
    {
        "id": 38,
        "name": "OMEN Astralis Wingman",
        "category": 7
    }
]


class EsportalCog(discord.Cog, name="Esportal Cog"):
    def __init__(self, bot):
        self.message = None
        self.interval = None
        self.bot_message = None
        self.regex = re.compile(r"https:\/\/esportal.com\/.*\/gather\/(\d+)")
        self.gather_id = None
        self.gather = None
        self.match = None
        self.state = None
        self.team1_score = None
        self.team2_score = None
        self.embed = None
        self.waitTime = 15  # in seconds

    @discord.Cog.listener()
    async def on_message(self, message):
        # Skip messages from bot.
        if message.author == self.bot.user:
            return
        
        # If not gather, skip
        gather_id_match = self.regex.search(self.message.content)
        if not gather_id_match:
            return
        
        self.gather_id = gather_id_match.group(1)
        print("gather_id_match: " + str(gather_id_match))
        print("self.gather_id: " + str(self.gather_id))
        
        
        self.main.start()

    def cog_unload(self):
        self.main.cancel()
        
    @task.loop(seconds=15)
    async def main(self):
        # Get gather
        print(f"GetGather id {self.gather_id}")
        self.gather = await self.get_gather(self.gather_id)
        if self.gather is None:
            print("No gather, not doing anything more.")
            self.main.stop()
            return
        # Get match
        if hasattr(self.gather, "match_id") and self.gather.match_id is not None:
            print(f"Match id {self.gather.match_id}")
            self.match = await self.get_match(self.gather.match_id)
        # Make reply/embed
        self.embed = self.make_embed(self.gather, self.match)
        # If we are editing
        if self.msg is not None:
            await self.msg.edit(embed=self.embed)
        else:
            self.msg = await self.message.channel.send(embed=self.embed)
        # Stop
        if self.state == "FINISHED":
            self.stopInterval()

    async def get_gather(self, gather_id):
        """Get Gather info from Esportal.com/gather/[id]"""
        print("Get Gather")
        url = f"https://api.esportal.com/gather/get?id={gather_id}"
        try:
            response = requests.get(url)
            data = await response.data
            return data
        except Exception as error:
            if hasattr(error, "response"):
                print(error.response.data)
                print(error.response.status)
            elif hasattr(error, "request"):
                print(error.request)
            else:
                print("Error", error.message)
            raise Exception("No gather")

    async def get_match(self):
        """Get esportal.com match data"""
        print("Get Match")
        url = f"https://api.esportal.com/match/get?_={Date.now()}&id={self.gather.match_id}"
        print(url)
        try:
            response = await axios.get(url)
            data = await response.data
            return data
        except Exception as error:
            print("Error", error)

    def make_embed(self):
        if self.gather is None:
            print("no gather data.")
            return
        print("Make Embed:")
        # Get Gather State
        self.state = "UNKNOWN"
        if self.gather.active is False and self.gather.match_id is None:
            self.state = "WAITING"
        elif self.gather.active is True and self.gather.match_id is not None:
            self.state = "IN-GAME"
        elif self.gather.active is False and self.gather.match_id is not None:
            self.state = "FINISHED"
        print("State: " + self.state)
        # Title + URL
        title = self.gather.name
        url = f"https://esportal.com/gather/{self.gather_id}"
        # Author
        author_name = self.bot.author_name
        author_icon = self.bot.author_icon
        author_url = self.bot.author_url
        # players
        players = []
        players_picked = []
        players_team1 = []
        players_team2 = []
        team1_leader = "1"
        team2_leader = "2"
        team1_score = None
        team2_score = None
        if self.state == "WAITING":
            for player in self.gather.players:
                players.append(player)
                if player.picked is True:
                    players_picked.append(player)
        elif self.state == "IN-GAME" or self.state == "FINISHED":
            for player in self.match.players:
                if player.team == 1:
                    players_team1.append(player)
                elif player.team == 2:
                    players_team2.append(player)
        # Score
        if self.state == "IN-GAME" or self.state == "FINISHED":
            print("adding team scores")
            team1_score = self.match.team1_score
        elif self.gather.team1_score is not None:
            team1_score = self.gather.team1_score
        if self.state == "IN-GAME" or self.state == "FINISHED":
            team2_score = self.match.team2_score
        elif self.gather.team2_score is not None:
            team2_score = self.this.gather.team2_score
        # Map
        map_name = None
        if self.state == "IN-GAME" or self.state == "FINISHED":
            map_name = self.find_map(self.match.map_id)
            print(f"match map id: {self.match.map_id}")
            print(f"map: {map_name}")
        
        # Summary
        summary = ""
        if self.state == "WAITING":
            summary = f":green_circle: **Waiting for players** :green_circle:\n\nCome join us! {len(players_picked)}/10\n"
        elif self.state == "IN-GAME":
            summary = f":yellow_circle: **Match in progress on {map_name}** :yellow_circle:\n\nTeam {team1_leader} ( **{team1_score}** - **{team2_score}** ) Team {team2_leader}\n"
        elif self.state == "FINISHED":
            summary = f":red_circle: **Match finished on {map_name}** :red_circle:\n\nTeam {team1_leader} ( **{team1_score}** - **{team2_score}** ) Team {team2_leader}\n"
        else:
            summary = ":white_circle: **UNKNOWN** :white_circle:"
        # Body Text
        print(self.gather.players_picked)
        body_text = ""
        player_list = []
        if self.state == "WAITING":
            for index, player in enumerate(players_picked):
                if index < 5:
                    player_list.append([player.username])
                elif index >= 5:
                    player_list[index - 5].append(player.username)
            for row in player_list:
                if len(row) < 2:
                    row.append("")
            player_list.insert(0, ["", ""])
            print("player_list")
            print(player_list)
            table = tabulate(player_list, headers=())
            body_text = "```" + table + "```"
        elif self.state == "IN-GAME" or self.state == "FINISHED":
            players_team1 = []
            players_team2 = []
            for player in self.match.players:
                if player.team == 1:
                    players_team1.append(player)
                elif player.team == 2:
                    players_team2.append(player)
            for index in range(5):
                print("pt1: " + players_team1[index])
                print("pt2: " + players_team1[index])
                player_list.append([players_team1[index].username, players_team2[index].username])
            player_list.insert(0, ["Team 1", "Team 2"])
            print("Player list to make_table:")
            print(player_list)
            table = tabulate(player_list)
            body_text = "" + table + ""
        else:
            body_text = "```\n"
        description = summary + "\n" + body_text
        embed = discord.MessageEmbed(
            color=self.bot.config.colors.esportal,
            title=title,
            url=url,
            author=discord.Author(name=author_name, icon_url=author_icon, url=author_url),
            description=description,
            footer="Last update",
            timestamp=discord.Timestamp.now()
        )
        print("Embed:", embed)
        return embed

    def find_map(self, id):
        map_name = None
        print("find map")
        for map in maps:
            print("map: ")
            print(map)
            print(f"map.id {map.id} : id {id}")
            print(map.id == id)
            if map.id == id:
                map_name = map.name
        return map_name

    