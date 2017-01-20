"""An XBlock that allows course authors to define vector drawing exercises."""

import json
import logging

from xblock.core import XBlock
from xblock.exceptions import JsonHandlerError
from xblock.fields import Scope, Boolean, Dict, Float, Integer, String
from xblock.fragment import Fragment
from xblock.validation import ValidationMessage
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin

try:
    # Used to detect if we're in the workbench so we can add Underscore.js
    from workbench.runtime import WorkbenchRuntime
except ImportError:
    WorkbenchRuntime = False  # pylint: disable=invalid-name

from .grader import Grader
from .utils import get_doc_link


loader = ResourceLoader(__name__)  # pylint: disable=invalid-name

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


class VectorDrawXBlock(StudioEditableXBlockMixin, XBlock):
    """
    An XBlock that allows course authors to define vector drawing exercises.
    """

    icon_class = "problem"

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
        help=(
            "Show the graph axis. "
            "Will also show grid lines (but note that the background image might cover them). "
            "Enabling this option makes the exercise more accessible for users "
            "relying on the keyboard for manipulating vectors."
        ),
        default=True,
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

    background_description = String(
        display_name="Background description",
        help=(
            "Please provide a description of the image for non-visual users. "
            "The description should provide sufficient information that would allow anyone "
            "to solve the problem if the image did not load."
        ),
        default="",
        scope=Scope.content
    )

    vectors = String(
        display_name="Vectors",
        help=(
            "List of vectors to use for the exercise. "
            "You must specify it as an array of entries "
            "where each entry represents an individual vector. "
            "See {doc_link} for more information. "
            "Note that you can also use the WYSIWYG editor below to create or modify vectors. "
            "If you do, any changes you make here will be overwritten by vector data "
            "from the WYSIWYG editor when saving."
        ).format(doc_link=get_doc_link('vectors')),
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
            "where each entry represents an individual point. "
            "See {doc_link} for more information."
        ).format(doc_link=get_doc_link('points')),
        default="[]",
        multiline_editor=True,
        resettable_editor=False,
        scope=Scope.content
    )

    expected_result = String(
        display_name="Expected result",
        help=(
            "Defines vector properties for grading. "
            "You must specify it as a JSON object where each key is the name of an existing vector "
            "and each value is a JSON object containing information about checks to perform "
            "and expected values. "
            "See {doc_link} for more information. "
            "Vectors omitted from this setting are ignored when grading. "
            "Note that you can also use the WYSIWYG editor below to opt in and out of checks "
            "for individual vectors. "
            "If you use the WYSIWYG editor at all, any changes you make here "
            "will be overwritten when saving."
        ).format(doc_link=get_doc_link('expected_result')),
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

    # Dictionary that keeps track of vector positions for correct answer;
    # treated as an editable field but hidden from author in Studio
    # since changes to it are implicit
    expected_result_positions = Dict(scope=Scope.content)

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
        'background_description',
        'vectors',
        'points',
        'expected_result',
        'expected_result_positions',
        'custom_checks'
    )

    has_score = True

    @property
    def settings(self):
        """
        Return settings for this exercise.
        """
        width_scale = self.width / float(self.height)
        box_size = self.bounding_box_size
        bounding_box = [-box_size*width_scale, box_size, box_size*width_scale, -box_size]
        return {
            'width': self.width,
            'height': self.height,
            'bounding_box': bounding_box,
            'axis': self.axis,
            'show_navigation': self.show_navigation,
            'show_vector_properties': self.show_vector_properties,
            'show_slope_for_lines': self.show_slope_for_lines,
            'add_vector_label': self.add_vector_label,
            'vector_properties_label': self.vector_properties_label,
            'background': self.background,
            'vectors': self.get_vectors,
            'points': self.get_points,
            'expected_result': self.get_expected_result,
            'expected_result_positions': self.expected_result_positions,
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
            'description': self.background_description,
        }

    def _get_default_vector(self):  # pylint: disable=no-self-use
        """
        Return dictionary that represents vector with default values filled in.
        """
        return {
            'type': 'vector',
            'render': False,
            'length_factor': 1,
            'length_units': '',
            'base_angle': 0,
            'style': {
                'pointSize': 1,
                'pointColor': 'red',
                'width': 4,
                'color': 'blue',
                'label': None,
                'labelColor': 'black'
            }
        }

    @property
    def get_vectors(self):
        """
        Return info about vectors belonging to this exercise.

        To do this, load vector info from JSON string specified by course author,
        and augment it with default values that are required for rendering vectors on the client.
        """
        vectors = []
        for vector in json.loads(self.vectors):
            default_vector = self._get_default_vector()
            default_vector_style = default_vector['style']
            default_vector_style.update(vector.pop('style', {}))
            default_vector.update(vector)
            vectors.append(default_vector)
        return vectors

    def _get_default_point(self):  # pylint: disable=no-self-use
        """
        Return dictionary that represents point with default values filled in.
        """
        return {
            'fixed': True,  # Default to True for backwards compatibility
            'render': True,
            'style': {
                'size': 1,
                'withLabel': False,
                'color': 'pink',
                'showInfoBox': False
            }
        }

    @property
    def get_points(self):
        """
        Return info about points belonging to this exercise.

        To do this, load point info from JSON string specified by course author,
        and augment it with default values that are required for rendering points on the client.
        """
        points = []
        for point in json.loads(self.points):
            default_point = self._get_default_point()
            default_point_style = default_point['style']
            default_point_style.update(point.pop('style', {}))
            default_point.update(point)
            default_point_style['name'] = default_point['name']
            default_point_style['fixed'] = default_point['fixed']
            point_color = default_point_style['color']
            default_point_style['strokeColor'] = point_color
            default_point_style['fillColor'] = point_color
            del default_point_style['color']
            points.append(default_point)
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
        context = context or {}
        context['self'] = self
        fragment = Fragment()
        fragment.add_content(loader.render_template('templates/html/vectordraw.html', context))
        fragment.add_css_url(
            "//cdnjs.cloudflare.com/ajax/libs/font-awesome/4.3.0/css/font-awesome.min.css"
        )
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/vectordraw.css'))
        # Workbench doesn't have Underscore.js, so add it:
        if WorkbenchRuntime and isinstance(self.runtime, WorkbenchRuntime):
            fragment.add_javascript_url(
                "//cdnjs.cloudflare.com/ajax/libs/underscore.js/1.8.2/underscore-min.js"
            )
        fragment.add_javascript_url(
            "//cdnjs.cloudflare.com/ajax/libs/jsxgraph/0.98/jsxgraphcore.js"
        )
        fragment.add_javascript_url(
            self.runtime.local_resource_url(self, 'public/js/vectordraw.js')
        )
        fragment.initialize_js(
            'VectorDrawXBlock', {"settings": self.settings, "user_state": self.user_state}
        )
        return fragment

    def studio_view(self, context):
        fragment = Fragment()
        context = {'fields': [], 'self': self}
        # Build a list of all the fields that can be edited:
        for field_name in self.editable_fields:
            if field_name == "expected_result_positions":
                continue
            field = self.fields[field_name]
            assert field.scope in (Scope.content, Scope.settings), (
                "Only Scope.content or Scope.settings fields can be used with "
                "StudioEditableXBlockMixin. Other scopes are for user-specific data and are "
                "not generally created/configured by content authors in Studio."
            )
            field_info = self._make_field_info(field_name, field)
            if field_info is not None:
                context["fields"].append(field_info)
        fragment.add_content(loader.render_template("templates/html/vectordraw_edit.html", context))
        # Add resources to studio_view fragment
        fragment.add_css_url(
            self.runtime.local_resource_url(self, 'public/css/vectordraw.css')
        )
        fragment.add_css_url(
            self.runtime.local_resource_url(self, 'public/css/vectordraw_edit.css')
        )
        fragment.add_javascript_url(
            "//cdnjs.cloudflare.com/ajax/libs/jsxgraph/0.98/jsxgraphcore.js"
        )
        fragment.add_javascript_url(
            self.runtime.local_resource_url(self, 'public/js/studio_edit.js')
        )
        fragment.add_javascript_url(
            self.runtime.local_resource_url(self, 'public/js/vectordraw_edit.js')
        )
        fragment.initialize_js(
            'VectorDrawXBlockEdit', {"settings": self.settings}
        )
        return fragment

    def validate_field_data(self, validation, data):
        """
        Validate this block's field data.
        """
        super(VectorDrawXBlock, self).validate_field_data(validation, data)

        def add_error(msg):
            """ Helper function for adding validation messages. """
            validation.add(ValidationMessage(ValidationMessage.ERROR, msg))

        if data.background_url.strip():
            if data.background_width == 0 and data.background_height == 0:
                add_error(
                    u"You specified a background image but no width or height. "
                    "For the image to display, you need to specify a non-zero value "
                    "for at least one of them."
                )
            if not data.background_description.strip():
                add_error(
                    u"No background description set. "
                    "This means that it will be more difficult for non-visual users "
                    "to solve the problem. "
                    "Please provide a description that contains sufficient information "
                    "that would allow anyone to solve the problem if the image did not load."
                )

    def _validate_check_answer_data(self, data):  # pylint: disable=no-self-use
        """
        Validate answer data submitted by user.
        """
        # Check vectors
        vectors = data.get('vectors')
        if not isinstance(vectors, dict):
            raise ValueError
        for vector_data in vectors.values():
            # Validate vector
            if not vector_data.viewkeys() == {'tail', 'tip'}:
                raise ValueError
            # Validate tip and tail
            tip = vector_data['tip']
            tip_valid = isinstance(tip, list) and len(tip) == 2
            tail = vector_data['tail']
            tail_valid = isinstance(tail, list) and len(tail) == 2
            if not (tip_valid and tail_valid):
                raise ValueError
        # Check points
        points = data.get('points')
        if not isinstance(points, dict):
            raise ValueError
        for coords in points.values():
            # Validate point
            point_valid = isinstance(coords, list) and len(coords) == 2
            if not point_valid:
                raise ValueError
        # If we get to this point, it means that vector and point data is valid;
        # the only thing left to check is whether data contains a list of checks:
        if 'checks' not in data:
            raise ValueError

    @XBlock.json_handler
    def check_answer(self, data, suffix=''):  # pylint: disable=unused-argument
        """
        Check and persist student's answer to this vector drawing problem.
        """
        # Validate data
        try:
            self._validate_check_answer_data(data)
        except ValueError:
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
        score = 1 if result["correct"] else 0
        self.runtime.publish(self, 'grade', dict(value=score, max_value=1))
        return {
            "result": result,
        }

    @staticmethod
    def workbench_scenarios():
        """
        Canned scenarios for display in the workbench.
        """
        return loader.load_scenarios_from_path('templates/xml')
