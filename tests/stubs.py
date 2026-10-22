"""Minimal Endstone test doubles; these tests do not run a Bedrock server."""

import sys
from types import ModuleType, SimpleNamespace


class Form:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.buttons = []

    def add_button(self, text, **kwargs):
        self.buttons.append(SimpleNamespace(text=text, **kwargs))


class Player:
    def __init__(self, name="Alice", *, admin=False, locale="en_US"):
        self.name = name
        self.admin = admin
        self.is_op = admin
        self.locale = locale
        self.xuid = "xuid-" + name
        self.forms = []
        self.messages = []
        self.location = SimpleNamespace(dimension=SimpleNamespace(name="Overworld"), x=1, y=64, z=2)

    def has_permission(self, permission):
        if permission == "Main.command.utp":
            return getattr(self, "command_allowed", True)
        return self.admin

    def send_form(self, form):
        self.forms.append(form)

    def send_message(self, message):
        self.messages.append(message)


class Logger:
    def __init__(self):
        self.errors = []

    def error(self, message):
        self.errors.append(message)


class Lang:
    def get_text(self, player, key):
        return key


def make_main(directory):
    return SimpleNamespace(
        first_dir_path=str(directory), lang_funct=Lang(), logger=Logger(), is_enabled=True,
        back_to_main_form=lambda player: None,
        tpa_funct=SimpleNamespace(button_text=lambda player: "Teleport Request"),
        server=SimpleNamespace(online_players=[], get_player=lambda name: None),
    )


def install():
    if getattr(sys.modules.get("endstone"), "_utp_test_stub", False):
        return
    endstone = ModuleType("endstone")
    endstone._utp_test_stub = True
    endstone.Player = Player
    endstone.ColorFormat = SimpleNamespace(**dict.fromkeys(
        ("BOLD", "LIGHT_PURPLE", "GREEN", "YELLOW", "RED", "WHITE"), ""
    ))
    sys.modules["endstone"] = endstone
    for module, names in {
        "form": ("ActionForm", "ModalForm", "TextInput", "Toggle", "Dropdown"),
        "event": ("PlayerJoinEvent", "PlayerDeathEvent"),
        "level": ("Location",),
        "command": ("Command", "CommandSender", "CommandSenderWrapper"),
        "plugin": ("Plugin",),
    }.items():
        child = ModuleType("endstone." + module)
        for name in names:
            setattr(child, name, Form)
        sys.modules[child.__name__] = child
    sys.modules["endstone.event"].event_handler = lambda fn: fn
