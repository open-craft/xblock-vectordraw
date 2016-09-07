/* Javascript for VectorDrawXBlock. */
function VectorDrawXBlock(runtime, element, init_args) {
    'use strict';

    // Logic for rendering and interacting with vector drawing exercise

    var VectorDraw = function(element_id, settings) {
        this.board = null;
        this.dragged_vector = null;
        this.drawMode = false;
        this.history_stack = {undo: [], redo: []};
        this.settings = settings;
        this.element = $('#' + element_id, element);

        this.element.on('click', '.reset', this.reset.bind(this));
        this.element.on('click', '.add-vector', this.addElementFromList.bind(this));
        this.element.on('click', '.undo', this.undo.bind(this));
        this.element.on('click', '.redo', this.redo.bind(this));
        this.element.on('change', '.menu .element-list-edit', this.onEditStart.bind(this));
        this.element.on('click', '.menu .vector-prop-update', this.onEditSubmit.bind(this));
        // Prevents default image drag and drop actions in some browsers.
        this.element.on('mousedown', '.jxgboard image', function(evt) { evt.preventDefault(); });

        this.render();
    };

    VectorDraw.prototype.render = function() {
        $('.vector-prop-slope', this.element).hide();
        // Assign the jxgboard element a random unique ID,
        // because JXG.JSXGraph.initBoard needs it.
        this.element.find('.jxgboard').prop('id', _.uniqueId('jxgboard'));
        this.createBoard();
    };

    VectorDraw.prototype.createBoard = function() {
        var id = this.element.find('.jxgboard').prop('id'),
            self = this;

        this.board = JXG.JSXGraph.initBoard(id, {
            keepaspectratio: true,
            boundingbox: this.settings.bounding_box,
            axis: this.settings.axis,
            showCopyright: false,
            showNavigation: this.settings.show_navigation
        });

        function getImageRatio(bg, callback) {
            $('<img/>').attr('src', bg.src).load(function() {
                //technically it's inverse of ratio, but we need it to calculate height
                var ratio = this.height / this.width;
                callback(bg, ratio);
            });
        }

        function drawBackground(bg, ratio) {
            var height = (bg.height) ? bg.height : bg.width * ratio;
            var coords = (bg.coords) ? bg.coords : [-bg.width/2, -height/2];
            var image = self.board.create('image', [bg.src, coords, [bg.width, height]], {fixed: true});
            $(image.rendNode).attr('alt', bg.description);
        }

        if (this.settings.background) {
            if (this.settings.background.height) {
                drawBackground(this.settings.background);
            }
            else {
                getImageRatio(this.settings.background, drawBackground);
            }
        }

        function renderAndSetMenuOptions(element, idx, type, board) {
            if (element.render) {
                if (type === 'point') {
                    board.renderPoint(idx);
                } else {
                    board.renderVector(idx);
                }
            } else {
                // Enable corresponding option in menu for adding vectors ...
                var addOption = board.getAddMenuOption(type, idx);
                addOption.prop('disabled', false);
                // ... and select it if no option is currently selected
                if ($('.menu .element-list-add option').filter(':selected').length === 0) {
                    addOption.prop('selected', true);
                }
                // Disable corresponding option in menu for editing vectors
                var editOption = board.getEditMenuOption(type, idx);
                editOption.prop('disabled', true);
            }
        }

        // a11y

        // Generate and set unique ID for "Vector Properties";
        // this is necessary to ensure that "aria-describedby" associations
        // between vectors and the "Vector Properties" box don't break
        // when multiple boards are present:
        var vectorProperties = $(".vector-properties", element);
        vectorProperties.attr("id", id + "-vector-properties");

        // Draw vectors and points
        _.each(this.settings.points, function(point, idx) {
            renderAndSetMenuOptions(point, idx, 'point', this);
        }, this);

        _.each(this.settings.vectors, function(vec, idx) {
            renderAndSetMenuOptions(vec, idx, 'vector', this);
        }, this);

        // Set up event handlers
        this.board.on('down', this.onBoardDown.bind(this));
        this.board.on('move', this.onBoardMove.bind(this));
        this.board.on('up', this.onBoardUp.bind(this));
    };

    VectorDraw.prototype.renderPoint = function(idx, coords) {
        var point = this.settings.points[idx];
        var coords = coords || point.coords;
        var board_object = this.board.elementsByName[point.name];
        if (board_object) {
            // If the point is already rendered, only update its coordinates.
            board_object.setPosition(JXG.COORDS_BY_USER, coords);
            return;
        }
        this.board.create('point', coords, point.style);
        if (!point.fixed) {
            // Disable the <option> element corresponding to point.
            var option = this.getAddMenuOption('point', idx);
            option.prop('disabled', true).prop('selected', false);
        }
    };

    VectorDraw.prototype.removePoint = function(idx) {
        var point = this.settings.points[idx];
        var object = this.board.elementsByName[point.name];
        if (object) {
            this.board.removeAncestors(object);
            // Enable the <option> element corresponding to point.
            var option = this.getAddMenuOption('point', idx);
            option.prop('disabled', false);
        }
    };

    VectorDraw.prototype.getVectorCoordinates = function(vec) {
        var coords = vec.coords;
        if (!coords) {
            var tail = vec.tail || [0, 0];
            var length = 'length' in vec ? vec.length : 5;
            var angle = 'angle' in vec ? vec.angle : 30;
            var radians = angle * Math.PI / 180;
            var tip = [
                tail[0] + Math.cos(radians) * length,
                tail[1] + Math.sin(radians) * length
            ];
            coords = [tail, tip];
        }
        return coords;
    };

    VectorDraw.prototype.renderVector = function(idx, coords) {
        var vec = this.settings.vectors[idx];
        coords = coords || this.getVectorCoordinates(vec);

        // If this vector is already rendered, only update its coordinates.
        var board_object = this.board.elementsByName[vec.name];
        if (board_object) {
            board_object.point1.setPosition(JXG.COORDS_BY_USER, coords[0]);
            board_object.point2.setPosition(JXG.COORDS_BY_USER, coords[1]);
            return;
        }

        var style = vec.style;

        var tail = this.board.create('point', coords[0], {
            name: vec.name,
            size: style.pointSize,
            fillColor: style.pointColor,
            strokeColor: style.pointColor,
            withLabel: false,
            fixed: (vec.type === 'arrow' | vec.type === 'vector'),
            showInfoBox: false
        });
        var tip = this.board.create('point', coords[1], {
            name: style.label || vec.name,
            size: style.pointSize,
            fillColor: style.pointColor,
            strokeColor: style.pointColor,
            withLabel: true,
            showInfoBox: false
        });
        // Not sure why, but including labelColor in attributes above doesn't work,
        // it only works when set explicitly with setAttribute.
        tip.setAttribute({labelColor: style.labelColor});
        tip.label.setAttribute({fontsize: 18, highlightStrokeColor: 'black'});

        var line_type = (vec.type === 'vector') ? 'arrow' : vec.type;
        var line = this.board.create(line_type, [tail, tip], {
            name: vec.name,
            strokeWidth: style.width,
            strokeColor: style.color
        });

        // Disable the <option> element corresponding to vector.
        var option = this.getAddMenuOption('vector', idx);
        option.prop('disabled', true).prop('selected', false);

        // a11y

        var lineElement = $(line.rendNode);
        var lineID = lineElement.attr("id");

        var titleID = lineID + "-title";
        var titleElement = $("<title>", {"id": titleID, "text": vec.name});
        lineElement.append(titleElement);
        lineElement.attr("aria-labelledby", titleID);

        var vectorProperties = $(".vector-properties", element);
        lineElement.attr("aria-describedby", vectorProperties.attr("id"));

        return line;
    };

    VectorDraw.prototype.removeVector = function(idx) {
        var vec = this.settings.vectors[idx];
        var object = this.board.elementsByName[vec.name];
        if (object) {
            this.board.removeAncestors(object);
            // Enable the <option> element corresponding to vector.
            var option = this.getAddMenuOption('vector', idx);
            option.prop('disabled', false);
        }
    };

    VectorDraw.prototype.getAddMenuOption = function(type, idx) {
        return this.element.find('.menu .element-list-add option[value=' + type + '-' + idx + ']');
    };

    VectorDraw.prototype.getEditMenuOption = function(type, idx) {
        return this.element.find('.menu .element-list-edit option[value=' + type + '-' + idx + ']');
    };

    VectorDraw.prototype.getSelectedElement = function() {
        var selector = this.element.find('.menu .element-list-add').val();
        if (selector) {
            selector = selector.split('-');
            return {
                type: selector[0],
                idx: parseInt(selector[1], 10)
            };
        }
        return {};
    };

    VectorDraw.prototype.enableEditOption = function(selectedElement) {
        var editOption = this.getEditMenuOption(selectedElement.type, selectedElement.idx);
        editOption.prop('disabled', false);
    };

    VectorDraw.prototype.addElementFromList = function() {
        this.pushHistory();
        var selected = this.getSelectedElement();
        if (selected.type === 'vector') {
            this.updateVectorProperties(this.renderVector(selected.idx));
        } else {
            this.renderPoint(selected.idx);
        }
        // Enable option corresponding to selected element in menu for selecting element to edit
        this.enableEditOption(selected);
    };

    VectorDraw.prototype.reset = function() {
        this.pushHistory();
        JXG.JSXGraph.freeBoard(this.board);
        this.resetVectorProperties();
        this.render();
    };

    VectorDraw.prototype.pushHistory = function() {
        var state = this.getState();
        var previous_state = _.last(this.history_stack.undo);
        if (!_.isEqual(state, previous_state)) {
            this.history_stack.undo.push(state);
            this.history_stack.redo = [];
        }
    };

    VectorDraw.prototype.undo = function() {
        var curr_state = this.getState();
        var undo_state = this.history_stack.undo.pop();
        if (undo_state && !_.isEqual(undo_state, curr_state)) {
            this.history_stack.redo.push(curr_state);
            this.setState(undo_state);
        }
    };

    VectorDraw.prototype.redo = function() {
        var state = this.history_stack.redo.pop();
        if (state) {
            this.history_stack.undo.push(this.getState());
            this.setState(state);
        }
    };

    VectorDraw.prototype.getMouseCoords = function(evt) {
        var i = evt[JXG.touchProperty] ? 0 : undefined;
        var c_pos = this.board.getCoordsTopLeftCorner(evt, i);
        var abs_pos = JXG.getPosition(evt, i);
        var dx = abs_pos[0] - c_pos[0];
        var dy = abs_pos[1] - c_pos[1];

        return new JXG.Coords(JXG.COORDS_BY_SCREEN, [dx, dy], this.board);
    };

    VectorDraw.prototype.getVectorForObject = function(obj) {
        if (obj instanceof JXG.Line) {
            return obj;
        }
        if (obj instanceof JXG.Text) {
            return this.getVectorForObject(obj.element);
        }
        if (obj instanceof JXG.Point) {
            return _.find(obj.descendants, function (d) { return (d instanceof JXG.Line); });
        }
        return null;
    };

    VectorDraw.prototype.getVectorSettingsByName = function(name) {
        return _.find(this.settings.vectors, function(vec) {
            return vec.name === name;
        });
    };

    VectorDraw.prototype.updateVectorProperties = function(vector) {
        var vec_settings = this.getVectorSettingsByName(vector.name);
        var x1 = vector.point1.X(),
            y1 = vector.point1.Y(),
            x2 = vector.point2.X(),
            y2 = vector.point2.Y();
        var length = vec_settings.length_factor * Math.sqrt(Math.pow(x2-x1, 2) + Math.pow(y2-y1, 2));
        var angle = ((Math.atan2(y2-y1, x2-x1)/Math.PI*180) - vec_settings.base_angle) % 360;
        if (angle < 0) {
            angle += 360;
        }
        var slope = (y2-y1)/(x2-x1);
        // Update menu for selecting vector to edit
        this.element.find('.menu .element-list-edit option').attr('selected', false);
        var idx = _.indexOf(this.settings.vectors, vec_settings),
            editOption = this.getEditMenuOption("vector", idx);
        editOption.attr('selected', true);
        // Update properties
        $('.vector-prop-angle input', this.element).val(angle.toFixed(2));
        if (vector.elType !== "line") {
            var tailInput = x1.toFixed(2) + ", " + y1.toFixed(2);
            var lengthInput = length.toFixed(2);
            if (vec_settings.length_units) {
                lengthInput += ' ' + vec_settings.length_units;
            }
            $('.vector-prop-tail input', this.element).val(tailInput);
            $('.vector-prop-length', this.element).show();
            $('.vector-prop-length input', this.element).val(lengthInput);
            $('.vector-prop-slope', this.element).hide();
        }
        else {
            $('.vector-prop-length', this.element).hide();
            if (this.settings.show_slope_for_lines) {
                $('.vector-prop-slope', this.element).show();
                $('.vector-prop-slope input', this.element).val(slope.toFixed(2));
            }
        }
        // Enable input fields
        $('.vector-properties input').prop('disabled', false);
        // Enable buttons
        $('.vector-properties button').prop('disabled', false);
        // Hide error message
        $('.vector-prop-update .update-error', element).hide();
    };

    VectorDraw.prototype.resetVectorProperties = function(vector) {
        // Reset dropdown for selecting vector to default value
        $('.menu .element-list-edit option[value="-"]', element).attr('selected', true);
        // Reset input fields to default values and disable them
        $('.menu .vector-prop-list input', element).prop('disabled', true).val('');
        // Disable "Update" button
        $('.vector-properties button').prop('disabled', true);
    };

    VectorDraw.prototype.isVectorTailDraggable = function(vector) {
        return vector.elType !== 'arrow';
    };

    VectorDraw.prototype.canCreateVectorOnTopOf = function(el) {
        // If the user is trying to drag the arrow of an existing vector, we should not create a new vector.
        if (el instanceof JXG.Line) {
            return false;
        }
        // If this is tip/tail of a vector, it's going to have a descendant Line - we should not create a new vector
        // when over the tip. Creating on top of the tail is allowed for plain vectors but not for segments.
        // If it doesn't have a descendant Line, it's a point from settings.points - creating a new vector is allowed.
        if (el instanceof JXG.Point) {
            var vector = this.getVectorForObject(el);
            if (!vector) {
                return el.getProperty('fixed');
            } else if (el === vector.point1 && !this.isVectorTailDraggable(vector)) {
                return true;
            } else {
                return false;
            }
        }
        return true;
    };

    VectorDraw.prototype.objectsUnderMouse = function() {
        var targetObjects = [];
        var highlightedObjects = this.board.highlightedObjects
        var keys = Object.keys(highlightedObjects);
        for (var i = 0; i < keys.length; i++) {
            targetObjects.push( highlightedObjects[keys[i]] );
        }
        return targetObjects
    }

    // for disabling scroll http://stackoverflow.com/a/4770179/2747370
    VectorDraw.prototype.preventDefault = function(e) {
        // Run preventDefault() on the event if the browser supports it, otherwise return false.
        e = e || window.event;
        if (e.preventDefault){
            e.preventDefault();
        }
        e.returnValue = false;
    }

    VectorDraw.prototype.preventDefaultForScrollKeys = function(e) {
        // Prevent the default behavior (scrolling) when pressing the arrow keys.
        var keys = {37: 1, 38: 1, 39: 1, 40: 1};
        if (keys[e.keyCode]) {
            this.preventDefault(e);
            return false;
        }
    }

    VectorDraw.prototype.disableScroll = function() {
        // Disable scrolling until enable scrolling is called.
        var preventDefault = this.preventDefault;
        var preventDefaultForScrollKeys = this.preventDefaultForScrollKeys;
        if (window.addEventListener){ // older FF
            window.addEventListener('DOMMouseScroll', preventDefault, false);
        }
        window.onwheel = preventDefault; // modern standard
        window.onmousewheel = document.onmousewheel = preventDefault; // older browsers, IE
        window.ontouchmove  = preventDefault; // mobile
        document.onkeydown  = preventDefaultForScrollKeys;
    }

    VectorDraw.prototype.enableScroll = function() {
        // Enable scrolling (undo the changes of disableScroll).
        var preventDefault = this.preventDefault;
        if (window.removeEventListener){
            window.removeEventListener('DOMMouseScroll', preventDefault, false);
        }
        window.onmousewheel = document.onmousewheel = null;
        window.onwheel = null;
        window.ontouchmove = null;
        document.onkeydown = null;
    }

    VectorDraw.prototype.onBoardDown = function(evt) {
        this.pushHistory();
        // Can't create a vector if none is selected from the list.
        var selected = this.getSelectedElement();
        var coords = this.getMouseCoords(evt);
        var targetObjects = this.objectsUnderMouse();
        if (!_.isEmpty(selected) && (!targetObjects || _.all(targetObjects, this.canCreateVectorOnTopOf.bind(this)))) {
            var point_coords = [coords.usrCoords[1], coords.usrCoords[2]];
            if (selected.type === 'vector') {
                this.drawMode = true;
                this.disableScroll();
                this.dragged_vector = this.renderVector(selected.idx, [point_coords, point_coords]);
            } else {
                this.renderPoint(selected.idx, point_coords);
            }
            // Enable option corresponding to selected element in menu for selecting element to edit
            this.enableEditOption(selected);
        }
        else {
            this.drawMode = false;
            var vectorPoint = _.find(targetObjects, this.getVectorForObject.bind(this));
            if (vectorPoint) {
                this.dragged_vector = this.getVectorForObject(vectorPoint);
                this.dragged_vector.point1.setProperty({fixed: false});
                this.updateVectorProperties(this.dragged_vector);
            }
        }
    };

    VectorDraw.prototype.onBoardMove = function(evt) {
        if (this.drawMode) {
            var coords = this.getMouseCoords(evt);
            this.dragged_vector.point2.moveTo(coords.usrCoords);
        }
        if (this.dragged_vector) {
            this.updateVectorProperties(this.dragged_vector);
        }
    };

    VectorDraw.prototype.onBoardUp = function(evt) {
        this.enableScroll();
        this.drawMode = false;
        if (this.dragged_vector && !this.isVectorTailDraggable(this.dragged_vector)) {
            this.dragged_vector.point1.setProperty({fixed: true});
        }
        this.dragged_vector = null;
    };

    VectorDraw.prototype.onEditStart = function(evt) {
        var vectorName = $(evt.currentTarget).find('option:selected').data('vector-name');
        var vectorObject = this.board.elementsByName[vectorName];
        this.updateVectorProperties(vectorObject);
    };

    VectorDraw.prototype.onEditSubmit = function(evt) {
        // Get vector that is currently "selected"
        var vectorName = $('.element-list-edit', element).find('option:selected').data('vector-name');
        // Get values from input fields
        var newTail = $('.vector-prop-tail input', element).val(),
            newLength = $('.vector-prop-length input', element).val(),
            newAngle = $('.vector-prop-angle input', element).val();
        // Process values
        newTail = _.map(newTail.split(/ *, */), function(coord) {
            return parseFloat(coord);
        });
        newLength = parseFloat(newLength);
        newAngle = parseFloat(newAngle);
        var values = [newTail[0], newTail[1], newLength, newAngle];
        // Validate values
        if (!_.some(values, Number.isNaN)) {
            $('.vector-prop-update .update-error', element).hide();
            // Use coordinates of new tail, new length, new angle to calculate new position of tip
            var radians = newAngle * Math.PI / 180;
            var newTip = [
                newTail[0] + Math.cos(radians) * newLength,
                newTail[1] + Math.sin(radians) * newLength
            ];
            // Update position of vector
            var board_object = this.board.elementsByName[vectorName];
            board_object.point1.setPosition(JXG.COORDS_BY_USER, newTail);
            board_object.point2.setPosition(JXG.COORDS_BY_USER, newTip);
            this.board.update();
        } else {
            $('.vector-prop-update .update-error', element).show();
        }
    };

    VectorDraw.prototype.getVectorCoords = function(name) {
        var object = this.board.elementsByName[name];
        if (object) {
            return {
                tail: [object.point1.X(), object.point1.Y()],
                tip: [object.point2.X(), object.point2.Y()]
            };
        }
    };

    VectorDraw.prototype.getState = function() {
        var vectors = {}, points = {};
        _.each(this.settings.vectors, function(vec) {
            var coords = this.getVectorCoords(vec.name);
            if (coords) {
                vectors[vec.name] = coords;
            }
        }, this);
        _.each(this.settings.points, function(point) {
            var obj = this.board.elementsByName[point.name];
            if (obj) {
                points[point.name] = [obj.X(), obj.Y()];
            }
        }, this);
        return {vectors: vectors, points: points};
    };

    VectorDraw.prototype.setState = function(state) {
        _.each(this.settings.vectors, function(vec, idx) {
            var vec_state = state.vectors[vec.name];
            if (vec_state) {
                this.renderVector(idx, [vec_state.tail, vec_state.tip]);
            } else {
                this.removeVector(idx);
            }
        }, this);
        _.each(this.settings.points, function(point, idx) {
            var point_state = state.points[point.name];
            if (point_state) {
                this.renderPoint(idx, point_state);
            } else {
                this.removePoint(idx);
            }
        }, this);
        this.board.update();
    };

    // Logic for checking answers

    var checkHandlerUrl = runtime.handlerUrl(element, 'check_answer');

    var checkXHR;

    function getInput(vectordraw) {
        var input = vectordraw.getState();

        // Transform the expected_result setting into a list of checks.
        var checks = [];

        _.each(vectordraw.settings.expected_result, function(answer, name) {
            var presence_check = {vector: name, check: 'presence'};
            if ('presence_errmsg' in answer) {
                presence_check.errmsg = answer.presence_errmsg;
            }
            checks.push(presence_check);

            var properties = [
                'tail', 'tail_x', 'tail_y', 'tip', 'tip_x', 'tip_y', 'coords',
                'length', 'angle', 'segment_angle', 'segment_coords', 'points_on_line'
            ];
            _.each(properties, function(prop) {
                if (prop in answer) {
                    var check = {vector: name, check: prop, expected: answer[prop]};
                    if (prop + '_tolerance' in answer) {
                        check.tolerance = answer[prop + '_tolerance'];
                    }
                    if (prop + '_errmsg' in answer) {
                        check.errmsg = answer[prop + '_errmsg'];
                    }
                    checks.push(check);
                }
            });
        });

        input.checks = checks;

        return input;
    }

    function updateStatus(data) {
        var correctness = $('.correctness', element),
            correctClass = 'checkmark-correct fa fa-check',
            incorrectClass = 'checkmark-incorrect fa fa-times';
        if (data.result.correct) {
            correctness.removeClass(incorrectClass);
            correctness.addClass(correctClass);
        } else {
            correctness.removeClass(correctClass);
            correctness.addClass(incorrectClass);
        }
        $('.status-message', element).text(data.result.msg);
    }

    function checkAnswer(vectordraw) {
        if (checkXHR) {
            checkXHR.abort();
        }
        var state = getInput(vectordraw);
        checkXHR = $.post(checkHandlerUrl, JSON.stringify(state))
            .success(updateStatus);
    }

    // Initialization logic

    // Initialize exercise.
    // Defer it so that we don't try to initialize it for a hidden element (in Studio);
    // JSXGraph has problems rendering a board if the containing element is hidden.
    window.setTimeout(function() {
        var vectordraw = new VectorDraw('vectordraw', init_args.settings);

        // Load user state
        if (!_.isEmpty(init_args.user_state)) {
            vectordraw.setState(init_args.user_state);
            updateStatus(init_args.user_state);
        }

        // Set up click handlers
        $('.action .check', element).on('click', function(e) { checkAnswer(vectordraw); });
    }, 0);

}
