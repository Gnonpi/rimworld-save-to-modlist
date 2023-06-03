"""Script allowing to extract your mod list from a RimWorld save file."""
import argparse
import csv
import dataclasses
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import cast

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

WIKI_SAVE_FILE_URL = "https://www.rimworldwiki.com/wiki/Save_file"


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
    logger.info(f"Loading mods from save file at '{input_save_path}'")
    try:
        # todo: should we use iterparse instead?
        tree = ET.parse(input_save_path)
    except ET.ParseError as ex:
        logger.error(f"Failed to parse xml save file: {ex}")
        raise ex
    root = tree.getroot()
    meta_el = [child for child in root if child.tag == "meta"]
    if len(meta_el) == 0:
        err_msg = "Couldn't find 'meta' element in rws file."
        logger.error(err_msg)
        logger.error("Check that you provided the correct path ({WIKI_SAVE_FILE_URL})")
        raise RuntimeError(err_msg)

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

    if game_version is None:
        err_msg = "Game version is empty"
        logger.error(err_msg)
        raise RuntimeError(err_msg)
    if len(mod_ids) != len(mod_steam_ids) or len(mod_ids) != len(mod_names):
        err_msg = (
            "Different number of mod ids/names/steamids "
            f"({len(mod_ids)}/{len(mod_steam_ids)}/{len(mod_names)})"
        )
        logger.error(err_msg)
        logger.error("This might indicate a problem within your save file structure")
        raise RuntimeError(err_msg)

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


def prepare_output_paths(input_path: Path, output_dir: Path) -> tuple[Path, Path]:
    """
    Get output paths for rml and csv from the input filename and output directory.

    :param input_path:
        path to the save file
    :param output_dir:
        path to the output folder
    """
    if not input_path.exists():
        err_msg = f"Cannot find save file at '{input_path}'"
        logger.error(err_msg)
        raise FileNotFoundError(input_path)
    if not output_dir.is_dir():
        err_msg = f"Output dir '{output_dir}' is not a folder"
        logger.error(err_msg)
        raise RuntimeError(err_msg)
    input_stem = input_path.stem
    output_rml = output_dir / (input_stem + ".rml")
    output_csv = output_dir / (input_stem + ".csv")
    return output_rml, output_csv


def mods_to_modlist(game_version: str, mods: list[ModFromSave], output_path: Path):
    """
    Write a RimWorld mod list file to a designated location.

    :param game_version:
        string with the game version
    :param mods:
        the list of mods to write
    :param output_path:
        the path to write the rml file at
    """
    if len(mods) == 0:
        logger.info("No mods were passed, skipping")
        return

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
    logger.info(f"Writing modlist as rml to '{output_path}'")
    ET.ElementTree(base_doc).write(
        output_path,
        xml_declaration=True,
        encoding="utf-8",
    )


def mods_to_csv(mods: list[ModFromSave], output_path: Path):
    """
    Export the mod list to a csv file.

    :param mods:
        the list of mods to write
    :param output_path:
        the path to write the rml file at
    """
    if len(mods) == 0:
        logger.info("No mods were passed, skipping")
        return

    field_names = ["mod_id", "mod_name", "mod_steam_id"]
    sorted_mods = sorted(mods, key=lambda m: m.mod_id)
    logger.info(f"Writing modlist as csv to '{output_path}'")
    with open(output_path, "w") as f:
        writer = csv.DictWriter(f, field_names, delimiter=";")
        writer.writeheader()
        for mod in sorted_mods:
            writer.writerow(dataclasses.asdict(mod))


def process_rws_file(input_path: Path, output_rml: Path, output_csv: Path):
    """
    Read the mods from input_path and write the modlist to output_rml, the csv to output_csv.

    :param input_path:
        path to the rws file to read
    :param output_rml:
        path to the rml to write to
    :param output_csv:
        path to the csv to write to
    """
    game_version, mod_list = extract_mod_from_save(input_path)
    mods_to_modlist(game_version, mod_list, output_rml)
    mods_to_csv(mod_list, output_csv)


def main():
    """Entrypoint function."""
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument("--input-path", type=Path, help="path to the rws")
    parser.add_argument("--output-dir", type=Path, help="folder where to write to")
    args = parser.parse_args()

    output_rml, output_csv = prepare_output_paths(args.input_path, args.output_dir)
    process_rws_file(args.input_path, output_rml, output_csv)


if __name__ == "__main__":
    main()
