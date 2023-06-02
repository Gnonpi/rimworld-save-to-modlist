"""Script allowing to extract your mod list from a RimWorld save file."""
import dataclasses
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import cast

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

INPUT_SAVE_PATH = "rws"
OUTPUT_MODLIST_PATH = "rml"


@dataclasses.dataclass(frozen=True)
class ModFromSave:
    """Info about one single mod."""

    mod_id: str
    mod_steam_id: str
    mod_name: str


def extract_mod_from_save(input_save_path: Path) -> tuple[str, list[ModFromSave]]:
    """
    Read the save file and extract the game version and the list of mod used.

    :param input_save_path:
        path to read the save file from

    :return:
        a tuple of two elements: the game version and the list of mod
    """
    logger.info(f"Loading mods from save file at {input_save_path}")
    tree = ET.parse(input_save_path)
    root = tree.getroot()
    meta_el = [child for child in root if child.tag == "meta"]
    game_version = None
    for meta_child in meta_el[0]:
        if meta_child.tag == "gameVersion":
            game_version = meta_child.text
        elif meta_child.tag == "modIds":
            mod_ids = [modid_el.text for modid_el in meta_child]
        elif meta_child.tag == "modSteamIds":
            mod_steam_ids = [modsteam_el.text for modsteam_el in meta_child]
        elif meta_child.tag == "modNames":
            mod_names = [modname.text for modname in meta_child]
        else:
            logger.debug(f"Skipping child: {meta_child.tag}")
    assert game_version is not None
    assert len(mod_ids) == len(mod_steam_ids)
    assert len(mod_ids) == len(mod_names)
    result = []
    for mod_id, mod_steam, mod_name in zip(
        mod_ids,
        mod_steam_ids,
        mod_names,
    ):
        mod_id = cast(str, mod_id)
        mod_steam = cast(str, mod_steam)
        mod_name = cast(str, mod_name)
        result.append(
            ModFromSave(
                mod_id=mod_id,
                mod_steam_id=mod_steam,
                mod_name=mod_name,
            )
        )
    logger.info(f"Game version from save is {game_version}")
    logger.info(f"Loaded {len(result)} mods from save")
    return game_version, result


def mods_to_modlist(game_version: str, mods: list[ModFromSave], output_path: Path):
    """
    Write a RimWorld mod list file to a designated location.

    :param game_version:
        string with the game version
    :param mods:
        the list of mods to write to
    :param output_path:
        the path to write the rml file at
    """
    base_doc = ET.Element("savedModList")
    meta_li = ET.SubElement(base_doc, "meta")
    game_version_node = ET.SubElement(meta_li, "gameVersion")
    game_version_node.text = game_version
    modIds_node = ET.SubElement(meta_li, "modIds")
    modSteamIds_node = ET.SubElement(meta_li, "modSteamIds")
    modNames_node = ET.SubElement(meta_li, "modNames")
    modList_node = ET.SubElement(base_doc, "modList")
    modList_ids_node = ET.SubElement(modList_node, "ids")
    modList_names_node = ET.SubElement(modList_node, "names")
    for mod_item in mods:
        ET.SubElement(modIds_node, "li").text = mod_item.mod_id
        ET.SubElement(modSteamIds_node, "li").text = mod_item.mod_steam_id
        ET.SubElement(modNames_node, "li").text = mod_item.mod_name
        ET.SubElement(modList_ids_node, "li").text = mod_item.mod_id
        ET.SubElement(modList_names_node, "li").text = mod_item.mod_name
    logger.info(f"Writing modlist to {output_path}")
    ET.ElementTree(base_doc).write(
        output_path,
        xml_declaration=True,
        encoding="utf-8",
    )


def main():
    """Entrypoint function."""
    game_version, mod_list = extract_mod_from_save(INPUT_SAVE_PATH)
    mods_to_modlist(game_version, mod_list, OUTPUT_MODLIST_PATH)

    mod_ids = [mod.mod_id for mod in mod_list]
    sorted_mod_ids = sorted(mod_ids)
    with open("mod_ids.txt", "w") as f:
        for mod_id in sorted_mod_ids:
            f.write(mod_id + "\n")


if __name__ == "__main__":
    main()
