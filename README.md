<code><a href="https://github.com/umarurize/UTP"><img height="25" src="./logo/UTP.png" alt="UTP" /></a>&nbsp;UTP</code>

![Total Git clones](https://img.shields.io/badge/dynamic/json?label=Total%20Git%20clones&query=$&url=https://cdn.jsdelivr.net/gh/umarurize/UTP@master/clone_count.txt&color=brightgreen)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/umarurize/UTP/total)
![](https://img.shields.io/badge/language-python-blue.svg) 
[![GitHub License](https://img.shields.io/github/license/umarurize/UTP)](LICENSE)

***

### ✨ Introductions
* **Rich features**
- [x] Home
- [x] Warp
- [x] Back
- [x] TPA & TPAHere
- [x] TPR
- [x] Death penalty (UMoney required)
* **Support with full GUI forms**
* **Support with hot reloading**
* **Support with localized multi-languages**

***

### 📦 Installation
**Tips:** *UTP is adapted to all versions of Endstone.*

<details> 
<summary>Check pre-plugins</summary>

* **Optional pre-plugins**
  * [ZX_UI](https://www.minebbs.com/resources/zx-ui.9830/)
  * [UMoney](https://github.com/U-Blocks/UMoney)

**Tips:** *the death penalty feature will only take effect if you have UMoney installed.*

</details>

1. Ensure you have downloaded the correct version and installed all required pre-plugins
2. Place the `.whl` file into your server's `plugins` folder
3. Restart your server
4. Enter the command `/utp` to call out the main form of UTP

***

### 📄 File structure
```
plugins/
├─ utp/
│  ├─ config.json
│  ├─ home.json
│  ├─ warp.json
│  ├─ tpa_setting.json
│  ├─ lang/
│  │  ├─ zh_CN.json
│  │  ├─ en_US.json
```

***

### ⚙️ Configuration
All files use strict JSON: comments, trailing commas, `NaN` and `Infinity` are not supported. Back up files before editing.

#### Permissions and applying changes
- `/utp` remains available to players through `Main.command.utp` (default: everyone).
- Configuration management requires `utp.admin` (default: operators). Permission is checked both when opening a form and when submitting or reloading, including after permission changes.
- **Configuration → Reload config.json from disk** reads and validates the complete file, then applies it. An invalid or unreadable file leaves the last good runtime configuration active and logs the error. At startup, an invalid existing configuration prevents UTP from loading; it is not replaced with defaults.
- **Edit function toggles** and **Edit global configuration** edit the active values. **Save and apply** validates the whole candidate and saves it before changing runtime state.
- A save is refused if another form/reload has superseded the editor, or if `config.json` has changed on disk. Reload from disk and reopen the editor before retrying. The disk check is best-effort, not cross-process locking; avoid editing the file at the same time as an in-game save.
- Configuration and TPA settings use temporary sibling files and atomic replacement, so a failed write does not truncate the original. The server needs write permission to the containing directory as well as read access to the files.

#### Configuration fields
`max_home`, `back_expiry_window`, `tpr_range` and `tpr_cooldown` must be positive JSON integers. Expiry and cooldown are in seconds. `death_penalty_rate` must be a finite number strictly between 0 and 1. Every documented `is_enabled` field must be a JSON boolean; required fields cannot be omitted. Object key order does not matter, and extra configuration keys are preserved.

Lowering `max_home` does not delete existing homes; players at or above the new limit cannot add more. Death penalty requires UMoney: at a rate of `0.01`, a balance of 2000 loses 20 on death. Feature toggles control the corresponding functions/menu entries.

`config.json`
```json
{
    "max_home": 5,
    "back_expiry_window": 30,
    "death_penalty_rate": 0.01,
    "tpr_range": 2000,
    "tpr_cooldown": 60,
    "is_enabled": {
        "home": true,
        "warp": true,
        "back": true,
        "tpa": true,
        "tpr": true,
        "death_penalty": false
    }
}
```

`home.json`
```json
{
    "umaru rize": {
        "test home": {
            "dim": "Overworld",
            "loc": [
                -285,
                49,
                -250
            ]
        },
        "Our first home": {
            "dim": "Nether",
            "loc": [
                -123,
                29,
                37
            ]
        }
    },
    "TheDeerInDream": {}
}
```

`warp.json`
```json
{
    "test warp1": {
        "dim": "Overworld",
        "loc": [
            0,
            0,
            0
        ]
    },
    "test warp2": {
        "dim": "Nether",
        "loc": [
            0,
            0, 
            0
        ]
    }
}
```

`tpa_setting.json`
```json
{
    "umaru rize": {
        "enabled": true,
        "blacklist": [],
        "whitelist": []
    },
    "TheDeerInDream": {
        "enabled": false,
        "blacklist": [],
        "whitelist": []
    }
}
```

Legacy player values such as `"TheDeerInDream": false` are still supported and migrated without changing the enabled value. Names in blacklists/whitelists are matched case-insensitively; a blacklist entry wins if a name appears in both. Whitelisted senders are automatically accepted when requests are enabled; other allowed senders still receive a confirmation prompt. Operator direct-teleport modes retain their existing behavior.

If TPA settings cannot be parsed, validated, read or saved, UTP preserves the existing file and disables TPA requests/settings rather than resetting player privacy choices. Check the logged error, repair the file or restore a backup, fix file/directory permissions if needed, and restart the server. The configuration reload button reloads only `config.json`; edit `home.json`, `warp.json` and `tpa_setting.json` with the server stopped.

***

### 🌎 Localized multi-language
* Currently supported localized languages for UTP:
- [x] `zh_CN`
- [x] `en_US`
* How to add more languages to UTP? Here we use Japanese for an example.
  * Create a file named `ja_JP.json` and place it into `lang` folder
  * Copy all key-value pairs from `en_US.json` and paste them into `ja_JP.json`
  * Refer to the English values and translate them all into Japanese, then save the file.
  * Restart your server, and you're all done!
* New configuration translation keys have built-in English/Chinese fallbacks for existing installations. Existing language files and custom translations are not overwritten.
* If you'd like your translated language to be included as one of the official languages of this plugin, feel free to shoot over a PR.

***

### 📷Screenshots
You can view related screenshots of UTP from images folder of this repo.


### Development checks
Run the focused regression suite with Python 3.10 or newer (no additional test dependencies):

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
python -m compileall -q src/endstone_utp tests
```

These tests use lightweight Endstone form/player doubles and real temporary JSON files. They cover configuration permissions, validation, reload/write conflicts and failures, TPA data preservation/migration, and home limits. They do not replace a smoke test on a real Endstone server.
