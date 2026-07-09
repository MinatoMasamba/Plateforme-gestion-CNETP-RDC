from apps.norms.diff_utils import build_inline_diff_segments


def test_build_inline_diff_segments_highlights_word_changes():
    old_text = "La présente norme définit le Cahier des clauses administratives générales."
    new_text = "La présente norme définit clauses administratives générales et autres clauses."

    segments = build_inline_diff_segments(old_text, new_text)

    assert any(segment['type'] == 'delete' and segment['text'] == 'le' for segment in segments)
    assert any(segment['type'] == 'insert' and segment['text'] == 'et' for segment in segments)
    assert any(segment['type'] == 'insert' and segment['text'] == 'autres' for segment in segments)
    assert any(segment['type'] == 'equal' and segment['text'] == 'La' for segment in segments)


def test_build_inline_diff_segments_preserves_paragraph_breaks():
    old_text = "Première ligne.\n\nDeuxième paragraphe."
    new_text = "Première ligne.\n\nDeuxième paragraphe modifié."

    segments = build_inline_diff_segments(old_text, new_text)

    assert any(segment['type'] == 'equal' and segment['text'] == '\n\n' for segment in segments)
    assert any(segment['type'] == 'insert' and segment['text'] == 'modifié' for segment in segments)
