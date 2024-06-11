#!/usr/bin/env python3
"""
I would like to turn this completly into a Group (and maybe GroupManager) class.
Most of the methods can probably turned into methods very simpple and makes it a lot
easier to use and maintain. Views and Modals could also be generated from a group class
instead of having their own classes. Read more: #75
"""
import signal
import sys
import os
import logging
import yaml
import discord
from filelock import FileLock
from typing import Union, List
from discord import abc  # discords base classes
from discord import (CategoryChannel, Interaction, Guild, Role, PermissionOverwrite,
    Interaction, ButtonStyle, User, Member, Client)
from discord.ui import TextInput, button
from discord.ext.commands import Context

from utility.sanitizer import sanitize
from config import DATA
from config import messages as msg
from views.base import BaseModal, BaseView
from cogs.group import organize_group as og
from utility.sanitizer import sanitize
from config import messages as msg

# module level functions and variables (cache).

# root level of the file are server, we could also save server specific data in the same
# file, so I renamed it to guilds.yml.
data_file = DATA/"guilds.yml"

def save_yaml(original_function):
    def wrapper(guild, *args, **kwargs):
        result = original_function(guild, *args, **kwargs)
        with open(data_file, "w+") as file:
            logging.debug(f"Saving triggered by {guild}...")
            with FileLock("groups.yml.lock"):
                yaml.safe_dump(guilds, file)
        return result
    return wrapper


@save_yaml
def sigterm_handler(_signo, _stack_frame):
    sys.exit(0)

signal.signal(signal.SIGINT, sigterm_handler)
signal.signal(signal.SIGTERM, sigterm_handler)

# LOAD GROUPS
guilds = {}
if os.path.isfile(data_file):
    with open(data_file, "r") as yaml_file:
        guilds = yaml.safe_load(yaml_file) or {}
else:
    logging.warning("No guilds file found. Trying to create one next save.")



def get_id(object):
    """utility function to get id from discord object or string"""
    if object is None:
        return object
    if isinstance(object, str) or isinstance(object, int):
        return int(object)
    return object.id


class Group():
    """ This class makes all group data and ui elements easy accessible and provides
    convenient methods to interact with the group. It's primarily used from within group
    commands and views.
    Most parameters of this class directly map to their dictionary representation.
    However, the init function is quite flexible in terms of input types, to make it
    easy to use in different scenarios. Methods use ids of discord objects when possible
    to avoid unnecessary calls to discord API. The methods that require such calls
    are usually async (i.e. setup_roles, create_channels).
    """
    
    def __init__(self, name: str=None, slug: str=None, ctx: Context=None, 
        inter: Interaction=None, guild: Union[Guild, int]=None,
        owner: Union[abc.User, int]=None, category: Union[CategoryChannel, int]=None,
        date: str="", max_players: int=4, description: str="", players: List[int]=[],
        bot: discord.Client=None,
        channels: List[int]=[]  # maybe remove?
        ) -> None:
        """Creates a new group object.
        The init function is a bit massive, but this allows to use it very flexible,
        with different types of input. When using in context of
        interactions/commands/yamlfile. 
        @param name: Human readable name of the group (used as title)
        @param slug: sanitized name of the group (used as key/id) unique per guild.
        @param ctx: discord context object, to derive guild and owner
        @param inter: interaction object, sets guild/owner if ctx is not given
        @param owner: user object or id of the owner overwrites owner from ctx/inter
        @param guild: guild object or id, overwrites owner from ctx/inter
        """
        self.name = name
        self.slug = sanitize(name) if name else None
        self.ctx = None
        self.inter = None
        if ctx:
            self.ctx = ctx
            self.guild = ctx.guild.id
            self.owner = ctx.author.id
            self.bot = ctx.bot
        elif inter: 
            self.inter = inter
            self.guild = inter.guild.id
            self.owner = inter.user.id
        if owner:
            self.owner = get_id(owner)
        if guild:
            self.guild = get_id(guild)
        if bot:
            self.bot = bot
        self.category = get_id(category)
        self.date = date
        self.max_players = max_players
        self.description = description
        self.players = [get_id(p) for p in players]
        self.channels = []  # TODO remove?
        self.role = None

    @classmethod
    def load(cls, guild_id, group_name, create=False):
        """Loads a group object from the guilds dict.
        TODO: maybe allow passing context, to get guild_id?
        @param create: if True, a new (unsaved) group object is created for missing data
        """
        group_slug = sanitize(group_name)
        data = guilds.get(guild_id, {}).get(group_slug)
        if not data and not create:
            raise ValueError(f"Group {group_name} not found in guild {guild_id}.")
        return cls.from_dict(guilds.get(guild_id, {}).get(group_slug))

    @classmethod
    def groups_from_guild(cls, guild_id: int):
        """Returns all groups from a guild."""
        groups_data = guilds.get(guild_id, {})
        groups = [Group.from_dict(data) for data in groups_data.values()]
        return groups

    @classmethod
    def from_dict(cls, data):
        """Generates all objects from the id's in a dict and returns a group object."""
        return cls(**data)
    
    async def setup_role(self):
        guild = self.bot.get_guild(self.guild)
        if not self.role:
            role = await guild.create_role(name=self.name)
            self.role = role.id
        else:
            role = self.ctx.guild.get_role(self.role)
        if self.ctx:
            await self.ctx.author.add_roles(role)
        elif self.inter:
            await self.inter.user.add_roles(role)
        for p in self.players:
            await guild.get_member(p).add_roles(role)
    
    async def create_channels(self, welcome=True):
        """Creates channels for the group.
        TODO: do we need to track the channels? Is tracking category not enough?
        """
        guild = self.bot.get_guild(self.guild)  # get guild object from id
        if not guild or not self.role:
            raise ValueError("Guild and role are required to setup channels.")
        permissions = {
            guild.default_role: PermissionOverwrite(read_messages=False),
            guild.get_role(self.role): PermissionOverwrite(read_messages=True)}
        category = await guild.create_category(name=self.slug)  # TODO: name or slug?
        text = await guild.create_text_channel(name="Text", 
            overwrites=permissions, category=category)
        self.default_channel = text.id  # maybe set one channel as the one the bot uses?
        await guild.create_voice_channel(
            name="Voice", overwrites=permissions, category=category)
        if welcome:
            await text.send(msg["gcreate_channel_created"].format(
                author=self.user.id))

    async def setup_guild(self):
        """Creates and assignes roles/channels permissions for this group."""
        await self.setup_role()
        await self.create_channels()

    def __str__(self):
        """String representation of a group. str(group), print(group)..."""
        return f"{self.name} ({self.owner})"
    
    @property
    def info_message(self):
        """message content for !ginfo and the like"""
        return msg["group_info"].format(group=self)
    
    def info_view(self, user: abc.User=None):
        """Returns buttons for group details for this group.
        @param user: user object, required if no ctx or inter is set.
        """
        user = user if user else self.user
        if not user:
            raise ValueError("User is required to create a group view.")
        return GroupView(user)
    
    def as_dict(self):
        """convert object into dict (trivial rn, but could be extended later)"""
        return {
            "name": self.name,
            "slug": self.slug,
            "owner": self.owner,
            "category": self.category,
            "date": self.date, 
            "max_players": self.max_players,
            "description": self.description,
            "players": self.players,
            "channels": []  # TODO remove?
        }
    
    @save_yaml
    def save(self):
        """Saves the group object to the guilds dict."""
        if not self.slug or not self.guild:
            raise ValueError("Group needs a guild and a slug to be saved.")
        guilds.setdefault(self.guild, {})
        guilds[get_id(self.guild)][self.slug] = self.as_dict()
    
    @save_yaml
    def remove_player(self, player: Union[abc.User, int]):
        """Removes a player from the group."""
        player_id = get_id(player)
        if player_id in self.players:
            self.players.remove(player_id)
            # return True, f"Spieler <@{player_id}> wurde entfernt."
        # return False, f"Spieler <@{player_id}> ist nicht in Gruppe {self.name}."
    
    @save_yaml
    def group_destroy(self, user: Union[abc.User, int]):
        """Destroys the group
        @return: tuple(bool, str) status, message
        """
        if not self.is_owner(user):
            return False, msg["not_owner"]
        guild = get_id(self.guild)
        group_data = guilds.get(guild, {}).pop(self.slug)
        return True, msg["group_destroyed"]

    def is_owner(self, user: Union[abc.User, int]):
        return get_id(self.owner) == get_id(user)

    @property
    def player_count(self):
        return len(self.players)
    
    @property
    def user(self):
        """this does return command author or button clicker, not the owner"""
        if self.ctx:
            return self.ctx.author
        elif self.inter:
            return self.inter.user
        return None
    
    @property
    def exists(self):
        return self.slug in guilds.get(self.guild, {})


class GroupModal(BaseModal, title="Neue Gruppe"):
    """ Modal for creating or editing a group
    This popup can only be created from an interaction (i.e. button click or /command),
    but not from simple !commands. The fields can be set as class variables and the user
    input will be accessible from the instance as self.<field_name>.value.
    TODO: allow to pass a group and prefill the fields for edit.
    TODO: distinguish between create and edit mode, maybe track old group name (key)
    """
    name = TextInput(label=msg["name_la"], placeholder=msg["name_ph"], min_length=1, max_length=80)
    text = TextInput(label=msg["text_la"], placeholder=msg["text_ph"], required=False, max_length=1400, min_length=0, style=discord.TextStyle.long)
    slots = TextInput(label=msg["slots_la"], placeholder=msg["slots_ph"], required=False, min_length=0, max_length=1, default=4)
    date = TextInput(label=msg["date_la"], placeholder=msg["date_ph"], required=False, min_length=0, max_length=150)

    def __init__(self, name=None):
        self.group = name
        super().__init__(timeout=460.0)

    async def on_submit(self, inter: Interaction) -> None:
        # await super().on_submit(interaction)
        group = Group(  # create object from form input
            name=self.name.value,
            description=self.text.value,
            max_players=int(self.slots.value),
            date=self.date.value,
            inter=inter,
            bot=self.bot
        )
        group.save()  # write to yaml
        await group.setup_guild()  # channels and roles etc..
        await inter.response.send_message(msg["submit_success"], ephemeral=True)


class GroupView(BaseView):
    """ Group detail View
    This is a placeholder for now. A view is can be attached to a message and contains
    interactive elements like buttons or select menus. Creating a class like this might 
    help to quickly create messages with group details and options to interact with them.
    TODO: Only [Join]/[Leave], [Edit]/[Delete]/[Anounce] should be owner command (gedit)
    TODO: Possible to hide buttons from non-owners or non-members?
    TODO: Generate this view from a group dictionary or name
    """
    interaction = None
    message = None
    group = None  # for now sanitized name, turns into group object later
    
    @button(label=msg["btn_join"], emoji="🍻", style=ButtonStyle.green)
    async def join(self, inter: Interaction, button) -> None:
        if self.group is None:
            status, answer = False, msg["no_group_set"]
        else:
            status, answer = og.add_self(
                sanitize(inter.guild.name),
                sanitize(self.group),
                inter.user.id)
        # ephemeral: only the interacting user sees the response.
        await inter.response.send_message(answer, ephemeral=True)
    

    # adding a component using it's decorator (fancy shit)
    @button(label=msg["btn_edit"], emoji="✏️", style=ButtonStyle.blurple)
    async def edit(self, inter, button) -> None:
        """ open modal to edit group on button click
        TODO: not fully implemented yet, modal is just an example (not saving)
        """
        # group_form = GroupModal()
        # await inter.response.send_modal(group_form)
        print(inter.name)
        # await inter.response.edit_message("Noch nicht implementiert", view=self)

    @button(label=msg["btn_destroy"], emoji="🗑️", style=ButtonStyle.red)
    async def destroy(self, inter, button) -> None:
        """ destroy a group from button click
        TODO: check permissions, maybe confirm dialog?
        """
        guild = sanitize(inter.guild.name)
        if not og.is_owner(guild, self.group, inter.user.id):
            await inter.response.send_message(msg["not_owner"], ephemeral=True)
            return
        status, answer = og.destroy_group(guild, self.group, inter.user.id)[:2]
        await inter.response.send_message(answer, ephemeral=True)


class NewGroupView(BaseView):
    """ View for !gcreate command
    NOTE: not yet implemented.. try with !view. Maybe we can reuse the group_modal
    """

    @discord.ui.button(label="Gruppe erstellen", style=discord.ButtonStyle.green)
    async def new(self, inter, button) -> None:
        group_form = GroupModal()
        group_form.bot = self.bot
        await inter.response.send_modal(group_form)



# TODO: move to config.constants or config.messages
PLAYER_NUMBER = "player_number"
PLAYER_NUMBER_PRINT = "Spielerzahl"
DATE = "date"
DATE_PRINT = "Datum"
DESCRIPTION = "description"
DESCRIPTION_PRINT = "Beschreibung"
PLAYER = "player"
PLAYER_PRINT = "Beschreibung"
CHANNELS = "channels"
CATEGORY = "category"
OWNER = "owner"



def is_owner(guild, group, author_id):
    logging.warning("DEPRECATED! use Group().is_owner() instead.")
    group_data = guilds.get(guild, {}).get(group)
    return group_data[OWNER] == author_id


def group_exists(guild, group):
    logging.warning("DEPRECATED! use Group().exists instead.")
    return guilds.get(guild) and guilds[guild].get(group)


@save_yaml
def destroy_group(guild, group, author=None):
    logging.warning("DEPRECATED! use Group.destroy() instead.")
    group_data = guilds.get(guild, {}).get(group)
    if group_data is None:
        return False, "Die Gruppe existiert nicht.", [], [], []
    if author and group_data[OWNER] != author:
        return False, "Du bist nicht der Besitzer der Gruppe.", [], [], []
    group_dict = guilds[guild].pop(group)
    return 1, "Die Gruppe wurde gelöscht.", group_dict[PLAYER], group_dict[CHANNELS], group_dict[CATEGORY]


def get_main_channel(guild, group):
    logging.warning("DEPRECATED! use Group.default_channel instead.")
    if not guilds.get(guild):
        guilds[guild] = {}
    guild_groups = guilds[guild]
    if guild_groups.get(group):
        return guild_groups[group].get(CHANNELS, [None])[0]
    return None



@save_yaml
def remove_player(guild, group, player):
    if not guilds.get(guild):
        guilds[guild] = {}
    guild_guilds = guilds[guild]
    if guild_guilds.get(group):
        if player in guild_guilds[group][PLAYER]:
            guild_guilds[group][PLAYER].remove(player)
            return True, f"Spieler <@{player}> wurde entfernt."
        else:
            return False, f"Spieler <@{player}> ist nicht in Gruppe {group}."
    else:
        return False, f"Gruppe {group} existiert nicht."


@save_yaml
def add_self(guild, group, player):
    """adds a player to a group
    TODO: should be named add_player?
    @param guild: guild id as string
    @param group: (sanitized) group name
    @param player: player id as string
    """
    if not guilds.get(guild):
        guilds[guild] = {}
    guild_groups = guilds[guild]
    if guild_groups.get(group):
        if player not in guild_groups[group][PLAYER]:
            current_player_number = len(guild_groups[group][PLAYER])
            maximum_player_number = int(guild_groups[group][PLAYER_NUMBER])
            if current_player_number < maximum_player_number:
                guild_groups[group][PLAYER].append(player)
                return_str = f"Du wurdest Gruppe {group} hinzugefügt.\n"
                return_str += f"Zum Verlassen `!gleave {group}`"
                return True, return_str
            else:
                return False, f"Gruppe {group} ist bereits voll: {current_player_number}/{maximum_player_number}"
        else:
            return False, f"Du bist bereits Teil der Gruppe {group}."
    else:
        return False, f"Gruppe {group} existiert nicht."


@save_yaml
def remove_self(guild, group, player):
    """removes a player from a group
    TODO: should be named remove_player?
    @param guild: guild id as string
    @param group: (sanitized) group name
    @param player: player id as string
    """
    if not guilds.get(guild):
        guilds[guild] = {}
    guild_groups = guilds[guild]
    if guild_groups.get(group):
        if player in guild_groups[group][PLAYER]:
            guild_groups[group][PLAYER].remove(player)
            return True, f"Du wurdest aus Gruppe {group} entfernt."
        else:
            return False, f"Du bist kein Spieler der Gruppe {group}."
    else:
        return False, f"Gruppe {group} existiert nicht."


@save_yaml
def remove_channel(guild, group, channel):
    if not guilds.get(guild):
        guilds[guild] = {}
    guild_guilds = guilds[guild]
    if guild_guilds.get(group):
        guild_guilds[group][CHANNELS].remove(channel)


def channel_exists(guild, group, channel):
    if not guilds.get(guild):
        guilds[guild] = {}
    guild_groups = guilds[guild]
    return guild_groups.get(group) and channel in guild_groups[group][CHANNELS]


def is_owner(guild, group, author_id):
    if not guilds.get(guild):
        guilds[guild] = {}
    guild_groups = guilds[guild]
    print(guild_groups[group][OWNER], author_id)
    return guild_groups.get(group) and guild_groups[group][OWNER] == author_id
