"""TO-DO: Write a description of what this XBlock is."""

import json
import pkg_resources

from xblock.core import XBlock
from xblock.fields import Scope, Boolean, Integer, String
from xblock.fragment import Fragment
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin


loader = ResourceLoader(__name__)


class VectorDrawXBlock(StudioEditableXBlockMixin, XBlock):
    """
    TO-DO: document what your XBlock does.
    """

    # Fields are defined on the class.  You can access them in your code as
    # self.<fieldname>.

    # TO-DO: delete count, and define your own fields.
    count = Integer(
        default=0, scope=Scope.user_state,
        help="A simple counter, to show something happening",
    )

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
        display_name="",
        help="The height of the board in pixels",
        default=400,
        scope=Scope.content
    )

    bounding_box_size = Integer(
        display_name="",
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
            "You must specify it as an array of entries where each entry represents an individual vector."
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
            "You must specify it as an array of entries where each entry represents an individual point."
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
            'This is needed when grading is more complex and cannot be defined in terms of "Expected results" only.'
        ),
        default="[]",
        multiline_editor=True,
        resettable_editor=False,
        scope=Scope.content
    )

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

    @property
    def background(self):
        return {
            'src': self.background_url,
            'width': self.background_width,
            'height': self.background_height,
        }

    @property
    def vectors_json(self):
        return json.loads(self.vectors)

    @property
    def points_json(self):
        return json.loads(self.points)

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    # TO-DO: change this view to display your data your own way.
    def student_view(self, context=None):
        """
        The primary view of the VectorDrawXBlock, shown to students
        when viewing courses.
        """
        context['self'] = self
        fragment = Fragment()
        fragment.add_content(loader.render_template('static/html/vectordraw.html', context))
        fragment.add_css(self.resource_string('static/css/vectordraw.css'))
        fragment.add_javascript_url("//cdnjs.cloudflare.com/ajax/libs/jsxgraph/0.98/jsxgraphcore.js")
        fragment.add_javascript(self.resource_string("static/js/src/vectordraw.js"))
        fragment.initialize_js(
            'VectorDrawXBlock',
            {
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
                'vectors': self.vectors_json,
                'points': self.points_json,
            }
        )
        return fragment

    # TO-DO: change this handler to perform your own actions.  You may need more
    # than one handler, or you may not need any handlers at all.
    @XBlock.json_handler
    def increment_count(self, data, suffix=''):
        """
        An example handler, which increments the data.
        """
        # Just to show data coming in...
        assert data['hello'] == 'world'

        self.count += 1
        return {"count": self.count}

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
