"""An XBlock that allows course authors to define vector drawing exercises."""

import json
import logging

from xblock.core import XBlock
from xblock.exceptions import JsonHandlerError
from xblock.fields import Scope, Boolean, Dict, Float, Integer, String
from xblock.fragment import Fragment
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin

from .grader import Grader


loader = ResourceLoader(__name__)  # pylint: disable=invalid-name

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


class VectorDrawXBlock(StudioEditableXBlockMixin, XBlock):
    """
    An XBlock that allows course authors to define vector drawing exercises.
    """

    # Content
    display_name = String(
        display_name="Title (display name)",
        help="Title to display",
        default="Vector Drawing",
        scope=Scope.content
    )

    description = String(
        display_name="Description",
        help="Exercise description displayed above vector drawing box",
        default="",
        multiline_editor="html",
        resettable_editor=False,
        scope=Scope.content
    )

    width = Integer(
        display_name="Width",
        help="The width of the board in pixels",
        default=550,
        scope=Scope.content
    )

    height = Integer(
        display_name="Height",
        help="The height of the board in pixels",
        default=400,
        scope=Scope.content
    )

    bounding_box_size = Integer(
        display_name="Bounding box size",
        help=(
            "Defines the bounding box height of the graph area. "
            "The bounding box width is calculated from the width/height ratio."
        ),
        default=10,
        scope=Scope.content
    )

    axis = Boolean(
        display_name="Show axis",
        help="Show the graph axis",
        default=False,
        scope=Scope.content
    )

    show_navigation = Boolean(
        display_name="Show navigation",
        help="Show navigation arrows and zoom controls",
        default=False,
        scope=Scope.content
    )

    show_vector_properties = Boolean(
        display_name="Show vector properties",
        help="Show box detailing vector properties",
        default=True,
        scope=Scope.content
    )

    show_slope_for_lines = Boolean(
        display_name="Show slope for lines",
        help="If True, slope will be shown for line objects.",
        default=False,
        scope=Scope.content
    )

    add_vector_label = String(
        display_name="Add vector label",
        help="Label for button that allows to add vectors to the board",
        default="Add Selected Force",
        scope=Scope.content
    )

    vector_properties_label = String(
        display_name="Vector properties label",
        help="Label for box that displays vector properties",
        default="Vector Properties",
        scope=Scope.content
    )

    background_url = String(
        display_name="Background URL",
        help="URL for background image",
        default="",
        scope=Scope.content
    )

    background_width = Integer(
        display_name="Background width",
        help="Width of background image",
        default=0,
        scope=Scope.content
    )

    background_height = Integer(
        display_name="Background height",
        help="Height of background image",
        default=0,
        scope=Scope.content
    )

    vectors = String(
        display_name="Vectors",
        help=(
            "List of vectors to use for the exercise. "
            "You must specify it as an array of entries "
            "where each entry represents an individual vector."
        ),
        default="[]",
        multiline_editor=True,
        resettable_editor=False,
        scope=Scope.content
    )

    points = String(
        display_name="Points",
        help=(
            "List of points to be drawn on the board for reference, or to be placed by the student."
            "You must specify it as an array of entries "
            "where each entry represents an individual point."
        ),
        default="[]",
        multiline_editor=True,
        resettable_editor=False,
        scope=Scope.content
    )

    expected_result = String(
        display_name="Expected result",
        help=(
            "Defines vector properties for grading. "
            "Vectors omitted from this setting are ignored when grading."
        ),
        default="{}",
        multiline_editor=True,
        resettable_editor=False,
        scope=Scope.content
    )

    custom_checks = String(
        display_name="Custom checks",
        help=(
            'List of custom checks to use for grading. '
            'This is needed when grading is more complex '
            'and cannot be defined in terms of "Expected results" only.'
        ),
        default="[]",
        multiline_editor=True,
        resettable_editor=False,
        scope=Scope.content
    )

    weight = Float(
        display_name="Weight",
        default=1,
        scope=Scope.settings,
        enforce_type=True
    )

    # User state

    # Dictionary containing vectors and points present on the board when user last clicked "Check",
    # as well as checks to perform in order to obtain grade
    answer = Dict(scope=Scope.user_state)
    # Dictionary that represents result returned by the grader for the most recent answer;
    # contains info about correctness of answer and feedback message
    result = Dict(scope=Scope.user_state)

    editable_fields = (
        'display_name',
        'description',
        'width',
        'height',
        'bounding_box_size',
        'axis',
        'show_navigation',
        'show_vector_properties',
        'show_slope_for_lines',
        'add_vector_label',
        'vector_properties_label',
        'background_url',
        'background_width',
        'background_height',
        'vectors',
        'points',
        'expected_result',
        'custom_checks'
    )

    has_score = True

    @property
    def settings(self):
        """
        Return settings for this exercise.
        """
        return {
            'width': self.width,
            'height': self.height,
            'bounding_box_size': self.bounding_box_size,
            'axis': self.axis,
            'show_navigation': self.show_navigation,
            'show_vector_properties': self.show_vector_properties,
            'show_slope_for_lines': self.show_slope_for_lines,
            'add_vector_label': self.add_vector_label,
            'vector_properties_label': self.vector_properties_label,
            'background': self.background,
            'vectors': self.get_vectors,
            'points': self.get_points,
            'expected_result': self.get_expected_result
        }

    @property
    def user_state(self):
        """
        Return user state, which is a combination of most recent answer and result.
        """
        user_state = self.answer
        if self.result:
            user_state['result'] = self.result
        return user_state

    @property
    def background(self):
        """
        Return information about background to draw for this exercise.
        """
        return {
            'src': self.background_url,
            'width': self.background_width,
            'height': self.background_height,
        }

    @property
    def get_vectors(self):
        """
        Load info about vectors for this exercise from JSON string specified by course author.
        """
        return json.loads(self.vectors)

    @property
    def get_points(self):
        """
        Load info about points for this exercise from JSON string specified by course author.
        """
        points = json.loads(self.points)
        for point in points:
            # If author did not specify whether point should be drawn in fixed location (True)
            # or placed by student (False), we default to True;
            # template needs this info to determine whether it should add option
            # for selecting point to dropdown menu:
            if 'fixed' not in point:
                point['fixed'] = True
        return points

    @property
    def get_expected_result(self):
        """
        Load info about expected result for this exercise
        from JSON string specified by course author.
        """
        return json.loads(self.expected_result)

    def student_view(self, context=None):
        """
        The primary view of the VectorDrawXBlock, shown to students
        when viewing courses.
        """
        context['self'] = self
        fragment = Fragment()
        fragment.add_content(loader.render_template('static/html/vectordraw.html', context))
        fragment.add_css_url(
            "//cdnjs.cloudflare.com/ajax/libs/font-awesome/4.3.0/css/font-awesome.min.css"
        )
        fragment.add_css(loader.load_unicode('static/css/vectordraw.css'))
        fragment.add_javascript_url(
            "//cdnjs.cloudflare.com/ajax/libs/jsxgraph/0.98/jsxgraphcore.js"
        )
        fragment.add_javascript(loader.load_unicode("static/js/src/vectordraw.js"))
        fragment.initialize_js(
            'VectorDrawXBlock', {"settings": self.settings, "user_state": self.user_state}
        )
        return fragment

    def is_valid(self, data):  # pylint: disable=no-self-use
        """
        Validate answer data submitted by user.
        """
        # Check vectors
        vectors = data.get('vectors')
        if vectors is None:
            return False
        for vector_data in vectors.values():
            # Validate vector
            vector_valid = 'tip' in vector_data and 'tail' in vector_data
            if not vector_valid:
                return False
            # Validate tip and tail
            tip = vector_data['tip']
            tip_valid = type(tip) == list and len(tip) == 2
            tail = vector_data['tail']
            tail_valid = type(tail) == list and len(tail) == 2
            if not (tip_valid and tail_valid):
                return False
        # Check points
        points = data.get('points')
        if points is None:
            return False
        for coords in points.values():
            # Validate point
            point_valid = type(coords) == list and len(coords) == 2
            if not point_valid:
                break
        # If we get to this point, it means that vector and point data is valid;
        # the only thing left to check is whether data contains a list of checks:
        return 'checks' in data

    @XBlock.json_handler
    def check_answer(self, data, suffix=''):  # pylint: disable=unused-argument
        """
        Check and persist student's answer to this vector drawing problem.
        """
        # Validate data
        if not self.is_valid(data):
            raise JsonHandlerError(400, "Invalid data")
        # Save answer
        self.answer = dict(
            vectors=data["vectors"],
            points=data["points"]
        )
        # Compute result
        grader = Grader()
        result = grader.grade(data)
        # Save result
        self.result = result
        # Publish grade data
        score = 1 if result["ok"] else 0
        self.runtime.publish(self, 'grade', dict(value=score, max_value=1))
        return {
            "result": result,
        }

    # TO-DO: change this to create the scenarios you'd like to see in the
    # workbench while developing your XBlock.
    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("VectorDrawXBlock",
             """<vertical_demo>
                <vectordraw/>
                <vectordraw/>
                <vectordraw/>
                </vertical_demo>
             """),
        ]
