import discord
from discord import Interaction
from discord import ButtonStyle
from discord.ui import TextInput, button
from views.base import BaseModal, BaseView
from cogs.group import organize_group as og
from utility.sanitizer import sanitize
from config import messages as msg


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
    
    @button(label="Beitreten", emoji="🍻", style=ButtonStyle.green)
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

    # adding a component using it's decorator (fancy shit)
    @button(label="Bearbeiten", emoji="✏️", style=ButtonStyle.blurple)
    async def edit(self, inter, button) -> None:
        """ open modal to edit group on button click
        TODO: not fully implemented yet, modal is just an example (not saving)
        """
        # group_form = GroupModal()
        # await inter.response.send_modal(group_form)
        print(inter.name)
        # await inter.response.edit_message("Noch nicht implementiert", view=self)

    @button(label="Löschen", emoji="🗑️", style=ButtonStyle.red)
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
