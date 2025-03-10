# /mnt/home2/mud/systems/attack_messages.py
from typing import Dict, List, Tuple
from ..driver import MudObject
from .combat import Attack

class AttackMessages:
    def __init__(self):
        self.messages: Dict[str, List[Tuple[int, Tuple[str, str, str]]]] = {
            # Blunt Weapons
            "blunt": [
                (0, ("You swing at $I clumsily.", "$N swings at you, missing.", "$N swings at $I and misses.")),
                (20, ("You tap $I’s $z with a light thud.", "$N taps your $z lightly.", "$N taps $I’s $z with a thud.")),
                (60, ("You hit $I in the $z with force.", "$N hits your $z firmly.", "$N strikes $I in the $z.")),
                (100, ("You bruise $I’s $z with a solid blow.", "$N bruises your $z painfully.", "$N bruises $I’s $z.")),
                (140, ("You smash $I’s $z with a hard strike.", "$N smashes your $z hard.", "$N smashes $I’s $z.")),
                (180, ("You crush $I’s $z under Netherese might.", "$N crushes your $z brutally.", "$N crushes $I’s $z.")),
                (220, ("You pulverize $I’s $z with devastating force.", "$N pulverizes your $z.", "$N pulverizes $I’s $z.")),
                (5000, ("You mash $I’s $z into a pulp with Veil-born power.", "$N mashes your $z into ruin.", "$N mashes $I’s $z to pulp."))
            ],
            "blunt-mace": [
                (0, ("You swing your mace at $I, missing.", "$N swings a mace at you, missing.", "$N swings a mace at $I and misses.")),
                (20, ("You tap $I’s $z with your mace.", "$N taps your $z with a mace.", "$N taps $I’s $z with a mace.")),
                (60, ("You bash $I’s $z with your mace.", "$N bashes your $z with a mace.", "$N bashes $I’s $z.")),
                (100, ("You bruise $I’s $z with a mace strike.", "$N bruises your $z with a mace.", "$N bruises $I’s $z.")),
                (140, ("You smash $I’s $z with a mace blow.", "$N smashes your $z with a mace.", "$N smashes $I’s $z.")),
                (180, ("You crush $I’s $z with your mace’s weight.", "$N crushes your $z with a mace.", "$N crushes $I’s $z.")),
                (220, ("You shatter $I’s $z with a mace’s force.", "$N shatters your $z with a mace.", "$N shatters $I’s $z.")),
                (5000, ("You obliterate $I’s $z with your mace’s might.", "$N obliterates your $z with a mace.", "$N obliterates $I’s $z."))
            ],
            "blunt-flail": [
                (0, ("You swing your flail at $I, missing.", "$N swings a flail at you, missing.", "$N swings a flail at $I and misses.")),
                (20, ("You tap $I’s $z with a flail’s chain.", "$N taps your $z with a flail.", "$N taps $I’s $z with a flail.")),
                (60, ("You lash $I’s $z with a flail’s strike.", "$N lashes your $z with a flail.", "$N lashes $I’s $z.")),
                (100, ("You whip $I’s $z with a flail’s force.", "$N whips your $z painfully.", "$N whips $I’s $z.")),
                (140, ("You smash $I’s $z with a flail’s swing.", "$N smashes your $z with a flail.", "$N smashes $I’s $z.")),
                (180, ("You crush $I’s $z with a flail’s might.", "$N crushes your $z brutally.", "$N crushes $I’s $z with a flail.")),
                (220, ("You shatter $I’s $z with a flail’s fury.", "$N shatters your $z with a flail.", "$N shatters $I’s $z.")),
                (5000, ("You pulverize $I’s $z with a flail’s wrath.", "$N pulverizes your $z to ruin.", "$N pulverizes $I’s $z with a flail."))
            ],
            "blunt-hands": [
                (0, ("You punch at $I, missing.", "$N punches at you and misses.", "$N swings a fist at $I and misses.")),
                (20, ("You poke $I’s $z with a weak jab.", "$N pokes your $z lightly.", "$N jabs $I’s $z weakly.")),
                (60, ("You hit $I’s $z with a solid punch.", "$N punches your $z firmly.", "$N punches $I in the $z.")),
                (100, ("You uppercut $I’s $z hard.", "$N uppercuts your $z painfully.", "$N uppercuts $I’s $z.")),
                (140, ("You slam $I’s $z with a fierce hook.", "$N hooks your $z brutally.", "$N hooks $I’s $z.")),
                (180, ("You batter $I’s $z with rapid fists.", "$N batters your $z with fists.", "$N batters $I’s $z.")),
                (220, ("You pummel $I’s $z into submission.", "$N pummels your $z relentlessly.", "$N pummels $I’s $z.")),
                (5000, ("You beat $I’s $z to a bloody pulp.", "$N beats your $z to pulp.", "$N beats $I’s $z to ruin."))
            ],
            "blunt-feet": [
                (0, ("You kick at $I, missing.", "$N kicks at you and misses.", "$N kicks at $I and misses.")),
                (20, ("You tap $I’s $z with a light kick.", "$N taps your $z with a kick.", "$N kicks $I’s $z lightly.")),
                (60, ("You kick $I’s $z firmly.", "$N kicks your $z with force.", "$N kicks $I in the $z.")),
                (100, ("You boot $I’s $z with a solid kick.", "$N boots your $z painfully.", "$N boots $I’s $z.")),
                (140, ("You smash $I’s $z with a hard kick.", "$N smashes your $z with a kick.", "$N smashes $I’s $z.")),
                (180, ("You crush $I’s $z with a vicious kick.", "$N crushes your $z with a kick.", "$N crushes $I’s $z.")),
                (220, ("You shatter $I’s $z with a powerful kick.", "$N shatters your $z with a kick.", "$N shatters $I’s $z.")),
                (5000, ("You kick $I’s $z into a bloody mess.", "$N kicks your $z to ruin.", "$N kicks $I’s $z to pulp."))
            ],
            # Sharp Weapons
            "sharp": [
                (0, ("You slash at $I, missing.", "$N slashes at you, missing.", "$N slashes at $I and misses.")),
                (20, ("You nick $I’s $z with a glancing cut.", "$N nicks your $z lightly.", "$N nicks $I’s $z.")),
                (60, ("You scratch $I’s $z with a sharp edge.", "$N scratches your $z.", "$N scratches $I’s $z.")),
                (100, ("You cut $I’s $z with a clean slice.", "$N cuts your $z painfully.", "$N cuts $I’s $z.")),
                (140, ("You slice $I’s $z deeply.", "$N slices your $z with force.", "$N slices $I’s $z.")),
                (180, ("You hack $I’s $z with a vicious swing.", "$N hacks your $z brutally.", "$N hacks $I’s $z.")),
                (220, ("You rend $I’s $z with Netherese precision.", "$N rends your $z apart.", "$N rends $I’s $z.")),
                (5000, ("You chop $I’s $z into bloody ribbons.", "$N chops your $z to shreds.", "$N chops $I’s $z into ruin."))
            ],
            "sharp-dagger": [
                (0, ("You swipe your dagger at $I, missing.", "$N swipes a dagger at you, missing.", "$N swipes a dagger at $I and misses.")),
                (20, ("You nick $I’s $z with your dagger.", "$N nicks your $z with a dagger.", "$N nicks $I’s $z with a dagger.")),
                (60, ("You scratch $I’s $z with your dagger.", "$N scratches your $z with a dagger.", "$N scratches $I’s $z.")),
                (100, ("You cut $I’s $z with a dagger’s edge.", "$N cuts your $z with a dagger.", "$N cuts $I’s $z.")),
                (140, ("You slice $I’s $z with a dagger’s thrust.", "$N slices your $z with a dagger.", "$N slices $I’s $z.")),
                (180, ("You gash $I’s $z with a dagger’s slash.", "$N gashes your $z brutally.", "$N gashes $I’s $z.")),
                (220, ("You rend $I’s $z with a dagger’s precision.", "$N rends your $z with a dagger.", "$N rends $I’s $z.")),
                (5000, ("You shred $I’s $z with a dagger’s fury.", "$N shreds your $z to ribbons.", "$N shreds $I’s $z into ruin."))
            ],
            "sharp-sword": [
                (0, ("You swing your sword at $I, missing.", "$N swings a sword at you, missing.", "$N swings a sword at $I and misses.")),
                (20, ("You graze $I’s $z with your sword.", "$N grazes your $z with a sword.", "$N grazes $I’s $z with a sword.")),
                (60, ("You slice $I’s $z with your sword.", "$N slices your $z with a sword.", "$N slices $I’s $z.")),
                (100, ("You cut $I’s $z with a sword’s edge.", "$N cuts your $z with a sword.", "$N cuts $I’s $z.")),
                (140, ("You slash $I’s $z with a sword’s sweep.", "$N slashes your $z deeply.", "$N slashes $I’s $z.")),
                (180, ("You hack $I’s $z with a sword’s might.", "$N hacks your $z brutally.", "$N hacks $I’s $z.")),
                (220, ("You cleave $I’s $z with a sword’s force.", "$N cleaves your $z apart.", "$N cleaves $I’s $z.")),
                (5000, ("You carve $I’s $z into ribbons with your sword.", "$N carves your $z to shreds.", "$N carves $I’s $z into ruin."))
            ],
            "sharp-heavy_sword": [
                (0, ("You swing your heavy sword at $I, missing.", "$N swings a heavy sword at you, missing.", "$N swings a heavy sword at $I and misses.")),
                (20, ("You nick $I’s $z with your heavy sword.", "$N nicks your $z with a heavy sword.", "$N nicks $I’s $z with a heavy sword.")),
                (60, ("You chop $I’s $z with your heavy sword.", "$N chops your $z with a heavy sword.", "$N chops $I’s $z.")),
                (100, ("You hack $I’s $z with a heavy sword’s weight.", "$N hacks your $z painfully.", "$N hacks $I’s $z.")),
                (140, ("You cleave $I’s $z with a heavy sword’s swing.", "$N cleaves your $z deeply.", "$N cleaves $I’s $z.")),
                (180, ("You split $I’s $z with a heavy sword’s force.", "$N splits your $z brutally.", "$N splits $I’s $z.")),
                (220, ("You rend $I’s $z with a heavy sword’s might.", "$N rends your $z apart.", "$N rends $I’s $z.")),
                (5000, ("You sunder $I’s $z with a heavy sword’s wrath.", "$N sunders your $z to ruin.", "$N sunders $I’s $z into pieces."))
            ],
            "sharp-axe": [
                (0, ("You swing your axe at $I, missing.", "$N swings an axe at you, missing.", "$N swings an axe at $I and misses.")),
                (20, ("You nick $I’s $z with your axe.", "$N nicks your $z with an axe.", "$N nicks $I’s $z with an axe.")),
                (60, ("You chop $I’s $z with your axe.", "$N chops your $z with an axe.", "$N chops $I’s $z.")),
                (100, ("You hack $I’s $z with an axe’s edge.", "$N hacks your $z painfully.", "$N hacks $I’s $z.")),
                (140, ("You cleave $I’s $z with an axe’s swing.", "$N cleaves your $z deeply.", "$N cleaves $I’s $z.")),
                (180, ("You split $I’s $z with an axe’s might.", "$N splits your $z brutally.", "$N splits $I’s $z.")),
                (220, ("You rend $I’s $z with an axe’s force.", "$N rends your $z apart.", "$N rends $I’s $z.")),
                (5000, ("You chop $I’s $z into chunks with your axe.", "$N chops your $z to pieces.", "$N chops $I’s $z into ruin."))
            ],
            # Piercing Weapons
            "piercing": [
                (0, ("You thrust at $I, missing.", "$N thrusts at you, missing.", "$N thrusts at $I and misses.")),
                (20, ("You jab $I’s $z lightly.", "$N jabs your $z with a prick.", "$N jabs $I’s $z.")),
                (60, ("You pierce $I’s $z with a quick stab.", "$N pierces your $z.", "$N pierces $I’s $z.")),
                (100, ("You impale $I’s $z with force.", "$N impales your $z painfully.", "$N impales $I’s $z.")),
                (140, ("You skewer $I’s $z with a deep thrust.", "$N skewers your $z.", "$N skewers $I’s $z.")),
                (180, ("You run $I through the $z with precision.", "$N runs you through the $z.", "$N runs $I through the $z.")),
                (220, ("You gore $I’s $z with Veil-sharpened might.", "$N gores your $z brutally.", "$N gores $I’s $z.")),
                (5000, ("You kebab $I’s $z with devastating power.", "$N turns your $z into a kebab.", "$N kebabs $I’s $z."))
            ],
            "piercing-dagger": [
                (0, ("You stab at $I with your dagger, missing.", "$N stabs at you with a dagger, missing.", "$N stabs at $I with a dagger and misses.")),
                (20, ("You prick $I’s $z with your dagger.", "$N pricks your $z with a dagger.", "$N pricks $I’s $z with a dagger.")),
                (60, ("You stab $I’s $z with your dagger.", "$N stabs your $z with a dagger.", "$N stabs $I’s $z.")),
                (100, ("You pierce $I’s $z with a dagger’s thrust.", "$N pierces your $z painfully.", "$N pierces $I’s $z.")),
                (140, ("You impale $I’s $z with a dagger’s stab.", "$N impales your $z deeply.", "$N impales $I’s $z.")),
                (180, ("You skewer $I’s $z with a dagger’s lunge.", "$N skewers your $z brutally.", "$N skewers $I’s $z.")),
                (220, ("You gore $I’s $z with a dagger’s precision.", "$N gores your $z with a dagger.", "$N gores $I’s $z.")),
                (5000, ("You run $I’s $z through with your dagger.", "$N runs your $z through with a dagger.", "$N runs $I’s $z through."))
            ],
            "piercing-pole_arm": [
                (0, ("You thrust your pole arm at $I, missing.", "$N thrusts a pole arm at you, missing.", "$N thrusts a pole arm at $I and misses.")),
                (20, ("You jab $I’s $z with your pole arm.", "$N jabs your $z with a pole arm.", "$N jabs $I’s $z with a pole arm.")),
                (60, ("You pierce $I’s $z with your pole arm.", "$N pierces your $z with a pole arm.", "$N pierces $I’s $z.")),
                (100, ("You impale $I’s $z with a pole arm’s thrust.", "$N impales your $z painfully.", "$N impales $I’s $z.")),
                (140, ("You skewer $I’s $z with a pole arm’s lunge.", "$N skewers your $z deeply.", "$N skewers $I’s $z.")),
                (180, ("You run $I through the $z with a pole arm.", "$N runs you through the $z with a pole arm.", "$N runs $I through the $z.")),
                (220, ("You gore $I’s $z with a pole arm’s might.", "$N gores your $z brutally.", "$N gores $I’s $z.")),
                (5000, ("You kebab $I’s $z with a pole arm’s power.", "$N kebabs your $z with a pole arm.", "$N kebabs $I’s $z."))
            ],
            # Magic Damage Types
            "magic-fire": [
                (0, ("You hurl fire at $I, but it fizzles.", "$N’s fire fizzles before you.", "$N’s fire fails against $I.")),
                (20, ("You singe $I’s $z with a spark of flame.", "$N singes your $z with flame.", "$N singes $I’s $z.")),
                (60, ("You scorch $I’s $z with a burst of fire.", "$N scorches your $z with fire.", "$N scorches $I’s $z.")),
                (100, ("You burn $I’s $z with a fiery blast.", "$N burns your $z painfully.", "$N burns $I’s $z.")),
                (140, ("You roast $I’s $z with Netherese flames.", "$N roasts your $z with fire.", "$N roasts $I’s $z.")),
                (180, ("You char $I’s $z with intense heat.", "$N chars your $z brutally.", "$N chars $I’s $z.")),
                (220, ("You incinerate $I’s $z with arcane fire.", "$N incinerates your $z.", "$N incinerates $I’s $z.")),
                (5000, ("You cremate $I’s $z with Mystra’s inferno.", "$N cremates your $z to ash.", "$N cremates $I’s $z."))
            ],
            "magic-cold": [
                (0, ("You cast cold at $I, but it fades.", "$N’s cold fades before you.", "$N’s cold fails against $I.")),
                (20, ("You chill $I’s $z with a frosty touch.", "$N chills your $z lightly.", "$N chills $I’s $z.")),
                (60, ("You freeze $I’s $z with icy shards.", "$N freezes your $z with ice.", "$N freezes $I’s $z.")),
                (100, ("You frost $I’s $z with a cold blast.", "$N frosts your $z painfully.", "$N frosts $I’s $z.")),
                (140, ("You numb $I’s $z with Netherese frost.", "$N numbs your $z with cold.", "$N numbs $I’s $z.")),
                (180, ("You shatter $I’s $z with icy power.", "$N shatters your $z with ice.", "$N shatters $I’s $z.")),
                (220, ("You encase $I’s $z in arcane ice.", "$N encases your $z in ice.", "$N encases $I’s $z.")),
                (5000, ("You freeze $I’s $z solid with Mystra’s chill.", "$N freezes your $z solid.", "$N freezes $I’s $z solid."))
            ],
            "magic-lightning": [
                (0, ("You hurl lightning at $I, but it sparks out.", "$N’s lightning sparks out before you.", "$N’s lightning fails against $I.")),
                (20, ("You zap $I’s $z with a faint jolt.", "$N zaps your $z lightly.", "$N zaps $I’s $z.")),
                (60, ("You shock $I’s $z with a bolt of lightning.", "$N shocks your $z with lightning.", "$N shocks $I’s $z.")),
                (100, ("You jolt $I’s $z with an electric surge.", "$N jolts your $z painfully.", "$N jolts $I’s $z.")),
                (140, ("You blast $I’s $z with Netherese lightning.", "$N blasts your $z with lightning.", "$N blasts $I’s $z.")),
                (180, ("You fry $I’s $z with a thunderous arc.", "$N fries your $z brutally.", "$N fries $I’s $z.")),
                (220, ("You electrify $I’s $z with arcane power.", "$N electrifies your $z.", "$N electrifies $I’s $z.")),
                (5000, ("You vaporize $I’s $z with Mystra’s storm.", "$N vaporizes your $z with lightning.", "$N vaporizes $I’s $z."))
            ],
            "magic-force": [
                (0, ("You hurl force at $I, but it dissipates.", "$N’s force dissipates before you.", "$N’s force fails against $I.")),
                (20, ("You nudge $I’s $z with a force ripple.", "$N nudges your $z with force.", "$N nudges $I’s $z.")),
                (60, ("You strike $I’s $z with a force wave.", "$N strikes your $z with force.", "$N strikes $I’s $z.")),
                (100, ("You blast $I’s $z with a force pulse.", "$N blasts your $z painfully.", "$N blasts $I’s $z.")),
                (140, ("You slam $I’s $z with Netherese force.", "$N slams your $z with force.", "$N slams $I’s $z.")),
                (180, ("You crush $I’s $z with a force surge.", "$N crushes your $z brutally.", "$N crushes $I’s $z.")),
                (220, ("You shatter $I’s $z with arcane force.", "$N shatters your $z with force.", "$N shatters $I’s $z.")),
                (5000, ("You obliterate $I’s $z with Mystra’s force.", "$N obliterates your $z.", "$N obliterates $I’s $z."))
            ],
            "magic-necrotic": [
                (0, ("You cast necrosis at $I, but it fades.", "$N’s necrosis fades before you.", "$N’s necrosis fails against $I.")),
                (20, ("You wither $I’s $z with a dark touch.", "$N withers your $z lightly.", "$N withers $I’s $z.")),
                (60, ("You blight $I’s $z with necrotic energy.", "$N blights your $z with darkness.", "$N blights $I’s $z.")),
                (100, ("You decay $I’s $z with a necrotic pulse.", "$N decays your $z painfully.", "$N decays $I’s $z.")),
                (140, ("You rot $I’s $z with Netherese blight.", "$N rots your $z with necrosis.", "$N rots $I’s $z.")),
                (180, ("You corrupt $I’s $z with dark power.", "$N corrupts your $z brutally.", "$N corrupts $I’s $z.")),
                (220, ("You dissolve $I’s $z with arcane rot.", "$N dissolves your $z with necrosis.", "$N dissolves $I’s $z.")),
                (5000, ("You consume $I’s $z with Mystra’s deathly grasp.", "$N consumes your $z to dust.", "$N consumes $I’s $z."))
            ]
            # Add more: acid, thunder, radiant, psychic as needed
        }

    def get_message(self, att: Attack) -> Tuple[str, str, str]:
        damage = att.damage
        damage_type = att.attack_data[2] if att.attack_data else "blunt"
        if att.attack_weapon == att.attacker:
            damage_type = "blunt-hands" if att.attack_data[0] == "hands" else "blunt-feet"
        elif att.attack_weapon.attrs.get("weapon_type"):
            damage_type = f"{att.attack_data[2]}-{att.attack_weapon.attrs['weapon_type'].replace(' ', '_')}"
        type_messages = self.messages.get(damage_type, self.messages[att.attack_data[2] if att.attack_data else "blunt"])

        for threshold, messages in type_messages:
            if damage <= threshold or threshold == 5000:
                attacker_msg, target_msg, room_msg = messages
                break

        replacements = {
            "$N": att.attacker.short(),
            "$I": att.person_hit.short(),
            "$z": att.target_zone
        }
        return (
            attacker_msg.replace("$N", replacements["$N"]).replace("$I", replacements["$I"]).replace("$z", replacements["$z"]),
            target_msg.replace("$N", replacements["$N"]).replace("$I", replacements["$I"]).replace("$z", replacements["$z"]),
            room_msg.replace("$N", replacements["$N"]).replace("$I", replacements["$I"]).replace("$z", replacements["$z"])
        )

attack_messages = AttackMessages()