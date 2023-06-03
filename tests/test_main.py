import pytest
from generate_modlist_from_save import (
    prepare_output_paths,
    extract_mod_from_save,
    mods_to_modlist,
    mods_to_csv,
    process_rws_file,
    ModFromSave,
)
import xml.etree.ElementTree as ET
from pathlib import Path


SAMPLE_EXPECTED_DATA = {
    "game_version": "1.4.3704 rev898",
    "mods": {
        "number": 79,
        "first_mod": {
            "name": "Harmony",
            "id": "brrainz.harmony",
            "steam_id": "2009463077",
        }
    }
}


def get_sample_path() -> Path:
    return Path(__file__).parent / "sample.rws"


class TestExtractModFromSave:
    def test_file_not_a_xml(self, tmp_path):
        p = tmp_path / "not-a-xml"
        with open(p, "w") as f:
            f.write("this-is-not-an-xml")
        with pytest.raises(ET.ParseError):
            extract_mod_from_save(p)

    def test_file_not_following_rws_structure(self, tmp_path):
        p = tmp_path / "not-right-structure.rws"
        base_doc = ET.Element("someblock")
        ET.SubElement(base_doc, "somesubblock")
        ET.ElementTree(base_doc).write(
            p, 
            xml_declaration=True,
            encoding="utf-8",
        )
        with pytest.raises(RuntimeError):
            extract_mod_from_save(p)

    def test_different_number_ids_and_names(self, tmp_path):
        p = tmp_path / "different-number-mod-attrs.rws"
        p.write_text("""<?xml version="1.0" encoding="utf-8"?>
<savegame>
	<meta>
		<gameVersion>1.0.0 rev0</gameVersion>
		<modIds>
            <li>aaa.first</li>
            <li>bbb.second</li>
        </modIds>
        <modSteamIds>
            <li>0.0.1</li>
            <!-- missing ids --> 
        </modSteamIds>
        <modNames>
            <li>First</li>
            <li>Second</li>
        </modNames>
    </meta>
</savegame>""")
        with pytest.raises(RuntimeError):
            extract_mod_from_save(p)

    def test_extract_from_sample(self):
        sample_path = get_sample_path()
        game_version, mod_list = extract_mod_from_save(sample_path)
        assert game_version == SAMPLE_EXPECTED_DATA["game_version"]
        assert len(mod_list) == SAMPLE_EXPECTED_DATA["mods"]["number"]
        first_mod = mod_list[0]
        first_mod_data = SAMPLE_EXPECTED_DATA["mods"]["first_mod"]
        assert first_mod == ModFromSave(
            mod_id=first_mod_data["id"],
            mod_steam_id=first_mod_data["steam_id"],
            mod_name=first_mod_data["name"],
        )


class TestPrepareOutputPath:
    def test_input_path_isnt_found(self, tmp_path):
        p_in = tmp_path / "file-not-created.rws"
        d_out = tmp_path / "output_dir"
        d_out.mkdir()
        with pytest.raises(FileNotFoundError):
            prepare_output_paths(p_in, d_out)

    def test_output_path_isnt_a_dir(self, tmp_path):
        p_in = tmp_path / "file.rws"
        p_in.write_text("in")
        p_out = tmp_path / "output.txt"
        p_out.write_text("out")
        with pytest.raises(RuntimeError):
            prepare_output_paths(p_in, p_out)
        
    def test_prepare_output_paths(self, tmp_path):
        p_in = tmp_path / "file-stem.rws"
        p_in.write_text("in")
        d_out = tmp_path / "output_dir"
        d_out.mkdir()
        rml_path, csv_path = prepare_output_paths(p_in, d_out)
        assert rml_path == d_out / "file-stem.rml"
        assert csv_path == d_out / "file-stem.csv"


class TestModsToModlist:
    def test_empty_list(self, tmp_path):
        p = tmp_path / "empty_list.rwl"
        mods_to_modlist("", [], p)
        assert not p.exists()

    def test_build_from_sample(self, tmp_path):
        p = tmp_path / "output.rwl"
        sample_path = get_sample_path()
        game_version, mod_list = extract_mod_from_save(sample_path)
        mods_to_modlist(game_version, mod_list, p)
        expected_rwl_path = sample_path.parent / "sample-expected.rwl"
        expected_content = expected_rwl_path.read_text()
        assert p.read_text() == expected_content


class TestModsToCsv:
    def test_empty_list(self, tmp_path):
        p = tmp_path / "empty_list.csv"
        mods_to_csv([], p)
        assert not p.exists()

    def test_build_from_sample(self, tmp_path):
        p = tmp_path / "output.csv"
        sample_path = get_sample_path()
        _, mod_list = extract_mod_from_save(sample_path)
        mods_to_csv(mod_list, p)
        expected_csv_path = sample_path.parent / "sample-expected.csv"
        expected_content = expected_csv_path.read_text()
        assert p.read_text() == expected_content


class TestWholeScript:
    def test_on_sample(self, tmp_path):
        d_out = tmp_path / "output_dir"
        d_out.mkdir()
        input_path = get_sample_path()
        output_rml, output_csv = prepare_output_paths(input_path, d_out)
        process_rws_file(input_path, output_rml, output_csv)
        expected_rml = (input_path.parent / "sample-expected.rwl").read_text()
        expected_csv = (input_path.parent / "sample-expected.csv").read_text()
        assert output_rml.read_text() == expected_rml
        assert output_csv.read_text() == expected_csv
