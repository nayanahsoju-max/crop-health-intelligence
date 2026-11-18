from crop_health.knowledge_base.service import KnowledgeBase

ALL_CLASSES = (
    "tomato_healthy", "tomato_bacterial_spot", "tomato_early_blight",
    "tomato_late_blight", "potato_healthy", "potato_early_blight",
    "potato_late_blight", "grape_black_rot", "grape_esca",
    "grape_isariopsis_leaf_blight",
)

GRAPE_CLASSES = (
    "grape_black_rot", "grape_esca", "grape_isariopsis_leaf_blight",
)


def test_selected_classes_have_source_backed_entries():
    kb = KnowledgeBase()
    for disease_id in ALL_CLASSES:
        entry = kb.require(disease_id)
        assert entry["sources"]
        assert all(source["url"].startswith("https://") for source in entry["sources"])
        assert all(source["organization"] for source in entry["sources"])
        assert all(source["title"] for source in entry["sources"])


def test_all_ten_classes_present_and_structured():
    kb = KnowledgeBase()
    all_entries = kb.all()
    assert len(all_entries) == 10
    entry_ids = {e["id"] for e in all_entries}
    assert entry_ids == set(ALL_CLASSES)
    for entry in all_entries:
        assert entry["id"]
        assert entry["crop"] in {"Tomato", "Potato", "Grape"}
        assert entry["disease_name"]
        assert entry["condition_type"] in {"disease", "status"}
        assert entry["description"]
        assert isinstance(entry["symptoms"], list)
        assert isinstance(entry["prevention"], list)
        assert isinstance(entry["general_management"], list)
        assert isinstance(entry["sources"], list) and len(entry["sources"]) >= 1


def test_grape_specific_records_and_symptoms():
    kb = KnowledgeBase()
    for gid in GRAPE_CLASSES:
        entry = kb.require(gid)
        assert entry["crop"] == "Grape"
        assert entry["condition_type"] == "disease"
        assert len(entry["symptoms"]) >= 3
        assert len(entry["prevention"]) >= 2
        assert len(entry["general_management"]) >= 2

    # Black rot specifics
    black_rot = kb.require("grape_black_rot")
    assert "Guignardia bidwellii" in black_rot["description"]
    assert any("pycnidia" in s.lower() for s in black_rot["symptoms"])
    assert any("mummies" in s.lower() for s in black_rot["symptoms"])

    # Esca specifics
    esca = kb.require("grape_esca")
    assert "trunk" in esca["description"].lower()
    assert any("tiger-stripe" in s.lower() for s in esca["symptoms"])
    assert any("measles" in s.lower() for s in esca["symptoms"])

    # Isariopsis specifics
    isariopsis = kb.require("grape_isariopsis_leaf_blight")
    assert "Pseudocercospora vitis" in isariopsis["description"]
    assert any("angular" in s.lower() for s in isariopsis["symptoms"])
    assert any("defoliation" in s.lower() for s in isariopsis["symptoms"])


def test_unknown_class_is_not_guessed():
    kb = KnowledgeBase()
    assert kb.get("unselected_crop_disease") is None


def test_healthy_record_does_not_claim_all_diseases_absent():
    entry = KnowledgeBase().require("tomato_healthy")
    assert entry["condition_type"] == "status"
    assert "does not rule out" in entry["description"]
