"""NMIT AC-NMIT-06 course grade estimates from recorded assessment marks."""

GRADE_BANDS = (
    (85, 'A+', 'Pass with Distinction'),
    (80, 'A', 'Pass with Distinction'),
    (75, 'A-', 'Pass with Distinction'),
    (70, 'B+', 'Pass with Merit'),
    (65, 'B', 'Pass with Merit'),
    (60, 'B-', 'Pass with Merit'),
    (55, 'C+', 'Pass'),
    (50, 'C', 'Pass'),
    (40, 'D', 'Fail'),
    (0, 'E', 'Fail'),
)


def letter_grade(percentage):
    """Use exact unrounded percentage to avoid incorrectly crossing a band."""
    if percentage is None:
        return None
    if not 0 <= percentage <= 100:
        raise ValueError('Grade percentage must be between 0 and 100')
    for minimum, letter, classification in GRADE_BANDS:
        if percentage >= minimum:
            return letter, classification


def course_estimate(assignments):
    """Summarise graded weight without treating missing grades as zero."""
    rows = list(assignments)
    graded = [r for r in rows if r['grade'] is not None and r['weight'] > 0]
    graded_weight = sum(r['weight'] for r in graded)
    points = sum(r['weight'] * r['grade'] / 100 for r in graded)
    total_weight = sum(r['weight'] for r in rows)
    average = points / graded_weight * 100 if graded_weight else None
    return {'average': average, 'band': letter_grade(average),
            'graded_weight': graded_weight, 'points': points,
            'total_weight': total_weight, 'remaining_weight': max(0, total_weight-graded_weight)}
