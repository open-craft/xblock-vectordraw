from __future__ import absolute_import

import json

from ddt import ddt, data
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from six.moves import zip
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable_test import StudioEditableBaseTest

loader = ResourceLoader(__name__)  # pylint: disable=invalid-name


@ddt
class TestVectorDraw(StudioEditableBaseTest):
    """
    Test student view of VectorDrawXBlock.
    """

    def setUp(self):
        super(TestVectorDraw, self).setUp()
        self.driver.implicitly_wait(3)

    def load_scenario(self, path, params=None):
        scenario = loader.render_django_template(path, params)
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

    def assert_hidden_text(self, selector, expected_text):
        hidden_text = self.browser.execute_script("return $('{}').text();".format(selector))
        self.assertEquals(hidden_text, expected_text)

    def assert_title_and_description(self, expected_title="Vector Drawing", expected_description=None):
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

    def assert_dimensions(self, board, expected_width="550px", expected_height="400px"):
        width = board.value_of_css_property("width")
        height = board.value_of_css_property("height")
        self.assertEquals(width, expected_width)
        self.assertEquals(height, expected_height)

    def assert_axis(self, board, is_present=False):
        text_elements = board.find_elements_by_css_selector(".JXGtext")
        ticks = any("ticks" in text_element.get_attribute("id") for text_element in text_elements)
        self.assertEquals(ticks, is_present)

    def assert_navigation_bar(self, board, is_present=False):
        if is_present:
            navigation_bar = board.find_element_by_css_selector("#jxgboard1_navigationbar")
            self.assertTrue(navigation_bar.is_displayed())
        else:
            self.assert_not_present(
                board,
                "#jxgboard1_navigationbar",
                "Navigation bar should be hidden by default."
            )

    def assert_background(self, board, is_present=False):
        if is_present:
            wait = WebDriverWait(board, self.timeout)
            wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "image")),
                'Timeout while waiting for "image" element.'
            )
            background = board.find_element_by_css_selector("image")
            self.assertTrue(background.is_displayed())
            src = background.get_attribute("xlink:href")
            self.assertEquals(src, "https://github.com/open-craft/jsinput-vectordraw/raw/master/Notes_and_Examples/2_boxIncline_multiVector/box_on_incline.png")
            alt = background.get_attribute("alt")
            self.assertEquals(alt, "A very informative description")
        else:
            self.assert_not_present(
                board,
                "image",
                "Board should not contain background image by default."
            )

    def assert_buttons(self, controls, add_vector_label="Add Selected Force"):
        # "Add vector" button
        add_vector = controls.find_element_by_css_selector(".add-vector")
        self.assertEquals(add_vector.text, add_vector_label)
        # "Reset" button
        reset = controls.find_element_by_css_selector(".reset")
        reset_label = reset.find_element_by_css_selector('.reset-label')
        self.assertEquals(reset_label.text, "Reset")
        reset.find_element_by_css_selector(".sr")
        self.assert_hidden_text(".reset > .sr", "Reset board to initial state")
        # "Redo" button
        redo = controls.find_element_by_css_selector(".redo")
        redo.find_element_by_css_selector(".fa.fa-repeat")
        redo.find_element_by_css_selector(".sr")
        self.assert_hidden_text(".redo > .sr", "Redo last action")
        # "Undo" button
        undo = controls.find_element_by_css_selector(".undo")
        undo.find_element_by_css_selector(".fa.fa-undo")
        undo.find_element_by_css_selector(".sr")
        self.assert_hidden_text(".undo > .sr", "Undo last action")

    def assert_vector_properties(
            self, menu, is_present=False, expected_label="Vector Properties",
            expected_name=None, expected_tail=None, expected_length=None, expected_angle=None,
            input_fields_disabled=True
    ):
        if is_present:
            vector_properties = menu.find_element_by_css_selector(".vector-properties")
            vector_properties_label = vector_properties.find_element_by_css_selector("h3")
            self.assertEquals(vector_properties_label.text, expected_label)
            # Name
            self.assert_vector_property(
                vector_properties, "name", "select", "name:", expected_name or "-",
                field_disabled=input_fields_disabled
            )
            # Tail
            self.assert_vector_property(
                vector_properties, "tail", "input", "tail position:", expected_tail or "",
                field_disabled=input_fields_disabled
            )
            # Length
            self.assert_vector_property(
                vector_properties, "length", "input", "length:", expected_length or "",
                field_disabled=input_fields_disabled
            )
            # Angle
            self.assert_vector_property(
                vector_properties, "angle", "input", "angle:", expected_angle or "",
                field_disabled=input_fields_disabled
            )
            # Slope
            vector_slope = vector_properties.find_element_by_css_selector(".vector-prop-slope")
            self.assertFalse(vector_slope.is_displayed())
            # "Update" button
            update_button = vector_properties.find_element_by_css_selector('button.update')
            update_button_disabled = update_button.get_attribute('disabled')
            self.assertEquals(bool(update_button_disabled), input_fields_disabled)
        else:
            self.assert_not_present(
                menu,
                ".vector-properties",
                "If show_vector_properties is set to False, menu should not show vector properties."
            )

    def assert_vector_property(
            self, vector_properties, property_name, input_type, expected_label, expected_value=None,
            field_disabled=False
    ):
        vector_property = vector_properties.find_element_by_css_selector(
            ".vector-prop-{}".format(property_name)
        )
        vector_property_label = vector_property.find_element_by_css_selector(
            "#vector-prop-{}-label".format(property_name)
        )
        self.assertEquals(vector_property_label.text, expected_label)
        vector_property_input = vector_property.find_element_by_css_selector(input_type)
        self.assertEquals(
            vector_property_input.get_attribute("aria-labelledby"), "vector-prop-{}-label".format(property_name)
        )
        if input_type == "input":
            self.assertEquals(vector_property_input.get_attribute("value"), expected_value)
            disabled = vector_property_input.get_attribute("disabled")
            self.assertEquals(bool(disabled), field_disabled)
        else:
            selected_option = vector_property_input.find_element_by_css_selector('option[selected="selected"]')
            self.assertEquals(selected_option.text, expected_value)

    def assert_actions(self):
        actions = self.exercise.find_element_by_css_selector(".action")
        self.assertTrue(actions.is_displayed())
        check = actions.find_element_by_css_selector(".check")
        check_label = check.find_element_by_css_selector(".check-label")
        self.assertEquals(check_label.text, "CHECK")
        check.find_element_by_css_selector(".sr")
        self.assert_hidden_text(".check > .sr", "Check your answer")

    def assert_add_dropdown(self, controls, vectors=[], points=[]):
        # Check dropdown
        dropdown = controls.find_element_by_css_selector("select")
        if not vectors and not points:
            self.assert_not_present(
                dropdown,
                "option",
                "Dropdown should not list any vectors or points by default."
            )
        else:
            self.assert_add_options(dropdown, vectors, "vector")
            non_fixed_points = [point for point in points if not point["fixed"]]
            self.assert_add_options(dropdown, non_fixed_points, "point")
        # Check label
        label_selector = "label.sr"
        select_label = controls.find_element_by_css_selector(label_selector)
        self.assert_hidden_text(label_selector, "Select element to add to board")
        select_id = "element-list"
        self.assertEquals(select_label.get_attribute("for"), select_id)

    def assert_add_options(self, dropdown, elements, element_type):
        element_options = dropdown.find_elements_by_css_selector('option[value^="{}-"]'.format(element_type))
        self.assertEquals(len(element_options), len(elements))
        for element, element_option in zip(elements, element_options):
            self.assertEquals(element_option.text, element["description"])
            option_disabled = element_option.get_attribute("disabled")
            self.assertEquals(bool(option_disabled), element["render"])

    def assert_edit_dropdown(self, menu, vectors=[], points=[]):
        vector_properties = menu.find_element_by_css_selector(".vector-properties")
        # Check dropdown
        dropdown = vector_properties.find_element_by_css_selector("select")
        if not vectors and not points:
            options = dropdown.find_elements_by_css_selector("option")
            self.assertEquals(len(options), 1)
            default_option = options[0]
            self.assertEquals(default_option.get_attribute("value"), "-")
        else:
            if vectors:
                self.assert_edit_options(dropdown, vectors, "vector")
            if points:
                non_fixed_points = [point for point in points if not point["fixed"]]
                self.assert_edit_options(dropdown, non_fixed_points, "point")

    def assert_edit_options(self, dropdown, elements, element_type):
        element_options = dropdown.find_elements_by_css_selector('option[value^="{}-"]'.format(element_type))
        self.assertEquals(len(element_options), len(elements))
        for element, element_option in zip(elements, element_options):
            self.assertEquals(element_option.text, element["name"])
            option_disabled = element_option.get_attribute("disabled")
            self.assertNotEquals(bool(option_disabled), element["render"])

    def assert_vectors(self, board, vectors):
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

    def assert_points(self, board, points):
        point_elements = board.find_elements_by_css_selector("ellipse")
        for point in points:
            board_has_point = self.board_has_point(point["expected_position"], point_elements)
            self.assertEquals(board_has_point, point["render"])

    def board_has_line(self, position, line_elements):
        line = self.find_line(position, line_elements)
        return bool(line) and self.line_has_title(line) and self.line_has_desc(line)

    def board_has_point(self, position, point_elements):
        return bool(self.find_point(position, point_elements))

    def board_has_label(self, board, label_text):
        text_elements = board.find_elements_by_css_selector(".JXGtext")
        for text_element in text_elements:
            is_tick = "ticks" in text_element.get_attribute("id")
            if not is_tick and text_element.text == label_text:
                return True
        return False

    def line_has_title(self, line):
        title = line.find_element_by_css_selector("title")
        title_id = title.get_attribute("id")
        aria_labelledby = line.get_attribute("aria-labelledby")
        return title_id == aria_labelledby

    def line_has_desc(self, line):
        aria_describedby = line.get_attribute("aria-describedby")
        return aria_describedby == "jxgboard1-vector-properties"

    def find_line(self, expected_line_position, line_elements):
        for line in line_elements:
            line_position = {
                "x1": int(line.get_attribute("x1").split(".", 1)[0]),
                "y1": int(line.get_attribute("y1").split(".", 1)[0]),
                "x2": int(line.get_attribute("x2").split(".", 1)[0]),
                "y2": int(line.get_attribute("y2").split(".", 1)[0]),
            }
            if line_position == expected_line_position:
                return line

    def find_point(self, expected_position, point_elements):
        for point in point_elements:
            point_position = {
                "cx": int(point.get_attribute("cx").split(".", 1)[0]),
                "cy": int(point.get_attribute("cy").split(".", 1)[0]),
            }
            if point_position == expected_position:
                return point

    def add_vector(self, board, vectors):
        menu = self.exercise.find_element_by_css_selector(".menu")
        controls = menu.find_element_by_css_selector(".controls")
        add_vector = controls.find_element_by_css_selector(".add-vector")
        add_vector.click()
        # Board should now show vector
        vectors[0]["render"] = True
        self.assert_vectors(board, vectors)
        # "Vector Properties" should display correct info
        self.assert_vector_properties(
            menu, is_present=True, expected_label="Custom properties label",
            expected_name="N", expected_tail="2.00, 2.00", expected_length="4.00", expected_angle="45.00",
            input_fields_disabled=False
        )
        self.assert_edit_dropdown(menu, vectors)

    def add_point(self, board, points):
        menu = self.exercise.find_element_by_css_selector(".menu")
        controls = menu.find_element_by_css_selector(".controls")
        add_vector = controls.find_element_by_css_selector(".add-vector")
        add_vector.click()
        # Board should now show point
        points[0]["render"] = True
        self.assert_points(board, points)

    def undo(self, board, vectors):
        menu = self.exercise.find_element_by_css_selector(".menu")
        controls = menu.find_element_by_css_selector(".controls")
        undo = controls.find_element_by_css_selector(".undo")
        undo.click()
        # Board should not show vector anymore
        vectors[0]["render"] = False
        self.assert_vectors(board, vectors)

    def redo(self, board, vectors):
        menu = self.exercise.find_element_by_css_selector(".menu")
        controls = menu.find_element_by_css_selector(".controls")
        redo = controls.find_element_by_css_selector(".redo")
        redo.click()
        # Board should now show vector
        vectors[0]["render"] = True
        self.assert_vectors(board, vectors)
        # "Vector Properties" should display correct info
        self.assert_vector_properties(
            menu, is_present=True, expected_label="Custom properties label",
            expected_name="N", expected_tail="2.00, 2.00", expected_length="4.00", expected_angle="45.00",
            input_fields_disabled=False
        )

    def reset(self, board, vectors, points):
        menu = self.exercise.find_element_by_css_selector(".menu")
        controls = menu.find_element_by_css_selector(".controls")
        reset = controls.find_element_by_css_selector(".reset")
        reset.click()
        # Board should not show vector anymore
        vectors[0]["render"] = False
        self.assert_vectors(board, vectors)
        # Board should not show point anymore
        points[0]["render"] = False
        self.assert_points(board, points)

    def submit_answer(self):
        actions = self.exercise.find_element_by_css_selector(".action")
        check = actions.find_element_by_css_selector(".check")
        check.click()

    def assert_status(self, answer_correct=True, expected_message="Test passed"):
        status = self.exercise.find_element_by_css_selector(".vectordraw-status")
        self.assertTrue(status.is_displayed())
        correctness = status.find_element_by_css_selector(".correctness")
        if answer_correct:
            self.assertIn("checkmark-correct fa fa-check", correctness.get_attribute("class"))
        else:
            self.assertIn("checkmark-incorrect fa fa-times", correctness.get_attribute("class"))
        status_message = status.find_element_by_css_selector(".status-message")
        self.assertEquals(status_message.text, expected_message)

    def change_property(self, property_name, new_value):
        menu = self.exercise.find_element_by_css_selector(".menu")
        vector_properties = menu.find_element_by_css_selector(".vector-properties")
        vector_property = vector_properties.find_element_by_css_selector(
            ".vector-prop-{}".format(property_name)
        )
        vector_property_input = vector_property.find_element_by_css_selector("input")
        # Enter new value
        vector_property_input.clear()
        vector_property_input.send_keys(new_value)
        # Find "Update" button
        update_button = vector_properties.find_element_by_css_selector(".vector-prop-update")
        # Click "Update" button
        update_button.click()

    def test_defaults(self):
        self.load_scenario("xml/defaults.xml")

        # Check title and description
        self.assert_title_and_description()

        # Check board
        board = self.exercise.find_element_by_css_selector("#jxgboard1")
        self.assert_dimensions(board)
        self.assert_axis(board, is_present=True)
        self.assert_navigation_bar(board)
        self.assert_background(board)
        # - Vectors
        self.assert_not_present(
            board,
            "line[aria-labelledby]",  # axes (which are present by default) don't have aria-labelledby attribute
            "Board should not contain any vectors or lines by default."
        )
        # - Points
        self.assert_not_present(
            board,
            "ellipse:not([display])",  # points don't have in-line "display" property
            "Board should not contain any points by default."
        )

        # Check menu
        menu = self.exercise.find_element_by_css_selector(".menu")
        controls = menu.find_element_by_css_selector(".controls")
        self.assert_add_dropdown(controls)
        self.assert_buttons(controls)
        self.assert_vector_properties(menu, is_present=True)
        self.assert_edit_dropdown(menu)

        # Check actions
        self.assert_actions()

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
        self.assert_title_and_description(
            expected_title="Custom Exercise", expected_description="Custom exercise description"
        )

        # Check board
        board = self.exercise.find_element_by_css_selector("#jxgboard1")
        self.assert_dimensions(board, expected_width="600px", expected_height="450px")
        self.assert_axis(board)
        self.assert_navigation_bar(board, is_present=True)
        self.assert_background(board, is_present=True)
        # - Vectors
        self.assert_vectors(board, vectors)
        # - Points
        self.assert_points(board, points)

        # Check menu
        menu = self.exercise.find_element_by_css_selector(".menu")
        controls = menu.find_element_by_css_selector(".controls")
        self.assert_add_dropdown(controls, vectors, points)
        self.assert_buttons(controls, add_vector_label="Custom button label")
        show_vector_properties = params["show_vector_properties"]
        if show_vector_properties:
            self.assert_vector_properties(menu, is_present=True, expected_label="Custom properties label")
            self.assert_edit_dropdown(menu, vectors, points)
        else:
            self.assert_vector_properties(menu)

        # Check actions
        self.assert_actions()

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
            elem = self.find_line(vector["expected_line_position"], line_elements)
        elif click_target == "tail":
            # Find tail and click it
            point_elements = board.find_elements_by_css_selector("ellipse")
            elem = self.find_point(vector["expected_tail_position"], point_elements)
        else:
            # Find tip and click it
            point_elements = board.find_elements_by_css_selector("ellipse")
            elem = self.find_point(vector["expected_tip_position"], point_elements)

        # XXX: potential a11y issue here. Clicking on the vector parts to
        # activate the action only works if hovering with the cursor before
        # clicking. This could prevent keyboard-only use.
        hover = ActionChains(self.driver)
        hover.move_to_element(elem).perform()
        elem.click()

        # Check if "Vector Properties" shows correct info
        menu = self.exercise.find_element_by_css_selector(".menu")
        self.assert_vector_properties(
            menu, is_present=True, expected_label="Custom properties label",
            expected_name="N", expected_tail="2.00, 2.00", expected_length="4.00", expected_angle="45.00",
            input_fields_disabled=False
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
        self.assert_vectors(board, vectors)
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
        self.assert_points(board, points)
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
        self.assert_vectors(board, vectors)
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
        self.assert_vectors(board, vectors)
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
        self.assert_vectors(board, vectors)
        # Board should not show point initially
        points = json.loads(params["points"])
        self.assert_points(board, points)
        # Add vector
        self.add_vector(board, vectors)
        # Add point
        self.add_point(board, points)
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
        self.assert_status()

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
        self.assert_status(
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
        self.assert_vectors(board, vectors)
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
        self.assert_vectors(board, vectors)
        # Status should show last result
        if params["answer_correct"]:
            self.assert_status()
        else:
            self.assert_status(
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
            "expected_result": json.dumps({})
        }
    )
    def test_change_tail_property(self, params):
        self.load_scenario("xml/custom.xml", params=params)
        board = self.exercise.find_element_by_css_selector("#jxgboard1")
        # Board should not show vector initially
        vectors = json.loads(params["vectors"])
        self.assert_vectors(board, vectors)
        # Add vector
        self.add_vector(board, vectors)
        # Change tail
        self.change_property("tail", "3, 3")
        # Check new position: Tail updated, tip updated
        vectors[0]["expected_line_position"] = {'x1': 370, 'y1': 159, 'x2': 425, 'y2': 102}
        vectors[0]["expected_tail_position"] = {'cx': 369, 'cy': 158}
        vectors[0]["expected_tip_position"] = {'cx': 434, 'cy': 94}
        self.assert_vectors(board, vectors)

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
    def test_change_length_property(self, params):
        self.load_scenario("xml/custom.xml", params=params)
        board = self.exercise.find_element_by_css_selector("#jxgboard1")
        # Board should not show vector initially
        vectors = json.loads(params["vectors"])
        self.assert_vectors(board, vectors)
        # Add vector
        self.add_vector(board, vectors)
        # Change tail
        self.change_property("length", "6")
        # Check new position: Tail unchanged, tip updated
        vectors[0]["expected_line_position"] = {'x1': 347, 'y1': 181, 'x2': 434, 'y2': 93}
        vectors[0]["expected_tail_position"] = {'cx': 347, 'cy': 181}
        vectors[0]["expected_tip_position"] = {'cx': 443, 'cy': 85}
        self.assert_vectors(board, vectors)

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
    def test_change_angle_property(self, params):
        self.load_scenario("xml/custom.xml", params=params)
        board = self.exercise.find_element_by_css_selector("#jxgboard1")
        # Board should not show vector initially
        vectors = json.loads(params["vectors"])
        self.assert_vectors(board, vectors)
        # Add vector
        self.add_vector(board, vectors)
        # Change tail
        self.change_property("angle", "170")
        # Check new position: Tail unchanged, tip updated
        vectors[0]["expected_line_position"] = {'x1': 347, 'y1': 181, 'x2': 269, 'y2': 167}
        vectors[0]["expected_tail_position"] = {'cx': 347, 'cy': 181}
        vectors[0]["expected_tip_position"] = {'cx': 258, 'cy': 165}
        self.assert_vectors(board, vectors)

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
    def test_change_property_invalid_input(self, params):
        self.load_scenario("xml/custom.xml", params=params)
        board = self.exercise.find_element_by_css_selector("#jxgboard1")
        # Board should not show vector initially
        vectors = json.loads(params["vectors"])
        self.assert_vectors(board, vectors)
        # Add vector
        self.add_vector(board, vectors)
        # Change tail
        self.change_property("tail", "invalid")
        # Check new position: Tail unchanged, tip unchanged
        vectors[0]["expected_line_position"] = {'x1': 347, 'y1': 181, 'x2': 402, 'y2': 125}
        vectors[0]["expected_tail_position"] = {'cx': 347, 'cy': 181}
        vectors[0]["expected_tip_position"] = {'cx': 411, 'cy': 117}
        self.assert_vectors(board, vectors)
        # Check error message
        error_message = self.exercise.find_element_by_css_selector(".update-error");
        self.wait_until_visible(error_message)
        self.assertEquals(error_message.text, "Invalid input.")
