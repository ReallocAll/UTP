import json
import math
import os
from copy import deepcopy
from pathlib import Path

from endstone import ColorFormat, Player
from endstone.form import ActionForm, ModalForm, Toggle, TextInput

from endstone_utp.storage import FileChangedError, atomic_write_json


ADMIN_PERMISSION = "utp.admin"
GLOBAL_FIELDS = (
    ("max_home", int),
    ("back_expiry_window", int),
    ("death_penalty_rate", float),
    ("tpr_range", int),
    ("tpr_cooldown", int),
)
TOGGLE_FIELDS = ("home", "warp", "back", "tpa", "tpr", "death_penalty")
DEFAULT_CONFIG = {
    "max_home": 5,
    "back_expiry_window": 30,
    "death_penalty_rate": 0.01,
    "tpr_range": 2000,
    "tpr_cooldown": 60,
    "is_enabled": dict.fromkeys(TOGGLE_FIELDS, True),
}
DEFAULT_CONFIG["is_enabled"]["death_penalty"] = False


def validate_config(data: dict) -> None:
    """Validate known fields without discarding unrelated keys from the file."""
    if not isinstance(data, dict):
        raise ValueError("config.json must contain an object")
    for key, value_type in GLOBAL_FIELDS:
        value = data.get(key)
        if value_type is int:
            if type(value) is not int or value <= 0:
                raise ValueError(f"{key} must be a positive integer")
        elif type(value) not in (int, float) or not 0 < value < 1 or not math.isfinite(value):
            raise ValueError(f"{key} must be finite and greater than 0 and less than 1")
    toggles = data.get("is_enabled")
    if not isinstance(toggles, dict):
        raise ValueError("is_enabled must contain an object")
    for key in TOGGLE_FIELDS:
        if type(toggles.get(key)) is not bool:
            raise ValueError(f"is_enabled.{key} must be a boolean")


def _reject_constant(value: str):
    raise ValueError(f"{value} is not valid JSON")


class Config:
    def __init__(self, main: "Main"):
        self.main = main
        self.lang_funct = main.lang_funct
        self.__config_data_file_path = Path(os.path.join(main.first_dir_path, "config.json"))
        self.__revision = 0
        try:
            self.config_data, self.__disk_content = self.__read_config_data()
        except FileNotFoundError as error:
            if self.__config_data_file_path.is_symlink():
                self.main.logger.error(f"Cannot load UTP config.json; broken symlink left unchanged: {error}")
                raise
            self.config_data = deepcopy(DEFAULT_CONFIG)
            self.__disk_content = atomic_write_json(
                self.__config_data_file_path, self.config_data, expected_content=None
            )
        except (OSError, ValueError) as error:
            self.main.logger.error(f"Cannot load UTP config.json; file left unchanged: {error}")
            raise

    def __read_config_data(self) -> tuple[dict, bytes]:
        content = self.__config_data_file_path.read_bytes()
        candidate = json.loads(content.decode("utf-8"), parse_constant=_reject_constant)
        validate_config(candidate)
        return candidate, content

    def __message(self, player: Player, key: str, *, error: bool = True) -> None:
        color = ColorFormat.RED if error else ColorFormat.YELLOW
        player.send_message(f"{color}{self.lang_funct.get_text(player, key)}")

    def __check_permission(self, player: Player) -> bool:
        if player.has_permission(ADMIN_PERMISSION):
            return True
        self.__message(player, "config.message.no_permission")
        return False

    def reload_config_main(self, player: Player) -> None:
        if not self.__check_permission(player):
            return
        form = ActionForm(
            title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                  f"{self.lang_funct.get_text(player, 'config.title')}",
            content=self.lang_funct.get_text(player, "config.content"),
            on_close=self.main.back_to_main_form,
        )
        for key, callback, icon in (
            ("config.button.reload", self.reload_from_disk, "textures/ui/refresh"),
            ("config.button.toggles", self.__edit_function_toggles, "textures/ui/craft_toggle_off"),
            ("config.button.global", self.__edit_global_config, "textures/ui/icon_setting"),
        ):
            form.add_button(
                f"{ColorFormat.YELLOW}{self.lang_funct.get_text(player, key)}",
                icon=icon, on_click=callback,
            )
        player.send_form(form)

    def reload_from_disk(self, player: Player) -> None:
        if not self.__check_permission(player):
            return
        try:
            candidate, content = self.__read_config_data()
        except (OSError, ValueError) as error:
            self.main.logger.error(f"Cannot reload UTP config.json; keeping active configuration: {error}")
            self.__message(player, "config.message.reload_failed")
            return
        self.config_data = candidate
        self.__disk_content = content
        self.__revision += 1
        self.__message(player, "config.message.reloaded", error=False)

    def __save_candidate(self, player: Player, candidate: dict, revision: int) -> None:
        # Recheck at the action, including permission revocation while a form is open.
        if not self.__check_permission(player):
            return
        if revision != self.__revision:
            self.__message(player, "config.message.conflict")
            return
        try:
            validate_config(candidate)
            content = atomic_write_json(
                self.__config_data_file_path, candidate, expected_content=self.__disk_content
            )
        except FileChangedError:
            self.__message(player, "config.message.conflict")
            return
        except (OSError, ValueError) as error:
            self.main.logger.error(f"Cannot save UTP config.json; keeping active configuration: {error}")
            self.__message(player, "config.message.save_failed")
            return
        self.config_data = candidate
        self.__disk_content = content
        self.__revision += 1
        self.__message(player, "config.message.saved", error=False)

    def __edit_function_toggles(self, player: Player) -> None:
        if not self.__check_permission(player):
            return
        candidate = deepcopy(self.config_data)
        revision = self.__revision
        controls = [
            Toggle(
                label=self.main.tpa_funct.button_text(player) if key == "tpa"
                else self.lang_funct.get_text(player, f"config.toggle.{key}"),
                default_value=candidate["is_enabled"][key],
            )
            for key in TOGGLE_FIELDS
        ]
        form = ModalForm(
            title=self.lang_funct.get_text(player, "config.button.toggles"),
            controls=controls,
            submit_button=self.lang_funct.get_text(player, "config.button.save"),
            on_close=self.reload_config_main,
        )

        def on_submit(p: Player, json_str: str) -> None:
            if not self.__check_permission(p):
                return
            try:
                values = json.loads(json_str)
                if not isinstance(values, list) or len(values) != len(TOGGLE_FIELDS):
                    raise ValueError("Incorrect toggle count")
                if any(type(value) is not bool for value in values):
                    raise ValueError("Toggles must be booleans")
                candidate["is_enabled"].update(zip(TOGGLE_FIELDS, values))
            except (ValueError, TypeError):
                self.__message(p, "message.error")
                return
            self.__save_candidate(p, candidate, revision)

        form.on_submit = on_submit
        player.send_form(form)

    def __edit_global_config(self, player: Player) -> None:
        if not self.__check_permission(player):
            return
        candidate = deepcopy(self.config_data)
        revision = self.__revision
        controls = [
            TextInput(
                label=self.lang_funct.get_text(player, f"config.field.{key}"),
                placeholder=self.lang_funct.get_text(
                    player, "config.hint.rate" if value_type is float else "config.hint.integer"
                ),
                default_value=str(candidate[key]),
            )
            for key, value_type in GLOBAL_FIELDS
        ]
        form = ModalForm(
            title=self.lang_funct.get_text(player, "config.button.global"),
            controls=controls,
            submit_button=self.lang_funct.get_text(player, "config.button.save"),
            on_close=self.reload_config_main,
        )

        def on_submit(p: Player, json_str: str) -> None:
            if not self.__check_permission(p):
                return
            try:
                values = json.loads(json_str)
                if not isinstance(values, list) or len(values) != len(GLOBAL_FIELDS):
                    raise ValueError("Incorrect field count")
                for (key, value_type), value in zip(GLOBAL_FIELDS, values):
                    if not isinstance(value, str):
                        raise ValueError("Text fields must contain strings")
                    candidate[key] = value_type(value)
                validate_config(candidate)
            except (ValueError, TypeError, OverflowError):
                self.__message(p, "message.error")
                return
            self.__save_candidate(p, candidate, revision)

        form.on_submit = on_submit
        player.send_form(form)
