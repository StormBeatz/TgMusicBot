#  Copyright (c) 2025 AshokShau
#  Licensed under the GNU AGPL v3.0: https://www.gnu.org/licenses/agpl-3.0.html
#  Part of the TgMusicBot project. All rights reserved where applicable.
from typing import Literal

from pytdbot import types

from src import config


def control_buttons(mode: Literal["play", "pause", "resume"], is_channel: bool) -> types.ReplyMarkupInlineKeyboard:
    prefix = "cplay" if is_channel else "play"

    def btn(text: str, name: str) -> types.InlineKeyboardButton:
        return types.InlineKeyboardButton(
            text=text,
            type=types.InlineKeyboardButtonTypeCallback(f"{prefix}_{name}".encode())
        )

    skip_btn = btn("⏩", "skip")
    stop_btn = btn("⏹️", "stop")
    pause_btn = btn("⏸️", "pause")
    resume_btn = btn("▶️", "resume")
    close_btn = btn("⏺ Close", "close")

    layouts = {
        "play": [[skip_btn, stop_btn, pause_btn, resume_btn], [close_btn]],
        "pause": [[skip_btn, stop_btn, resume_btn], [close_btn]],
        "resume": [[skip_btn, stop_btn, pause_btn], [close_btn]],
    }

    return types.ReplyMarkupInlineKeyboard(layouts.get(mode, [[close_btn]]))

CLOSE_BTN = types.InlineKeyboardButton(
    text="⏺ Close", type=types.InlineKeyboardButtonTypeCallback(b"play_close")
)

CHANNEL_BTN = types.InlineKeyboardButton(
    text="Channel 📡", type=types.InlineKeyboardButtonTypeUrl(config.SUPPORT_CHANNEL)
)

GROUP_BTN = types.InlineKeyboardButton(
    text="Support 💬", type=types.InlineKeyboardButtonTypeUrl(config.SUPPORT_GROUP)
)

SOURCE_BTN = types.InlineKeyboardButton(
    text="Source Code 🖥️", type=types.InlineKeyboardButtonTypeCallback(b"source")
)

DEVELOPER_BTN = types.InlineKeyboardButton(
    text="Developer 👨‍💻", type=types.InlineKeyboardButtonTypeUrl("https://t.me/Nikchil")
)

HELP_BTN = types.InlineKeyboardButton(
    text="Help 🆘", type=types.InlineKeyboardButtonTypeCallback(b"help_all")
)

BACK_BTN = types.InlineKeyboardButton(
    text="🔙 Back", type=types.InlineKeyboardButtonTypeCallback(b"back_to_start")
)

USER_BTN = types.InlineKeyboardButton(
    text="User Commands", type=types.InlineKeyboardButtonTypeCallback(b"help_user")
)

ADMIN_BTN = types.InlineKeyboardButton(
    text="Admin Commands", type=types.InlineKeyboardButtonTypeCallback(b"help_admin")
)

OWNER_BTN = types.InlineKeyboardButton(
    text="Owner Commands", type=types.InlineKeyboardButtonTypeCallback(b"help_owner")
)

DEVS_BTN = types.InlineKeyboardButton(
    text="Dev Commands", type=types.InlineKeyboardButtonTypeCallback(b"help_devs")
)

SupportButton = types.ReplyMarkupInlineKeyboard(
    [[CHANNEL_BTN], [GROUP_BTN]]
)

StartMenu = types.ReplyMarkupInlineKeyboard(
    [[CHANNEL_BTN], [GROUP_BTN], [SOURCE_BTN], [DEVELOPER_BTN], [HELP_BTN]]
)

SupportMenu = types.ReplyMarkupInlineKeyboard(
    [[GROUP_BTN]]
)

SourceMenu = types.ReplyMarkupInlineKeyboard([[BACK_BTN]])

HelpMenu = types.ReplyMarkupInlineKeyboard(
    [[USER_BTN, ADMIN_BTN], [OWNER_BTN, DEVS_BTN], [BACK_BTN]]
)

BackHelpMenu = types.ReplyMarkupInlineKeyboard([[HELP_BTN, CLOSE_BTN]])


# ─────────────────────
# Dynamic Keyboard Generator
# ─────────────────────


def add_me_markup(username: str) -> types.ReplyMarkupInlineKeyboard:
    """
    Returns an inline keyboard with a button to add the bot to a group
    and support buttons.
    """
    return types.ReplyMarkupInlineKeyboard(
        [
            [
                types.InlineKeyboardButton(
                    text="➕ Add me to your group",
                    type=types.InlineKeyboardButtonTypeUrl(
                        f"https://t.me/{username}?startgroup=true"
                    ),
                ),
            ],
            [HELP_BTN],
            [DEVELOPER_BTN, SOURCE_BTN],
            [CHANNEL_BTN, GROUP_BTN],
        ]
    )
