import pytest

from tasktool.worktree_lifecycle import worktree_name


@pytest.mark.parametrize(
    "id_, title, expected",
    [
        ("P5.S1", "Tasktool worktree lifecycle core",
         "worktree-p5-s1-tasktool-worktree-lifecycle-core"),
        ("X42", "Hotfix: shim drift",
         "worktree-x42-hotfix-shim-drift"),
        ("P13.S2", "Checkout rewrite",
         "worktree-p13-s2-checkout-rewrite"),
        # Whitespace + underscore collapse
        ("P1.S1", "  Foo   bar__baz  ",
         "worktree-p1-s1-foo-bar-baz"),
        # Non-ascii / punctuation stripped
        ("P1.S1", "Café — déjà vu!",
         "worktree-p1-s1-caf-d-j-vu"),
        # Repeated dashes collapsed
        ("P1.S1", "a---b",
         "worktree-p1-s1-a-b"),
        # Slice followup letter preserved
        ("P2.S3a", "Follow up",
         "worktree-p2-s3a-follow-up"),
    ],
)
def test_worktree_name_table(id_, title, expected):
    assert worktree_name(id_, title) == expected


def test_worktree_name_truncates_long_title_at_dash_boundary():
    long_title = "alpha bravo charlie delta echo foxtrot golf hotel india juliet"
    out = worktree_name("P1.S1", long_title)
    # slug portion (after "worktree-p1-s1-") must be <= 40 chars and end on a dash boundary
    slug = out.removeprefix("worktree-p1-s1-")
    assert len(slug) <= 40
    assert not slug.endswith("-")
    # truncation must not introduce a trailing partial word
    assert out.startswith("worktree-p1-s1-alpha-bravo-charlie-delta-echo")


def test_worktree_name_empty_title_keeps_id_segment():
    # Empty/all-stripped title must still produce a stable name (no trailing dash, no collision risk)
    out = worktree_name("X9", "!!!")
    assert out == "worktree-x9"


def test_worktree_name_rejects_malformed_id():
    from tasktool.ids import IdParseError
    with pytest.raises(IdParseError):
        worktree_name("not-an-id", "title")
