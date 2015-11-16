import json

from ddt import ddt, data
from selenium.common.exceptions import NoSuchElementException

from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable_test import StudioEditableBaseTest

loader = ResourceLoader(__name__)  # pylint: disable=invalid-name


@ddt
class TestVectorDraw(StudioEditableBaseTest):
    """
    Test student view of VectorDrawXBlock.
    """

    def load_scenario(self, path, params=None):
        scenario = loader.render_template(path, params)
        self.set_scenario_xml(scenario)
        self.element = self.go_to_view("student_view")
        self.exercise = self.element.find_element_by_css_selector(".vectordraw_block")

    def assert_not_present(self, parent, selector, errmsg):
        try:
            parent.find_element_by_css_selector(selector)
        except NoSuchElementException:
            pass
        else:
            self.fail(errmsg)

    def check_title_and_description(self, expected_title="Vector Drawing", expected_description=None):
        title = self.exercise.find_element_by_css_selector("h2")
        self.assertEquals(title.text, expected_title)
        if expected_description:
            description = self.exercise.find_element_by_css_selector(".vectordraw-description")
            self.assertEquals(description.text, expected_description)
        else:
            self.assert_not_present(
                self.exercise,
                ".vectordraw-description",
                "Description element present even though no description has been set by user."
            )

    def check_dimensions(self, board, expected_width="550px", expected_height="400px"):
        width = board.value_of_css_property("width")
        height = board.value_of_css_property("height")
        self.assertEquals(width, expected_width)
        self.assertEquals(height, expected_height)

    def check_axis(self, board, is_present=False):
        text_elements = board.find_elements_by_css_selector(".JXGtext")
        ticks = any("ticks" in text_element.get_attribute("id") for text_element in text_elements)
        self.assertEquals(ticks, is_present)

    def check_navigation_bar(self, board, is_present=False):
        if is_present:
            navigation_bar = board.find_element_by_css_selector("#jxgboard1_navigationbar")
            self.assertTrue(navigation_bar.is_displayed())
        else:
            self.assert_not_present(
                board,
                "#jxgboard1_navigationbar",
                "Navigation bar should be hidden by default."
            )

    def check_background(self, board, is_present=False):
        if is_present:
            background = board.find_element_by_css_selector("image")
            self.assertTrue(background.is_displayed())
            src = background.get_attribute("xlink:href")
            self.assertEquals(src, "https://github.com/open-craft/jsinput-vectordraw/raw/master/Notes_and_Examples/2_boxIncline_multiVector/box_on_incline.png")
        else:
            self.assert_not_present(
                board,
                "image",
                "Board should not contain background image by default."
            )

    def check_buttons(self, controls, add_vector_label="Add Selected Force"):
        add_vector = controls.find_element_by_css_selector(".add-vector")
        self.assertEquals(add_vector.text, add_vector_label)
        reset = controls.find_element_by_css_selector(".reset")
        self.assertEquals(reset.text, "Reset")
        undo = controls.find_element_by_css_selector(".undo")
        undo.find_element_by_css_selector(".fa.fa-undo")
        redo = controls.find_element_by_css_selector(".redo")
        redo.find_element_by_css_selector(".fa.fa-repeat")

    def check_vector_properties(
            self, menu, is_present=False, expected_label="Vector Properties",
            expected_name=None, expected_length=None, expected_angle=None
    ):
        if is_present:
            vector_properties = menu.find_element_by_css_selector(".vector-properties")
            vector_properties_label = vector_properties.find_element_by_css_selector("h3")
            self.assertEquals(vector_properties_label.text, expected_label)
            vector_name = vector_properties.find_element_by_css_selector(".vector-prop-name")
            self.assertEquals(vector_name.text, "name: {}".format(expected_name or "-"))
            vector_length = vector_properties.find_element_by_css_selector(".vector-prop-length")
            self.assertEquals(vector_length.text, "length: {}".format(expected_length or "-"))
            vector_angle = vector_properties.find_element_by_css_selector(".vector-prop-angle")
            self.assertTrue(vector_angle.text.startswith("angle: {}".format(expected_angle or "-")))
            vector_slope = vector_properties.find_element_by_css_selector(".vector-prop-slope")
            self.assertFalse(vector_slope.is_displayed())
        else:
            self.assert_not_present(
                menu,
                ".vector-properties",
                "If show_vector_properties is set to False, menu should not show vector properties."
            )

    def check_actions(self):
        actions = self.exercise.find_element_by_css_selector(".action")
        self.assertTrue(actions.is_displayed())
        check = actions.find_element_by_css_selector(".check")
        self.assertEquals(check.text, "CHECK YOUR ANSWER")

    def check_dropdown(self, controls, vectors=[], points=[]):
        dropdown = controls.find_element_by_css_selector("select")
        if not vectors and not points:
            self.assert_not_present(
                dropdown,
                "option",
                "Dropdown should not list any vectors or points by default."
            )
        else:
            self.check_options(dropdown, vectors, "vector")
            non_fixed_points = [point for point in points if not point["fixed"]]
            self.check_options(dropdown, non_fixed_points, "point")

    def check_options(self, dropdown, elements, element_type):
        element_options = dropdown.find_elements_by_css_selector('option[value^="{}-"]'.format(element_type))
        self.assertEquals(len(element_options), len(elements))
        for element, element_option in zip(elements, element_options):
            self.assertEquals(element_option.text, element["description"])
            option_disabled = element_option.get_attribute("disabled")
            self.assertEquals(bool(option_disabled), element["render"])

    def check_vectors(self, board, vectors):
        line_elements = board.find_elements_by_css_selector("line")
        point_elements = board.find_elements_by_css_selector("ellipse")
        for vector in vectors:
            # Find line
            board_has_line = self.board_has_line(vector["expected_line_position"], line_elements)
            # Find tail
            board_has_tail = self.board_has_point(vector["expected_tail_position"], point_elements)
            # Find tip
            board_has_tip = self.board_has_point(vector["expected_tip_position"], point_elements)
            # Find label
            board_has_label = self.board_has_label(board, vector["name"])
            # Check if line, tip, tail are present
            if vector["render"]:
                self.assertTrue(board_has_line)
                self.assertTrue(board_has_tail)
                self.assertTrue(board_has_tip)
                self.assertTrue(board_has_label)
            else:
                self.assertFalse(board_has_line)
                self.assertFalse(board_has_tail)
                self.assertFalse(board_has_tip)
                self.assertFalse(board_has_label)

    def check_points(self, board, points):
        point_elements = board.find_elements_by_css_selector("ellipse")
        for point in points:
            board_has_point = self.board_has_point(point["expected_position"], point_elements)
            self.assertEquals(board_has_point, point["render"])

    def board_has_line(self, position, line_elements):
        return bool(self.find_line(position, line_elements))

    def board_has_point(self, position, point_elements):
        return bool(self.find_point(position, point_elements))

    def board_has_label(self, board, label_text):
        text_elements = board.find_elements_by_css_selector(".JXGtext")
        for text_element in text_elements:
            is_tick = "ticks" in text_element.get_attribute("id")
            if not is_tick and text_element.text == label_text:
                return True
        return False

    def find_line(self, position, line_elements):
        expected_line_position = position.items()
        for line in line_elements:
            line_position = {
                "x1": int(float(line.get_attribute("x1"))),
                "y1": int(float(line.get_attribute("y1"))),
                "x2": int(float(line.get_attribute("x2"))),
                "y2": int(float(line.get_attribute("y2"))),
            }.items()
            if line_position == expected_line_position:
                return line

    def find_point(self, position, point_elements):
        expected_position = position.items()
        for point in point_elements:
            point_position = {
                "cx": int(float(point.get_attribute("cx"))),
                "cy": int(float(point.get_attribute("cy"))),
            }.items()
            if point_position == expected_position:
                return point

    def add_vector(self, board, vectors):
        menu = self.exercise.find_element_by_css_selector(".menu")
        controls = menu.find_element_by_css_selector(".controls")
        add_vector = controls.find_element_by_css_selector(".add-vector")
        add_vector.click()
        # Board should now show vector
        vectors[0]["render"] = True
        self.check_vectors(board, vectors)
        # "Vector Properties" should display correct info
        self.check_vector_properties(
            menu, is_present=True, expected_label="Custom properties label",
            expected_name="N", expected_length="4.00", expected_angle="45.00"
        )

    def add_point(self, board, points):
        menu = self.exercise.find_element_by_css_selector(".menu")
        controls = menu.find_element_by_css_selector(".controls")
        add_vector = controls.find_element_by_css_selector(".add-vector")
        add_vector.click()
        # Board should now show point
        points[0]["render"] = True
        self.check_points(board, points)

    def undo(self, board, vectors):
        menu = self.exercise.find_element_by_css_selector(".menu")
        controls = menu.find_element_by_css_selector(".controls")
        undo = controls.find_element_by_css_selector(".undo")
        undo.click()
        # Board should not show vector anymore
        vectors[0]["render"] = False
        self.check_vectors(board, vectors)

    def redo(self, board, vectors):
        menu = self.exercise.find_element_by_css_selector(".menu")
        controls = menu.find_element_by_css_selector(".controls")
        redo = controls.find_element_by_css_selector(".redo")
        redo.click()
        # Board should now show vector
        vectors[0]["render"] = True
        self.check_vectors(board, vectors)
        # "Vector Properties" should display correct info
        self.check_vector_properties(
            menu, is_present=True, expected_label="Custom properties label",
            expected_name="N", expected_length="4.00", expected_angle="45.00"
        )

    def reset(self, board, vectors, points):
        menu = self.exercise.find_element_by_css_selector(".menu")
        controls = menu.find_element_by_css_selector(".controls")
        reset = controls.find_element_by_css_selector(".reset")
        reset.click()
        # Board should not show vector anymore
        vectors[0]["render"] = False
        self.check_vectors(board, vectors)
        # Board should not show point anymore
        points[0]["render"] = False
        self.check_points(board, points)

    def submit_answer(self):
        actions = self.exercise.find_element_by_css_selector(".action")
        check = actions.find_element_by_css_selector(".check")
        check.click()

    def check_status(self, answer_correct=True, expected_message="Test passed"):
        status = self.exercise.find_element_by_css_selector(".vectordraw-status")
        self.assertTrue(status.is_displayed())
        correctness = status.find_element_by_css_selector(".correctness")
        if answer_correct:
            self.assertTrue("checkmark-correct fa fa-check" in correctness.get_attribute("class"))
        else:
            self.assertTrue("checkmark-incorrect fa fa-times" in correctness.get_attribute("class"))
        status_message = status.find_element_by_css_selector(".status-message")
        self.assertEquals(status_message.text, expected_message)

    def test_defaults(self):
        self.load_scenario("xml/defaults.xml")

        # Check title and description
        self.check_title_and_description()

        # Check board
        board = self.exercise.find_element_by_css_selector("#jxgboard1")
        self.check_dimensions(board)
        self.check_axis(board)
        self.check_navigation_bar(board)
        self.check_background(board)
        # - Vectors
        self.assert_not_present(
            board,
            "line",
            "Board should not contain any vectors or lines by default."
        )
        # - Points
        self.assert_not_present(
            board,
            "ellipse",
            "Board should not contain any points by default."
        )

        # Check menu
        menu = self.exercise.find_element_by_css_selector(".menu")
        controls = menu.find_element_by_css_selector(".controls")
        self.check_dropdown(controls)
        self.check_buttons(controls)
        self.check_vector_properties(menu, is_present=True)

        # Check actions
        self.check_actions()

    @data(
        {
            "show_vector_properties": True,
            "vectors": json.dumps([
                {
                    "name": "N",
                    "description": "Normal force - N",
                    "tail": [2, 2],
                    "length": 4,
                    "angle": 45,
                    "render": True,
                    "expected_line_position": {"x1": 347, "y1": 181, "x2": 402, "y2": 125},
                    "expected_tail_position": {"cx": 347, "cy": 181},
                    "expected_tip_position": {"cx": 411, "cy": 117},
                }, {
                    "name": "f",
                    "description": "Friction - f",
                    "coords": [
                        [-2, -5],
                        [-1, -3]
                    ],
                    "render": False,
                    "expected_line_position": {"x1": 257, "y1": 340, "x2": 273, "y2": 304},
                    "expected_tail_position": {"cx": 257, "cy": 340},
                    "expected_tip_position": {"cx": 279, "cy": 294},
                }
            ]),
            "points": json.dumps([
                {
                    "name": "cmA",
                    "description": "Point A",
                    "coords": [-0.1, -2.2],
                    "render": True,
                    "fixed": True,
                    "expected_position": {"cx": 300, "cy": 276},
                },
                {
                    "name": "cmB",
                    "description": "Point B",
                    "coords": [-4.0, 0.21],
                    "render": True,
                    "fixed": False,
                    "expected_position": {"cx": 211, "cy": 222},
                },
                {
                    "name": "cmC",
                    "description": "Point C",
                    "coords": [2.5, 2.9],
                    "render": False,
                    "fixed": False,
                    "expected_position": {"cx": 359, "cy": 161},
                }
            ]),
            "expected_result": json.dumps({})
        },
        {
            "show_vector_properties": False,
            "vectors": json.dumps([]),
            "points": json.dumps([]),
            "expected_result": json.dumps({})
        },
    )
    def test_custom_exercise(self, params):
        vectors = json.loads(params["vectors"])
        points = json.loads(params["points"])
        self.load_scenario("xml/custom.xml", params=params)

        # Check title and description
        self.check_title_and_description(
            expected_title="Custom Exercise", expected_description="Custom exercise description"
        )

        # Check board
        board = self.exercise.find_element_by_css_selector("#jxgboard1")
        self.check_dimensions(board, expected_width="600px", expected_height="450px")
        self.check_axis(board, is_present=True)
        self.check_navigation_bar(board, is_present=True)
        self.check_background(board, is_present=True)
        # - Vectors
        self.check_vectors(board, vectors)
        # - Points
        self.check_points(board, points)

        # Check menu
        menu = self.exercise.find_element_by_css_selector(".menu")
        controls = menu.find_element_by_css_selector(".controls")
        self.check_dropdown(controls, vectors, points)
        self.check_buttons(controls, add_vector_label="Custom button label")
        show_vector_properties = params["show_vector_properties"]
        if show_vector_properties:
            self.check_vector_properties(menu, is_present=True, expected_label="Custom properties label")
        else:
            self.check_vector_properties(menu)

        # Check actions
        self.check_actions()

    @data("line", "tail", "tip")
    def test_select_vector(self, click_target):
        params = {
            "show_vector_properties": True,
            "vectors": json.dumps([
                {
                    "name": "N",
                    "description": "Normal force - N",
                    "tail": [2, 2],
                    "length": 4,
                    "angle": 45,
                    "render": True,
                    "expected_line_position": {"x1": 347, "y1": 181, "x2": 402, "y2": 125},
                    "expected_tail_position": {"cx": 347, "cy": 181},
                    "expected_tip_position": {"cx": 411, "cy": 117},
                }
            ]),
            "points": json.dumps([]),
            "expected_result": json.dumps({})
        }
        self.load_scenario("xml/custom.xml", params=params)
        board = self.exercise.find_element_by_css_selector("#jxgboard1")
        vector = json.loads(params["vectors"])[0]
        if click_target == "line":
            # Find line and click it
            line_elements = board.find_elements_by_css_selector("line")
            line = self.find_line(vector["expected_line_position"], line_elements)
            line.click()
        elif click_target == "tail":
            # Find tail and click it
            point_elements = board.find_elements_by_css_selector("ellipse")
            tail = self.find_point(vector["expected_tail_position"], point_elements)
            tail.click()
        else:
            # Find tip and click it
            point_elements = board.find_elements_by_css_selector("ellipse")
            tip = self.find_point(vector["expected_tip_position"], point_elements)
            tip.click()
        # Check if "Vector Properties" shows correct info
        menu = self.exercise.find_element_by_css_selector(".menu")
        self.check_vector_properties(
            menu, is_present=True, expected_label="Custom properties label",
            expected_name="N", expected_length="4.00", expected_angle="45.00"
        )

    @data(
        {
            "show_vector_properties": True,
            "vectors": json.dumps([
                {
                    "name": "N",
                    "description": "Normal force - N",
                    "tail": [2, 2],
                    "length": 4,
                    "angle": 45,
                    "render": False,
                    "expected_line_position": {"x1": 347, "y1": 181, "x2": 402, "y2": 125},
                    "expected_tail_position": {"cx": 347, "cy": 181},
                    "expected_tip_position": {"cx": 411, "cy": 117},
                }
            ]),
            "points": json.dumps([]),
            "expected_result": json.dumps({})
        }
    )
    def test_add_vector(self, params):
        self.load_scenario("xml/custom.xml", params=params)
        board = self.exercise.find_element_by_css_selector("#jxgboard1")
        # Board should not show vector initially
        vectors = json.loads(params["vectors"])
        self.check_vectors(board, vectors)
        # Add vector
        self.add_vector(board, vectors)

    @data(
        {
            "show_vector_properties": True,
            "vectors": json.dumps([]),
            "points": json.dumps([
                {
                    "name": "cmC",
                    "description": "Point C",
                    "coords": [2.5, 2.9],
                    "render": False,
                    "fixed": False,
                    "expected_position": {"cx": 359, "cy": 161},
                }
            ]),
            "expected_result": json.dumps({})
        }
    )
    def test_add_point(self, params):
        self.load_scenario("xml/custom.xml", params=params)
        board = self.exercise.find_element_by_css_selector("#jxgboard1")
        # Board should not show point initially
        points = json.loads(params["points"])
        self.check_points(board, points)
        # Add point
        self.add_point(board, points)

    @data(
        {
            "show_vector_properties": True,
            "vectors": json.dumps([
                {
                    "name": "N",
                    "description": "Normal force - N",
                    "tail": [2, 2],
                    "length": 4,
                    "angle": 45,
                    "render": False,
                    "expected_line_position": {"x1": 347, "y1": 181, "x2": 402, "y2": 125},
                    "expected_tail_position": {"cx": 347, "cy": 181},
                    "expected_tip_position": {"cx": 411, "cy": 117},
                }
            ]),
            "points": json.dumps([]),
            "expected_result": json.dumps({})
        }
    )
    def test_undo(self, params):
        self.load_scenario("xml/custom.xml", params=params)
        board = self.exercise.find_element_by_css_selector("#jxgboard1")
        # Board should not show vector initially
        vectors = json.loads(params["vectors"])
        self.check_vectors(board, vectors)
        # Add vector
        self.add_vector(board, vectors)
        # Undo
        self.undo(board, vectors)

    @data(
        {
            "show_vector_properties": True,
            "vectors": json.dumps([
                {
                    "name": "N",
                    "description": "Normal force - N",
                    "tail": [2, 2],
                    "length": 4,
                    "angle": 45,
                    "render": False,
                    "expected_line_position": {"x1": 347, "y1": 181, "x2": 402, "y2": 125},
                    "expected_tail_position": {"cx": 347, "cy": 181},
                    "expected_tip_position": {"cx": 411, "cy": 117},
                }
            ]),
            "points": json.dumps([]),
            "expected_result": json.dumps({})
        }
    )
    def test_redo(self, params):
        self.load_scenario("xml/custom.xml", params=params)
        board = self.exercise.find_element_by_css_selector("#jxgboard1")
        # Board should not show vector initially
        vectors = json.loads(params["vectors"])
        self.check_vectors(board, vectors)
        # Add vector
        self.add_vector(board, vectors)
        # Undo
        self.undo(board, vectors)
        # Redo
        self.redo(board, vectors)

    @data(
        {
            "show_vector_properties": True,
            "vectors": json.dumps([
                {
                    "name": "N",
                    "description": "Normal force - N",
                    "tail": [2, 2],
                    "length": 4,
                    "angle": 45,
                    "render": False,
                    "expected_line_position": {"x1": 347, "y1": 181, "x2": 402, "y2": 125},
                    "expected_tail_position": {"cx": 347, "cy": 181},
                    "expected_tip_position": {"cx": 411, "cy": 117},
                }
            ]),
            "points": json.dumps([
                {
                    "name": "cmC",
                    "description": "Point C",
                    "coords": [2.5, 2.9],
                    "render": False,
                    "fixed": False,
                    "expected_position": {"cx": 359, "cy": 161},
                }
            ]),
            "expected_result": json.dumps({})
        }
    )
    def test_reset(self, params):
        self.load_scenario("xml/custom.xml", params=params)
        board = self.exercise.find_element_by_css_selector("#jxgboard1")
        # Board should not show vector initially
        vectors = json.loads(params["vectors"])
        self.check_vectors(board, vectors)
        # Board should not show point initially
        points = json.loads(params["points"])
        self.check_points(board, points)
        # Add point (need to do this first since point is selected initially)
        self.add_point(board, points)
        # Add vector
        self.add_vector(board, vectors)
        # Reset
        self.reset(board, vectors, points)

    @data(
        {
            "show_vector_properties": True,
            "vectors": json.dumps([
                {
                    "name": "N",
                    "description": "Normal force - N",
                    "tail": [2, 2],
                    "length": 4,
                    "angle": 45,
                    "render": False,
                    "expected_line_position": {"x1": 347, "y1": 181, "x2": 402, "y2": 125},
                    "expected_tail_position": {"cx": 347, "cy": 181},
                    "expected_tip_position": {"cx": 411, "cy": 117},
                }
            ]),
            "points": json.dumps([]),
            "expected_result": json.dumps({
                 "N": {"angle": 45, "tail": [2, 2]},
            })
        }
    )
    def test_correct_answer(self, params):
        # Logic for checking answer is covered by unit tests;
        # we are only checking UI behavior here.
        self.load_scenario("xml/custom.xml", params=params)
        board = self.exercise.find_element_by_css_selector("#jxgboard1")
        vectors = json.loads(params["vectors"])
        # Add vector
        self.add_vector(board, vectors)
        # Submit answer
        self.submit_answer()
        # Check status
        self.check_status()

    @data(
        {
            "show_vector_properties": True,
            "vectors": json.dumps([
                {
                    "name": "N",
                    "description": "Normal force - N",
                    "tail": [2, 2],
                    "length": 4,
                    "angle": 45,
                    "render": False,
                    "expected_line_position": {"x1": 347, "y1": 181, "x2": 402, "y2": 125},
                    "expected_tail_position": {"cx": 347, "cy": 181},
                    "expected_tip_position": {"cx": 411, "cy": 117},
                }
            ]),
            "points": json.dumps([]),
            "expected_result": json.dumps({
                 "N": {"angle": 110, "tail": [-0.6, 0.4]},
            })
        }
    )
    def test_incorrect_answer(self, params):
        # Logic for checking answer is covered by unit tests;
        # we are only checking UI behavior here.
        self.load_scenario("xml/custom.xml", params=params)
        board = self.exercise.find_element_by_css_selector("#jxgboard1")
        vectors = json.loads(params["vectors"])
        # Add vector
        self.add_vector(board, vectors)
        # Submit answer
        self.submit_answer()
        # Check status
        self.check_status(
            answer_correct=False, expected_message="Vector N does not start at correct point."
        )

    @data(
        {
            "show_vector_properties": True,
            "vectors": json.dumps([
                {
                    "name": "N",
                    "description": "Normal force - N",
                    "tail": [2, 2],
                    "length": 4,
                    "angle": 45,
                    "render": False,
                    "expected_line_position": {"x1": 347, "y1": 181, "x2": 402, "y2": 125},
                    "expected_tail_position": {"cx": 347, "cy": 181},
                    "expected_tip_position": {"cx": 411, "cy": 117},
                }
            ]),
            "points": json.dumps([]),
            "expected_result": json.dumps({
                 "N": {"angle": 45, "tail": [2, 2]},
            }),
            "answer_correct": True
        },
        {
            "show_vector_properties": True,
            "vectors": json.dumps([
                {
                    "name": "N",
                    "description": "Normal force - N",
                    "tail": [2, 2],
                    "length": 4,
                    "angle": 45,
                    "render": False,
                    "expected_line_position": {"x1": 347, "y1": 181, "x2": 402, "y2": 125},
                    "expected_tail_position": {"cx": 347, "cy": 181},
                    "expected_tip_position": {"cx": 411, "cy": 117},
                }
            ]),
            "points": json.dumps([]),
            "expected_result": json.dumps({
                 "N": {"angle": 110, "tail": [-0.6, 0.4]},
            }),
            "answer_correct": False
        }
    )
    def test_state(self, params):
        self.load_scenario("xml/custom.xml", params=params)
        board = self.exercise.find_element_by_css_selector("#jxgboard1")
        vectors = json.loads(params["vectors"])
        # Board should not show vector initially
        self.check_vectors(board, vectors)
        # Add vector
        self.add_vector(board, vectors)
        # Submit answer
        self.submit_answer()
        # Reload page
        self.element = self.go_to_view("student_view")
        self.exercise = self.element.find_element_by_css_selector(".vectordraw_block")
        board = self.exercise.find_element_by_css_selector("#jxgboard1")
        # Board should show vector
        vectors[0]["render"] = True
        self.check_vectors(board, vectors)
        # Status should show last result
        if params["answer_correct"]:
            self.check_status()
        else:
            self.check_status(
                answer_correct=False, expected_message="Vector N does not start at correct point."
            )
