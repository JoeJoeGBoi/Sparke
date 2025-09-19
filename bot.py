"""Discord invite-role bot entry point.

This bot listens for member joins and assigns roles based on the invite code
used during the join. It exposes commands for managing invite-role mappings.

The bot expects a bot token supplied via the ``DISCORD_TOKEN`` environment
variable. When running under Docker (see ``Dockerfile``) this variable is
passed through from the host.
"""
from __future__ import annotations

import logging
import os
from typing import Dict

import discord
from discord.ext import commands

# Configure basic logging so container logs surface useful information
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Intents for tracking invites and members
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
# ``message_content`` intent is required for prefix commands to function.
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Dictionary to store invite-to-role mappings {invite_code: role_id}
invite_role_map: Dict[str, int] = {}
# Dictionary to track uses of invites per guild {guild_id: {invite_code: uses}}
invite_uses: Dict[int, Dict[str, int]] = {}


@bot.event
async def on_ready() -> None:
    logger.info("Logged in as %s", bot.user)
    # Initialize invite uses
    for guild in bot.guilds:
        try:
            invites = await guild.invites()
        except discord.Forbidden:
            logger.warning("Missing permissions to view invites for guild %s", guild.name)
            continue
        invite_uses[guild.id] = {invite.code: invite.uses for invite in invites}
    logger.info("Cached invite usage for %d guild(s)", len(invite_uses))


@bot.command(name="createinvite")
@commands.guild_only()
@commands.has_permissions(manage_guild=True)
async def create_invite(ctx: commands.Context, role: discord.Role, max_uses: int = 0, max_age: int = 0) -> None:
    """Create an invite linked to a specific role.

    Example: ``!createinvite @Role 5 3600``
    """
    invite = await ctx.channel.create_invite(max_uses=max_uses, max_age=max_age, unique=True)
    invite_role_map[invite.code] = role.id
    await ctx.send(f"🔗 Invite created: {invite.url} (Grants role: {role.name})")
    logger.info("Created invite %s mapped to role %s (%s)", invite.code, role.name, role.id)


@bot.command(name="listinvites")
@commands.guild_only()
async def list_invites(ctx: commands.Context) -> None:
    """List all active invite-to-role mappings."""
    if not invite_role_map:
        await ctx.send("No invite-role mappings set up yet.")
        return

    lines = []
    for code, role_id in invite_role_map.items():
        role = ctx.guild.get_role(role_id)
        role_name = role.name if role else "Deleted Role"
        lines.append(f"Invite `{code}` → Role `{role_name}`")
    await ctx.send("\n".join(lines))


@bot.command(name="clearinvites")
@commands.guild_only()
@commands.has_permissions(manage_guild=True)
async def clear_invites(ctx: commands.Context) -> None:
    """Clear all invite-role mappings."""
    invite_role_map.clear()
    await ctx.send("🧹 Cleared all invite-role mappings.")
    logger.info("Invite-role mappings cleared in guild %s", ctx.guild.name if ctx.guild else "DM")


@bot.event
async def on_member_join(member: discord.Member) -> None:
    guild = member.guild
    try:
        invites = await guild.invites()
    except discord.Forbidden:
        logger.warning("Missing permissions to view invites for guild %s", guild.name)
        return

    old_uses = invite_uses.get(guild.id, {})

    # Find which invite was used
    used_invite = None
    for invite in invites:
        if old_uses.get(invite.code, 0) < invite.uses:
            used_invite = invite
            break

    # Update stored invite uses
    invite_uses[guild.id] = {invite.code: invite.uses for invite in invites}

    if used_invite and used_invite.code in invite_role_map:
        role_id = invite_role_map[used_invite.code]
        role = guild.get_role(role_id)
        if role is None:
            logger.warning("Role %s not found in guild %s", role_id, guild.name)
            return
        try:
            await member.add_roles(role, reason=f"Joined using invite {used_invite.code}")
        except discord.Forbidden:
            logger.warning("Missing permissions to assign role %s in guild %s", role.name, guild.name)
            return
        logger.info("Assigned role %s to %s via invite %s", role.name, member.display_name, used_invite.code)


def main() -> None:
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN environment variable is not set.")

    bot.run(token)


if __name__ == "__main__":
    main()
