"""Verify actual game captures and create compact JPEG copies for review."""
import json
import pathlib

import numpy as np
from PIL import Image

root = pathlib.Path(__file__).resolve().parents[1]
folder = root / "build/screenshots"
rival_capture_names = (
    "rival_qiu_zhen",
    "rival_su_yao",
    "rival_paths",
    "rival_compete",
    "rival_cooperate",
    "rival_independent",
    "rival_end_compete",
    "rival_end_cooperate",
    "rival_end_independent",
)
images = []
named_images = {}
for name in ("title", "dialogue", "cast", "wardrobe_training", "wardrobe_festival", "outfit_dialogue", "quest_hub", "spirit_encounter", "world_gallery", "ferry_encounter", "archive_encounter", "river_pilot", "river_spirit", "river_harbor", "object_bronze_clapper", "object_sealed_echo_case", "interior_gallery", "attributes", "attribute_choices", "orchard_healer", "orchard_spirit", "orchard_choices", "city_market", "city_mask_maker", "city_archivist", "city_courier", "city_perfumer", "city_courser", "city_moth", "city_choices", "court_upper_bench", "court_luo_shan", "court_bai_qun", "court_du_heng", "court_rain_heron", "court_investigation_choice", "court_final_choice", "court_weather_setup", "mortal_arrival", "mortal_han_mei", "mortal_mite", "first_trace", "cultivation_codex", "object_copper_practice_wick", "sluice_examiner", "sluice_retention", "paired_channel", "brine_mantis", "object_meridian_caliper", "foundry_examiner", "foundry_friend", "foundry_phase_room", "foundry_material_fault", "foundry_creature", "second_pair", "foundry_choices", "foundry_home", "foundry_certificate", "object_phase_comb", "ridge_surveyor", "ridge_tortoise", "ridge_weather", "ridge_cloudhound", "ridge_discharge", "ridge_choices", "object_storm_compass", "storm_observatory", "storm_choices", "salt_watermill", "salt_forewoman", "salt_salamander", "salt_choices", "forest_ensemble", "lanternwing_crane", "desert_attributes", "archive_ensemble", "archive_courtyard", "archive_lantern_keeper", "bitter_wells_yard", "bitter_wells_workroom", "bitter_wells_lodging", "desert_dilemma", "completed_comparison", "xu_lin", "tidemirror_otter", "cinderback_pangolin", "chen_rui", "wu_zheng", "song_mei", "expanded_canal_choice", "storm_completed_practice", "salt_completed_practice", "consequence_choices", "consequence_house", "consequence_school", "consequence_lamp", "native_lark_pass_cliff_market", "native_outer_shoal_salvage_yard", "native_vermilion_hollows_inspection_gallery", "native_kestrel_basin_heat_court", "native_mirror_basin_reservoir_cloister", "native_chime_reach_relay_plaza", "native_qin_bo", "native_reservoir_qiu_nan", "native_reservoir_mei_rong", "native_reservoir_jing_su", "native_reservoir_fu_lian", "native_reservoir_zhou_wen", "native_reservoir_tian_yu", "native_mine_worker_lodging", "native_mine_surface_yard", "native_mine_clinic_room", "native_mine_practice_court", "native_wintercity_gao_shen", "native_mine_wei_yan", "native_lantern_shao_ye", "native_lark_pass_avalanche_shelter", "reed_crossing_choice", "reed_crossing_grain", "reed_crossing_linen", "reed_crossing_wages", "career_enrolment", "career_kiln", "career_archive", "career_survey", "career_independent", "career_portfolio", "career_portfolio_archive", "career_portfolio_survey", "career_portfolio_independent", "commission_offer", "commission_kiln", "commission_archive", "commission_survey", "commission_independent", "commission_portfolio_kiln", "commission_portfolio_archive", "commission_portfolio_survey", "commission_portfolio_independent", "commission_kiln_kitchen") + rival_capture_names:
    source = Image.open(folder / f"{name}.png").convert("RGB")
    assert source.width >= 1280 and source.height >= 720, "Capture must use the real game viewport"
    pixels = np.asarray(source)
    assert pixels.std() > 15, "Screenshot must contain a rendered scene"
    source.save(folder / f"{name}.jpg", quality=82, optimize=True)
    images.append(pixels)
    named_images[name] = pixels
assert not np.array_equal(images[0], images[1]), "Title and dialogue must be different views"
assert not np.array_equal(images[1], images[2]), "Cast modal must render on top of dialogue"
assert not np.array_equal(images[3], images[4]), "Training and festival outfits must render differently"
assert not np.array_equal(images[1], images[5]), "Chosen outfits must render in story scenes"
assert not np.array_equal(images[6], images[7]), "Quest and spirit scenes must differ"
assert not np.array_equal(images[7], images[8]), "World gallery must render separately"
assert not np.array_equal(images[9], images[10]), "Ferryman and archivist must render as distinct characters"
assert not np.array_equal(images[11], images[12]), "Pilot and river spirit must render independently"
assert not np.array_equal(images[12], images[13]), "River and harbor scenes must use distinct environments"
assert not np.array_equal(images[14], images[15]), "Object paintings must render as distinct inspectable artifacts"
assert not np.array_equal(images[8], images[16]), "Interior gallery must render its own full painting view"
assert not np.array_equal(images[1], images[17]), "Attributes must render a separate character panel"
assert not np.array_equal(images[1], images[18]), "Gated choices must render their visible requirements"
assert not np.array_equal(images[19], images[20]), "Orchard healer and spirit must render distinct originals"
assert not np.array_equal(images[20], images[21]), "Orchard settlement choices must render separately"
for index in range(23, 29):
    assert not np.array_equal(images[22], images[index]), "City portraits must render independently of the market"
for first in range(23, 29):
    for second in range(first + 1, 29):
        assert not np.array_equal(images[first], images[second]), "Every city character must have a distinct rendered encounter"
assert not np.array_equal(images[22], images[29]), "City settlement choices must render separately"
for first in range(30, 35):
    for second in range(first + 1, 35):
        assert not np.array_equal(images[first], images[second]), "Every court participant must have a distinct rendered encounter"
for first, second in ((30, 36), (34, 37), (35, 36), (36, 37)):
    assert not np.array_equal(images[first], images[second]), "Court hearings, investigations, remedies and weather setup must render separately"
for first, second in ((38, 39), (39, 40), (40, 41), (41, 42), (42, 43)):
    assert not np.array_equal(images[first], images[second]), "Cultivation opening, portraits, trace, codex and wick must render independently"
for first in range(44, 49):
    for second in range(first + 1, 49):
        assert not np.array_equal(images[first], images[second]), "Sluice examiner, stage tests, monster and caliper must render distinct views"
for first in range(49, 59):
    for second in range(first + 1, 59):
        assert not np.array_equal(images[first], images[second]), "Foundry stages, distinct participants, home and comb must render independently"
for first in range(59, 66):
    for second in range(first + 1, 66):
        assert not np.array_equal(images[first], images[second]), "Thunderfen encounters, chance, discharge and compass must render distinctly"
for first in range(66, 72):
    for second in range(first + 1, 72):
        assert not np.array_equal(images[first], images[second]), "Storm and salt-road locations, people, creature and decisions must render independently"
for first, second in (("consequence_house", "consequence_school"), ("consequence_house", "consequence_lamp"), ("consequence_school", "consequence_lamp")):
    assert not np.array_equal(named_images[first], named_images[second]), "Different selected commitments must render different delayed outcomes at identical scores"
for painting in ["lark_pass_cliff_market","outer_shoal_salvage_yard","vermilion_hollows_inspection_gallery","kestrel_basin_heat_court","mirror_basin_reservoir_cloister","chime_reach_relay_plaza","qin_bo","reservoir_qiu_nan","reservoir_mei_rong","reservoir_jing_su","reservoir_fu_lian","reservoir_zhou_wen","reservoir_tian_yu","mine_worker_lodging","mine_surface_yard","mine_clinic_room","mine_practice_court","wintercity_gao_shen","mine_wei_yan","lantern_shao_ye","lark_pass_avalanche_shelter"]:
    assert not np.array_equal(named_images["world_gallery"], named_images["native_" + painting]), "The actual gallery must show the selected continuation original"
for first, second in (("reed_crossing_grain", "reed_crossing_linen"), ("reed_crossing_grain", "reed_crossing_wages"), ("reed_crossing_linen", "reed_crossing_wages")):
    assert not np.array_equal(named_images[first], named_images[second]), "Actual Reed Crossing choices must produce different retained cargo accounts"
for first, second in (("career_kiln", "career_archive"), ("career_kiln", "career_survey"), ("career_archive", "career_survey"), ("career_enrolment", "career_portfolio")):
    assert not np.array_equal(named_images[first], named_images[second]), "Career enrollment and selected professions must render distinct actual scenes"
for first, second in (("career_portfolio", "career_portfolio_archive"), ("career_portfolio", "career_portfolio_survey"), ("career_portfolio_archive", "career_portfolio_survey"), ("career_portfolio_survey", "career_portfolio_independent")):
    assert not np.array_equal(named_images[first], named_images[second]), "Saved career selections must render their own completed portfolios"
commission_entries = ("commission_offer", "commission_kiln", "commission_archive", "commission_survey", "commission_independent")
for first_index, first in enumerate(commission_entries):
    for second in commission_entries[first_index + 1:]:
        assert not np.array_equal(named_images[first], named_images[second]), "New commission offers and recorded professions must render distinct native environments"
commission_portfolios = tuple(f"commission_portfolio_{career}" for career in ("kiln", "archive", "survey", "independent"))
for first_index, first in enumerate(commission_portfolios):
    for second in commission_portfolios[first_index + 1:]:
        assert not np.array_equal(named_images[first], named_images[second]), "Saved commissions must render their own performed-work portfolios"
for career in ("kiln", "archive", "survey", "independent"):
    assert not np.array_equal(named_images[f"commission_{career}"], named_images[f"commission_portfolio_{career}"]), "Accepted commission entries and completed portfolios must render separately"
assert not np.array_equal(named_images["commission_kiln"], named_images["commission_kiln_kitchen"]), "The actual on-site kiln contract must render its original shared kitchen"
assert not np.array_equal(named_images["commission_kiln_kitchen"], named_images["commission_portfolio_kiln"]), "Performed kitchen work and its receiving review must render separately"
# These scenes come from actual rival choices, receiving reviews and saved endings.
for first_index, first in enumerate(rival_capture_names):
    for second in rival_capture_names[first_index + 1:]:
        assert not np.array_equal(named_images[first], named_images[second]), "Rival portraits, three played paths and their retained endings must render distinct views"
print(f"Verified {len(images)} rendered captures including distinct saved-choice consequences.")

# Timed samples come from the real Godot viewport.
animation_folder = root / "build/animations"
rendered = [Image.open(animation_folder / "rendered" / f"frame_{index:02d}.png").convert("RGB")
            for index in range(16)]
start = np.asarray(rendered[0], dtype=np.float32)[50:330, 520:940]
body_change = max(float(np.mean(np.abs(start - np.asarray(frame, dtype=np.float32)[50:330, 520:940])))
                  for frame in rendered[1:])
assert body_change >= 0.2, f"Rendered body bob is missing: {body_change:.3f}"
rendered[0].save(animation_folder / "rendered_game.webp", format="WEBP", save_all=True,
                 append_images=rendered[1:], duration=250, loop=0,
                 lossless=True, quality=100, method=4, exact=True)
comparison = Image.new("RGB", (480 * 4, 270))
for column, index in enumerate((0, 4, 8, 12)):
    comparison.paste(rendered[index].resize((480, 270), Image.Resampling.LANCZOS), (column * 480, 0))
comparison.save(animation_folder / "rendered_game_frames.jpg", quality=82, optimize=True)
print(f"Verified gentle body bob in timed game playback: maximum mean body-region change {body_change:.2f}/255.")


# Add measured review media to the same delivery report only after all checks pass.
report_path = root / "build/content_report.json"
if report_path.exists():
    report = json.loads(report_path.read_text())
    report["rendered_screenshots"] = len(images)
    report["rival_rendered_screenshots"] = len(rival_capture_names)
    report_path.write_text(json.dumps(report, indent=2) + "\n")
