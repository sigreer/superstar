from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from tasktool.model import (
    Project, Phase, Slice, Task, CrossCutting, BlockedOn, Status, PlanningStatus,
    SliceWorkflowStep, PhaseWorkflowStep, ReviewStage,
)
from tasktool.serialize import (
    load_project, save_project, dumps_canonical, loads_project, to_dict, from_dict,
)

class RoundTripTests(unittest.TestCase):
    def test_empty_project_roundtrip(self):
        p = Project(project="demo")
        d = to_dict(p)
        back = from_dict(d)
        self.assertEqual(back, p)

    def test_full_project_roundtrip(self):
        p = Project(project="demo", north_star="x", last_reviewed="2026-05-17")
        ph = Phase(
            id="P1", title="phase", created="2026-05-17",
            status=Status.IN_PROGRESS,
            planning_path="docs/specs/2026-05-17-p1-phase-plan.md",
        )
        s = Slice(
            id="S1", title="slice", created="2026-05-17", status=Status.BLOCKED,
            blocked_on=BlockedOn(kind="id", value="P1.S2"),
            depends_on=["P1.S2"],
            planning_status=PlanningStatus.RATIFIED,
            parallel_group="bootstrap",
            refs=["a.md", "b.md"],
        )
        s.tasks.append(Task(id="T1", title="task", created="2026-05-17"))
        ph.slices.append(s)
        p.phases.append(ph)
        p.cross_cutting.append(CrossCutting(id="X1", title="x", created="2026-05-17"))

        back = from_dict(to_dict(p))
        self.assertEqual(back, p)

class CanonicalFormatTests(unittest.TestCase):
    def test_dumps_sorted_keys(self):
        p = Project(project="demo")
        out = dumps_canonical(p)
        parsed = json.loads(out)
        self.assertEqual(parsed["project"], "demo")
        keys = list(parsed.keys())
        self.assertEqual(keys, sorted(keys))

    def test_dumps_trailing_newline(self):
        out = dumps_canonical(Project(project="demo"))
        self.assertTrue(out.endswith("\n"))

    def test_dumps_indent_two(self):
        out = dumps_canonical(Project(project="demo"))
        self.assertIn("\n  ", out)

class DiskIOTests(unittest.TestCase):
    def test_save_then_load(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "tasklist.json"
            p = Project(project="demo")
            save_project(p, path)
            loaded = load_project(path)
            self.assertEqual(loaded, p)

    def test_save_is_canonical_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "tasklist.json"
            p = Project(project="demo")
            save_project(p, path)
            on_disk = path.read_text(encoding="utf-8")
            self.assertEqual(on_disk, dumps_canonical(p))

def test_started_field_round_trips_on_slice():
    text = """{
      "project": "demo",
      "schema_version": 1,
      "phases": [{
        "id": "P1",
        "title": "Phase",
        "created": "2026-05-19",
        "slices": [{
          "id": "S1",
          "title": "Slice",
          "created": "2026-05-19",
          "started": "2026-05-19"
        }]
      }]
    }"""
    p = loads_project(text)
    assert p.phases[0].slices[0].started == "2026-05-19"
    assert '"started": "2026-05-19"' in dumps_canonical(p)


def test_legacy_tasklist_without_archived_cross_cutting_loads():
    project = loads_project(
        json.dumps(
            {
                "project": "demo",
                "schema_version": 1,
                "phases": [],
                "cross_cutting": [],
                "archived_phases": [],
            }
        )
    )

    assert project.archived_cross_cutting == []


def test_slice_worktree_fields_round_trip():
    from tasktool.serialize import from_dict, to_dict
    raw = {
        "project": "demo",
        "schema_version": 1,
        "phases": [{
            "id": "P1", "title": "P", "created": "2026-05-21", "status": "ready",
            "slices": [{
                "id": "S1", "title": "S", "created": "2026-05-21", "status": "ready",
                "worktree_path": ".worktrees/worktree-p1-s1-s",
                "worktree_branch": "worktree-p1-s1-s",
                "worktree_in_place": False,
                "worktree_pruned_at": None,
                "worktree_prune_pending": False,
                "worktree_prune_pending_at": None,
            }],
        }],
        "cross_cutting": [],
        "archived_phases": [],
        "archived_cross_cutting": [],
    }
    p = from_dict(raw)
    out = to_dict(p)
    s = out["phases"][0]["slices"][0]
    assert s["worktree_path"] == ".worktrees/worktree-p1-s1-s"
    assert s["worktree_branch"] == "worktree-p1-s1-s"
    # Default-valued worktree_in_place (False) is omitted from serialised form
    # so historical rows do not gain new keys on round-trip.
    assert "worktree_in_place" not in s


def test_slice_worktree_fields_default_null_when_absent():
    from tasktool.serialize import from_dict, to_dict
    raw = {
        "project": "demo", "schema_version": 1,
        "phases": [{
            "id": "P1", "title": "P", "created": "2026-05-21", "status": "ready",
            "slices": [{"id": "S1", "title": "S", "created": "2026-05-21", "status": "ready"}],
        }],
        "cross_cutting": [], "archived_phases": [], "archived_cross_cutting": [],
    }
    p = from_dict(raw)
    s = p.phases[0].slices[0]
    assert s.worktree_path is None
    assert s.worktree_branch is None
    assert s.worktree_in_place is False
    assert s.worktree_pruned_at is None
    assert s.worktree_prune_pending is False
    assert s.worktree_prune_pending_at is None


def test_slice_without_worktree_fields_emits_no_worktree_keys():
    """Historical rows that never set worktree_* fields must round-trip without
    gaining those keys. Defaults must be omitted on serialise."""
    from tasktool.serialize import from_dict, to_dict
    raw = {
        "project": "demo", "schema_version": 1,
        "phases": [{
            "id": "P1", "title": "P", "created": "2026-05-21", "status": "ready",
            "slices": [{"id": "S1", "title": "S", "created": "2026-05-21", "status": "ready"}],
        }],
        "cross_cutting": [], "archived_phases": [], "archived_cross_cutting": [],
    }
    p = from_dict(raw)
    out = to_dict(p)
    s = out["phases"][0]["slices"][0]
    for key in (
        "worktree_path", "worktree_branch", "worktree_in_place",
        "worktree_pruned_at", "worktree_prune_pending", "worktree_prune_pending_at",
    ):
        assert key not in s, f"unexpected default key {key!r} in serialised slice"


def test_cross_without_worktree_fields_emits_no_worktree_keys():
    from tasktool.serialize import from_dict, to_dict
    raw = {
        "project": "demo", "schema_version": 1,
        "phases": [],
        "cross_cutting": [{
            "id": "X9", "title": "x", "created": "2026-05-21", "status": "ready",
        }],
        "archived_phases": [], "archived_cross_cutting": [],
    }
    p = from_dict(raw)
    out = to_dict(p)
    c = out["cross_cutting"][0]
    for key in (
        "worktree_path", "worktree_branch", "worktree_in_place",
        "worktree_pruned_at", "worktree_prune_pending", "worktree_prune_pending_at",
    ):
        assert key not in c


def test_slice_non_default_worktree_fields_are_preserved():
    from tasktool.serialize import from_dict, to_dict
    raw = {
        "project": "demo", "schema_version": 1,
        "phases": [{
            "id": "P1", "title": "P", "created": "2026-05-21", "status": "ready",
            "slices": [{
                "id": "S1", "title": "S", "created": "2026-05-21", "status": "ready",
                "worktree_in_place": True,
            }],
        }],
        "cross_cutting": [], "archived_phases": [], "archived_cross_cutting": [],
    }
    p = from_dict(raw)
    out = to_dict(p)
    s = out["phases"][0]["slices"][0]
    assert s["worktree_in_place"] is True
    # The other defaults must still be omitted.
    assert "worktree_path" not in s
    assert "worktree_branch" not in s


def test_cross_worktree_fields_round_trip():
    from tasktool.serialize import from_dict, to_dict
    raw = {
        "project": "demo", "schema_version": 1,
        "phases": [],
        "cross_cutting": [{
            "id": "X9", "title": "x", "created": "2026-05-21", "status": "ready",
            "worktree_path": ".worktrees/worktree-x9-x",
            "worktree_branch": "worktree-x9-x",
            "worktree_in_place": False,
            "worktree_pruned_at": None,
            "worktree_prune_pending": False,
            "worktree_prune_pending_at": None,
        }],
        "archived_phases": [], "archived_cross_cutting": [],
    }
    p = from_dict(raw)
    out = to_dict(p)
    assert out["cross_cutting"][0]["worktree_path"] == ".worktrees/worktree-x9-x"


def test_serialize_audit_fields_round_trip(tmp_path):
    from tasktool.model import Project, Phase, Slice
    from tasktool.serialize import save_project, load_project
    p = Project(project="demo")
    ph = Phase(id="P5", title="t", created="2026-05-21")
    s = Slice(id="S2", title="t", created="2026-05-21",
              worktree_pruned_at="2026-05-22",
              worktree_prune_pending=True,
              worktree_prune_pending_at="2026-05-22")
    ph.slices.append(s)
    p.phases.append(ph)
    path = tmp_path / "tasklist.json"
    save_project(p, path)
    p2 = load_project(path)
    s2 = p2.phases[0].slices[0]
    assert s2.worktree_pruned_at == "2026-05-22"
    assert s2.worktree_prune_pending is True
    assert s2.worktree_prune_pending_at == "2026-05-22"


def test_serialize_cross_audit_fields_round_trip(tmp_path):
    from tasktool.model import Project, CrossCutting
    from tasktool.serialize import save_project, load_project
    p = Project(project="demo")
    c = CrossCutting(id="X1", title="t", created="2026-05-21",
                     worktree_pruned_at="2026-05-22",
                     worktree_prune_pending=True,
                     worktree_prune_pending_at="2026-05-22")
    p.cross_cutting.append(c)
    path = tmp_path / "tasklist.json"
    save_project(p, path)
    p2 = load_project(path)
    c2 = p2.cross_cutting[0]
    assert c2.worktree_pruned_at == "2026-05-22"
    assert c2.worktree_prune_pending is True
    assert c2.worktree_prune_pending_at == "2026-05-22"


def _round_trip(p: Project) -> Project:
    return from_dict(to_dict(p))


def test_workflow_step_round_trip_slice():
    s = Slice(id="S1", title="t", created="2026-05-23",
              workflow_step=SliceWorkflowStep.PLAN)
    ph = Phase(id="P6", title="t", created="2026-05-23", slices=[s])
    p = Project(project="x", phases=[ph])
    rt = _round_trip(p)
    assert rt.phases[0].slices[0].workflow_step is SliceWorkflowStep.PLAN


def test_workflow_step_round_trip_phase():
    ph = Phase(id="P6", title="t", created="2026-05-23",
               workflow_step=PhaseWorkflowStep.IN_PROGRESS)
    p = Project(project="x", phases=[ph])
    rt = _round_trip(p)
    assert rt.phases[0].workflow_step is PhaseWorkflowStep.IN_PROGRESS


def test_review_fields_round_trip():
    s = Slice(id="S1", title="t", created="2026-05-23",
              review_active=True, review_stage=ReviewStage.APPLYING_FIXES)
    ph = Phase(id="P6", title="t", created="2026-05-23", slices=[s])
    p = Project(project="x", phases=[ph])
    rt = _round_trip(p)
    assert rt.phases[0].slices[0].review_active is True
    assert rt.phases[0].slices[0].review_stage is ReviewStage.APPLYING_FIXES


def test_workflow_step_default_none_omitted_from_json():
    s = Slice(id="S1", title="t", created="2026-05-23")
    ph = Phase(id="P6", title="t", created="2026-05-23", slices=[s])
    p = Project(project="x", phases=[ph])
    raw = to_dict(p)
    s_dict = raw["phases"][0]["slices"][0]
    assert "workflow_step" not in s_dict
    assert "review_active" not in s_dict
    assert "review_stage" not in s_dict
    assert "workflow_step" not in raw["phases"][0]


def test_review_active_false_omitted_even_with_stage_explicit():
    s = Slice(id="S1", title="t", created="2026-05-23",
              review_active=False, review_stage=None)
    ph = Phase(id="P6", title="t", created="2026-05-23", slices=[s])
    raw = to_dict(Project(project="x", phases=[ph]))
    assert "review_active" not in raw["phases"][0]["slices"][0]
    assert "review_stage" not in raw["phases"][0]["slices"][0]


def test_legacy_row_without_workflow_fields_loads_clean():
    raw = {
        "project": "x",
        "schema_version": 1,
        "phases": [{
            "id": "P1", "title": "t", "created": "2026-05-01", "slices": [
                {"id": "S1", "title": "t", "created": "2026-05-01"}
            ]
        }],
        "cross_cutting": [],
        "archived_phases": [],
        "archived_cross_cutting": [],
    }
    p = from_dict(raw)
    assert p.phases[0].workflow_step is None
    assert p.phases[0].slices[0].workflow_step is None
    assert p.phases[0].slices[0].review_active is False
    assert p.phases[0].slices[0].review_stage is None


class P7OmitWhenDefaultTests(unittest.TestCase):
    def test_default_slice_omits_new_keys(self):
        p = Project(project="demo")
        ph = Phase(id="P1", title="phase", created="2026-06-02")
        ph.slices.append(Slice(id="S1", title="slice", created="2026-06-02"))
        p.phases.append(ph)
        out = to_dict(p)
        slc = out["phases"][0]["slices"][0]
        for key in (
            "integration_surfaces", "reservations", "coordination_group",
            "worktree_base_sha", "landed_base_sha",
        ):
            self.assertNotIn(key, slc, f"{key} should be omitted when default")

    def test_default_project_omits_reservations_ledger(self):
        p = Project(project="demo")
        out = to_dict(p)
        self.assertNotIn("reservations_ledger", out)

    def test_schema_version_serialized_as_3(self):
        p = Project(project="demo")
        out = to_dict(p)
        self.assertEqual(out["schema_version"], 3)

    def test_non_default_slice_keys_are_kept(self):
        from tasktool.model import Reservation
        p = Project(project="demo")
        ph = Phase(id="P1", title="phase", created="2026-06-02")
        s = Slice(
            id="S1", title="slice", created="2026-06-02",
            integration_surfaces=["cms-block-registry"],
            reservations=[Reservation(
                resource="homepage-sort", value="15", scope="phase",
                note="hero slot",
            )],
            coordination_group="cms",
            worktree_base_sha="abc123",
            landed_base_sha="def456",
        )
        ph.slices.append(s)
        p.phases.append(ph)
        slc = to_dict(p)["phases"][0]["slices"][0]
        self.assertEqual(slc["integration_surfaces"], ["cms-block-registry"])
        self.assertEqual(slc["reservations"], [{
            "resource": "homepage-sort", "value": "15",
            "scope": "phase", "note": "hero slot",
        }])
        self.assertEqual(slc["coordination_group"], "cms")
        self.assertEqual(slc["worktree_base_sha"], "abc123")
        self.assertEqual(slc["landed_base_sha"], "def456")

    def test_non_default_reservations_ledger_is_kept(self):
        from tasktool.model import LedgerReservation
        p = Project(project="demo")
        p.reservations_ledger.append(LedgerReservation(
            resource="route-slug", value="/offers", scope="project",
            note=None, owner_id="P20.S3", owner_phase_id="P20",
            archived_date="2026-06-02",
        ))
        out = to_dict(p)
        self.assertEqual(out["reservations_ledger"], [{
            "resource": "route-slug", "value": "/offers", "scope": "project",
            "note": None, "owner_id": "P20.S3", "owner_phase_id": "P20",
            "archived_date": "2026-06-02",
        }])


class P7DeserializeTests(unittest.TestCase):
    def test_missing_keys_default_on_deserialize(self):
        # A row with none of the new keys (the v1/v2 historical shape).
        raw = {
            "project": "demo", "schema_version": 3,
            "phases": [{
                "id": "P1", "title": "t", "created": "2026-06-02", "status": "ready",
                "slices": [{
                    "id": "S1", "title": "t", "created": "2026-06-02",
                    "status": "ready",
                }],
            }],
            "cross_cutting": [], "archived_phases": [], "archived_cross_cutting": [],
        }
        p = from_dict(raw)
        s = p.phases[0].slices[0]
        self.assertEqual(s.integration_surfaces, [])
        self.assertEqual(s.reservations, [])
        self.assertIsNone(s.coordination_group)
        self.assertIsNone(s.worktree_base_sha)
        self.assertIsNone(s.landed_base_sha)
        self.assertEqual(p.reservations_ledger, [])

    def test_present_keys_deserialize_to_objects(self):
        from tasktool.model import Reservation, LedgerReservation
        raw = {
            "project": "demo", "schema_version": 3,
            "phases": [{
                "id": "P1", "title": "t", "created": "2026-06-02", "status": "ready",
                "slices": [{
                    "id": "S1", "title": "t", "created": "2026-06-02",
                    "status": "ready",
                    "integration_surfaces": ["cms-block-registry", "theme-tail-css"],
                    "reservations": [
                        {"resource": "homepage-sort", "value": "15",
                         "scope": "phase", "note": "hero"},
                        {"resource": "route-slug", "value": "/offers",
                         "scope": "project", "note": None},
                    ],
                    "coordination_group": "cms",
                    "worktree_base_sha": "abc123",
                    "landed_base_sha": "def456",
                }],
            }],
            "cross_cutting": [], "archived_phases": [], "archived_cross_cutting": [],
            "reservations_ledger": [
                {"resource": "block-kind", "value": "slider", "scope": "project",
                 "note": None, "owner_id": "P20.S2", "owner_phase_id": "P20",
                 "archived_date": "2026-06-01"},
            ],
        }
        p = from_dict(raw)
        s = p.phases[0].slices[0]
        self.assertEqual(s.integration_surfaces, ["cms-block-registry", "theme-tail-css"])
        self.assertEqual(s.reservations[0], Reservation(
            resource="homepage-sort", value="15", scope="phase", note="hero"))
        self.assertEqual(s.reservations[1], Reservation(
            resource="route-slug", value="/offers", scope="project", note=None))
        self.assertEqual(s.coordination_group, "cms")
        self.assertEqual(s.worktree_base_sha, "abc123")
        self.assertEqual(s.landed_base_sha, "def456")
        self.assertEqual(p.reservations_ledger[0], LedgerReservation(
            resource="block-kind", value="slider", scope="project", note=None,
            owner_id="P20.S2", owner_phase_id="P20", archived_date="2026-06-01"))

    def test_full_roundtrip_with_p7_fields(self):
        from tasktool.model import Reservation, LedgerReservation
        p = Project(project="demo")
        ph = Phase(id="P1", title="phase", created="2026-06-02")
        ph.slices.append(Slice(
            id="S1", title="slice", created="2026-06-02",
            integration_surfaces=["cms-block-registry"],
            reservations=[Reservation(
                resource="homepage-sort", value="15", scope="phase", note="hero")],
            coordination_group="cms",
            worktree_base_sha="abc123",
            landed_base_sha="def456",
        ))
        p.phases.append(ph)
        p.reservations_ledger.append(LedgerReservation(
            resource="block-kind", value="slider", scope="project", note=None,
            owner_id="P20.S2", owner_phase_id="P20", archived_date="2026-06-01"))
        back = from_dict(to_dict(p))
        self.assertEqual(back, p)

    def test_default_roundtrip_equality(self):
        # A wholly-default project must round-trip to an equal object even
        # though the new keys are omitted on serialize.
        p = Project(project="demo")
        ph = Phase(id="P1", title="phase", created="2026-06-02")
        ph.slices.append(Slice(id="S1", title="slice", created="2026-06-02"))
        p.phases.append(ph)
        back = from_dict(to_dict(p))
        self.assertEqual(back, p)
