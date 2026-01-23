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
`config.json`
```json5
{
    "max_home": 5,  // the max num of homes allocated to each single player
    "back_expiry_window": 30, // in seconds
    "death_penalty_rate": 0.01,
    /**
    Once the death penalty feature is enabled and UMoney is installed:
    If a player's money is 2000 and the death penalty rate is set to 0.01,
    the player will lose 20 upon death.
    **/
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
    /**
    If set to false, the relevant feature button won't be displayed in the main form.
    
    The death penalty feature will only take effect if UMoney is installed.
    
    If UMoney isn't installed, the death penalty feature won't take effect - even if "death_penalty" is set to true.
    **/
}
```

`home.json`
```json5
{
    "umaru rize": { // player name
        "test home": {  // home name
            "dim": "Overworld", // home dimension
            "loc": [  // home location
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
```json5
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
```json5
{
    "umaru rize": true,
    "TheDeerInDream": false
    /**
    If set to false, other players won't be able to send TPA/TPAHere requests to this player.
    **/
}
```

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
* If you'd like your translated language to be included as one of the official languages of this plugin, feel free to shoot over a PR.

***

### 📷Screenshots
You can view related screenshots of UTP from images folder of this repo.
