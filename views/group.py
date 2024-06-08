import discord
from discord import Interaction
from discord.ui import TextInput, Select
from views.base import BaseModal, BaseView
from cogs.group import organize_group as og
from utility.sanitizer import sanitize


class GroupModal(BaseModal, title="Neue Gruppe"):
    """ Modal for creating or editing a group
    This popup can only be created from an interaction (i.e. button click or /command),
    but not from simple !commands. The fields can be set as class variables and the user
    input will be accessible from the instance as self.<field_name>.value.
    TODO: allow to pass a group and prefill the fields for edit.
    TODO: distinguish between create and edit mode, maybe track old group name (key)
    """
    name = TextInput(label="Name", placeholder="Name der Gruppe", min_length=1, max_length=80)
    text = TextInput(label="Beschreibung", placeholder="Beschreibung der Gruppe", max_length=1400, min_length=1, style=discord.TextStyle.long)
    places = TextInput(label="Plätze", placeholder="Spielerzahl", min_length=1, max_length=1, default=4)
    time = TextInput(label="Uhrzeit", placeholder="HH:MM", min_length=5, max_length=5)

    def __init__(self, name=None):
        self.group = name
        super().__init__(timeout=460.0)

    async def on_submit(self, inter: Interaction) -> None:
        # await super().on_submit(interaction)
        # Create group from input data
        guild = sanitize(inter.guild.name)
        group = sanitize(self.name.value)  # TODO: add original name as title
        category = await inter.guild.create_category(name=group)
        og.create_group(
            guild, 
            group, 
            inter.user.id,
            category.id,
            self.time.value,
            description=self.text.value, 
            player_number=int(self.places.value))
        await inter.response.send_message(
            ":white_check_mark: Gruppe erstellt!", ephemeral=True)


class GroupView(BaseView):
    """ Group detail View
    This is a placeholder for now. A view is can be attached to a message and contains
    interactive elements like buttons or select menus. Creating a class like this might 
    help to quickly create messages with group details and options to interact with them.
    TODO: Buttons like [Join], [Leave], [Edit], [Delete], [Anounce]
    TODO: Possible to hide buttons from non-owners or non-members?
    TODO: Generate this view from a group dictionary or name
    """
    interaction = None
    message = None
    group = None  # for now sanitized name, turns into group object later

    # adding a component using it's decorator (fancy shit)
    @discord.ui.button(label="Bearbeiten", style=discord.ButtonStyle.blurple)
    async def edit(self, inter, button) -> None:
        """ open modal to edit group on button click
        TODO: not fully implemented yet, modal is just an example (not saving)
        """
        # group_form = GroupModal()
        # await inter.response.send_modal(group_form)
        print(inter.name)
        # await inter.response.edit_message("Noch nicht implementiert", view=self)
    
    @discord.ui.button(label="Beitreten", style=discord.ButtonStyle.green)
    async def join(self, inter: Interaction, button) -> None:
        if self.group is None:
            status, answer = False, "Gruppe nicht gesetzt."
        else:
            status, answer = og.add_self(
                sanitize(inter.guild.name),
                sanitize(self.group),
                inter.user.id)
        # ephemeral: only the interacting user sees the response.
        await inter.response.send_message(answer, ephemeral=True)
    
    # async def open_form(interaction: discord.Interaction):
    #     print("button pressed")


class NewGroupView(BaseView):
    """ View for !gcreate command
    NOTE: not yet implemented.. try with !view. Maybe we can reuse the group_modal
    """

    @discord.ui.button(label="Gruppe erstellen", style=discord.ButtonStyle.green)
    async def new(self, inter, button) -> None:
        group_form = GroupModal()
        await inter.response.send_modal(group_form)
