"""
This module contains grading logic for Vector Drawing exercises.

It uses the following data structures:

- `vectors`: A dictionary of Vector objects.

   Keys are vector names and values represent individual vectors that were present
   on the drawing board when the student submitted an answer by clicking the 'Check' button.

- `points`: A dictionary of Point objects.

   Keys are point names and values represent individual points that were present
   on the drawing board when the student submitted an answer by clicking the 'Check' button.

- `check`: A dictionary representing a specific check.

   Contains the name of the check itself (e.g., 'presence', 'coords', 'angle'),
   the name of the element on which to perform the check, as well as
   the expected value of the property being checked.
   Optionally contains information about tolerance to apply when performing the check,
   and/or a custom error message to present to the user if the check fails.

- `answer`: A dictionary representing a specific answer submitted by a student.

   Contains three entries: vectors, points, and checks. The first two (vectors, points)
   provide information about vectors and points present on the drawing board
   when the answer was submitted. The third one (checks) specifies the checks
   to perform for individual vectors and points.

"""

# pylint: disable=invalid-name

import inspect
import logging
import math


log = logging.getLogger(__name__)  # pylint: disable=invalid-name


# Built-in check functions

def _errmsg(default_message, check, vectors):
    """
    Return error message for `check` targeting a vector from `vectors`.

    If `check` does not define a custom error message, fall back on `default_message`.
    """
    template = check.get('errmsg', default_message)
    vec = vectors[check['vector']]
    return template.format(
        name=vec.name,
        tail_x=vec.tail.x,
        tail_y=vec.tail.y,
        tip_x=vec.tip.x,
        tip_y=vec.tip.y,
        length=vec.length,
        angle=vec.angle
    )


def _errmsg_point(default_message, check, point):
    """
    Return error message for `check` targeting `point`.

    If `check` does not define a custom error message, fall back on `default_message`.
    """
    template = check.get('errmsg', default_message)
    return template.format(name=check['point'], x=point.x, y=point.y)


def check_presence(check, vectors):
    """
    Check if `vectors` contains vector targeted by `check`.
    """
    if check['vector'] not in vectors:
        errmsg = check.get('errmsg', 'You need to use the {name} vector.')
        raise ValueError(errmsg.format(name=check['vector']))


def _check_vector_endpoint(check, vectors, endpoint):
    """
    Check if `endpoint` (tail or tip) of vector targeted by `check` is in correct position.
    """
    vec = vectors[check['vector']]
    tolerance = check.get('tolerance', 1.0)
    expected = check['expected']
    verb = 'start' if endpoint == 'tail' else 'end'
    endpoint = getattr(vec, endpoint)
    dist = math.hypot(expected[0] - endpoint.x, expected[1] - endpoint.y)
    if dist > tolerance:
        raise ValueError(_errmsg(
            'Vector {name} does not {verb} at correct point.'.format(name='{name}', verb=verb),
            check,
            vectors
        ))


def check_tail(check, vectors):
    """
    Check if tail of vector targeted by `check` is in correct position.
    """
    return _check_vector_endpoint(check, vectors, endpoint='tail')


def check_tip(check, vectors):
    """
    Check if tip of vector targeted by `check` is in correct position.
    """
    return _check_vector_endpoint(check, vectors, endpoint='tip')


def _check_coordinate(check, coord):
    """
    Check `coord` against expected value.
    """
    tolerance = check.get('tolerance', 1.0)
    expected = check['expected']
    return abs(expected - coord) > tolerance


def check_tail_x(check, vectors):
    """
    Check if x position of tail of vector targeted by `check` is correct.
    """
    vec = vectors[check['vector']]
    if _check_coordinate(check, vec.tail.x):
        raise ValueError(_errmsg('Vector {name} does not start at correct point.', check, vectors))


def check_tail_y(check, vectors):
    """
    Check if y position of tail of vector targeted by `check` is correct.
    """
    vec = vectors[check['vector']]
    if _check_coordinate(check, vec.tail.y):
        raise ValueError(_errmsg('Vector {name} does not start at correct point.', check, vectors))


def check_tip_x(check, vectors):
    """
    Check if x position of tip of vector targeted by `check` is correct.
    """
    vec = vectors[check['vector']]
    if _check_coordinate(check, vec.tip.x):
        raise ValueError(_errmsg('Vector {name} does not end at correct point.', check, vectors))


def check_tip_y(check, vectors):
    """
    Check if y position of tip of vector targeted by `check` is correct.
    """
    vec = vectors[check['vector']]
    if _check_coordinate(check, vec.tip.y):
        raise ValueError(_errmsg('Vector {name} does not end at correct point.', check, vectors))


def _coord_delta(expected, actual):
    """
    Return distance between `expected` and `actual` coordinates.
    """
    if expected == '_':
        return 0
    else:
        return expected - actual


def _coords_within_tolerance(vec, expected, tolerance):
    """
    Check if distance between coordinates of `vec` and `expected` coordinates is within `tolerance`.
    """
    for expected_coords, vec_coords in ([expected[0], vec.tail], [expected[1], vec.tip]):
        delta_x = _coord_delta(expected_coords[0], vec_coords.x)
        delta_y = _coord_delta(expected_coords[1], vec_coords.y)
        if math.hypot(delta_x, delta_y) > tolerance:
            return False
    return True


def check_coords(check, vectors):
    """
    Check if coordinates of vector targeted by `check` are in correct position.
    """
    vec = vectors[check['vector']]
    expected = check['expected']
    tolerance = check.get('tolerance', 1.0)
    if not _coords_within_tolerance(vec, expected, tolerance):
        raise ValueError(_errmsg('Vector {name} coordinates are not correct.', check, vectors))


def check_segment_coords(check, vectors):
    """
    Check if coordinates of segment targeted by `check` are in correct position.
    """
    vec = vectors[check['vector']]
    expected = check['expected']
    tolerance = check.get('tolerance', 1.0)
    if not (_coords_within_tolerance(vec, expected, tolerance) or
            _coords_within_tolerance(vec.opposite(), expected, tolerance)):
        raise ValueError(_errmsg('Segment {name} coordinates are not correct.', check, vectors))


def check_length(check, vectors):
    """
    Check if length of vector targeted by `check` is correct.
    """
    vec = vectors[check['vector']]
    tolerance = check.get('tolerance', 1.0)
    if abs(vec.length - check['expected']) > tolerance:
        raise ValueError(_errmsg(
            'The length of {name} is incorrect. Your length: {length:.1f}', check, vectors
        ))


def _angle_within_tolerance(vec, expected, tolerance):
    """
    Check if difference between angle of `vec` and `expected` angle is within `tolerance`.
    """
    # Calculate angle between vec and identity vector with expected angle
    # using the formula:
    # angle = acos((A . B) / len(A)*len(B))
    x = vec.tip.x - vec.tail.x
    y = vec.tip.y - vec.tail.y
    dot_product = x * math.cos(expected) + y * math.sin(expected)
    angle = math.degrees(math.acos(dot_product / vec.length))
    return abs(angle) <= tolerance


def check_angle(check, vectors):
    """
    Check if angle of vector targeted by `check` is correct.
    """
    vec = vectors[check['vector']]
    tolerance = check.get('tolerance', 2.0)
    expected = math.radians(check['expected'])
    if not _angle_within_tolerance(vec, expected, tolerance):
        raise ValueError(
            _errmsg('The angle of {name} is incorrect. Your angle: {angle:.1f}', check, vectors)
        )


def check_segment_angle(check, vectors):
    """
    Check if angle of segment targeted by `check` is correct.
    """
    # Segments are not directed, so we must check the angle between the segment and
    # the vector that represents it, as well as its opposite vector.
    vec = vectors[check['vector']]
    tolerance = check.get('tolerance', 2.0)
    expected = math.radians(check['expected'])
    if not (_angle_within_tolerance(vec, expected, tolerance) or
            _angle_within_tolerance(vec.opposite(), expected, tolerance)):
        raise ValueError(
            _errmsg('The angle of {name} is incorrect. Your angle: {angle:.1f}', check, vectors)
        )


def _dist_line_point(line, point):
    """
    Return distance between `line` and `point`.

    The line is passed in as a Vector instance, the point as a Point instance.
    """
    direction_x = line.tip.x - line.tail.x
    direction_y = line.tip.y - line.tail.y
    determinant = (point.x - line.tail.x) * direction_y - (point.y - line.tail.y) * direction_x
    return abs(determinant) / math.hypot(direction_x, direction_y)


def check_points_on_line(check, vectors):
    """
    Check if line targeted by `check` passes through correct points.
    """
    line = vectors[check['vector']]
    tolerance = check.get('tolerance', 1.0)
    points = check['expected']
    for point in points:
        point = Point(point[0], point[1])
        if _dist_line_point(line, point) > tolerance:
            raise ValueError(_errmsg(
                'The line {name} does not pass through the correct points.', check, vectors
            ))


def check_point_coords(check, points):
    """
    Check if coordinates of point targeted by `check` are correct.
    """
    point = points[check['point']]
    tolerance = check.get('tolerance', 1.0)
    expected = check['expected']
    dist = math.hypot(expected[0] - point.x, expected[1] - point.y)
    if dist > tolerance:
        return _errmsg_point('Point {name} is not at the correct location.', check, point)


class Point(object):
    """ Represents a single point on the vector drawing board. """
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Vector(object):
    """ Represents a single vector on the vector drawing board. """
    def __init__(self, name, x1, y1, x2, y2):  # pylint: disable=too-many-arguments
        self.name = name
        self.tail = Point(x1, y1)
        self.tip = Point(x2, y2)
        self.length = math.hypot(x2 - x1, y2 - y1)
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        if angle < 0:
            angle += 360
        self.angle = angle

    def opposite(self):
        """
        Return new vector with tip and tail swapped.
        """
        return Vector(self.name, self.tip.x, self.tip.y, self.tail.x, self.tail.y)


class Grader(object):
    """
    Implements grading logic for student answers to Vector Drawing exercises.
    """
    check_registry = {
        'presence': check_presence,
        'tail': check_tail,
        'tip': check_tip,
        'tail_x': check_tail_x,
        'tail_y': check_tail_y,
        'tip_x': check_tip_x,
        'tip_y': check_tip_y,
        'coords': check_coords,
        'length': check_length,
        'angle': check_angle,
        'segment_angle': check_segment_angle,
        'segment_coords': check_segment_coords,
        'points_on_line': check_points_on_line,
        'point_coords': check_point_coords,
    }

    def __init__(self, success_message='Test passed', custom_checks=None):
        self.success_message = success_message
        if custom_checks:
            self.check_registry.update(custom_checks)

    def grade(self, answer):
        """
        Check correctness of `answer` by running checks defined for it one by one.

        Short-circuit as soon as a single check fails.
        """
        check_data = dict(
            vectors=self._get_vectors(answer),
            points=self._get_points(answer),
        )
        for check in answer['checks']:
            check_data['check'] = check
            check_fn = self.check_registry[check['check']]
            args = [check_data[arg] for arg in inspect.getargspec(check_fn).args]
            try:
                check_fn(*args)
            except ValueError as e:
                return {'correct': False, 'msg': e.message}
        return {'correct': True, 'msg': self.success_message}

    def _get_vectors(self, answer):  # pylint: disable=no-self-use
        """
        Turn vector info in `answer` into a dictionary of Vector objects.
        """
        vectors = {}
        for name, props in answer['vectors'].iteritems():
            tail = props['tail']
            tip = props['tip']
            vectors[name] = Vector(name, tail[0], tail[1], tip[0], tip[1])
        return vectors

    def _get_points(self, answer):  # pylint: disable=no-self-use
        """
        Turn point info in `answer` into a dictionary of Point objects.
        """
        return {name: Point(*coords) for name, coords in answer['points'].iteritems()}
