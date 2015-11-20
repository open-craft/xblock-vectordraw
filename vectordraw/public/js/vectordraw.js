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
        this.element = $('#' + element_id);

        this.element.on('click', '.reset', this.reset.bind(this));
        this.element.on('click', '.add-vector', this.addElementFromList.bind(this));
        this.element.on('click', '.undo', this.undo.bind(this));
        this.element.on('click', '.redo', this.redo.bind(this));
        // Prevents default image drag and drop actions in some browsers.
        this.element.on('mousedown', '.jxgboard image', function(evt) { evt.preventDefault(); });

        this.render();
    };

    VectorDraw.prototype.render = function() {
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
            self.board.create('image', [bg.src, coords, [bg.width, height]], {fixed: true});
        }

        if (this.settings.background) {
            if (this.settings.background.height) {
                drawBackground(this.settings.background);
            }
            else {
                getImageRatio(this.settings.background, drawBackground);
            }
        }

        var noOptionSelected = true;

        function renderOrEnableOption(element, idx, type, board) {
            if (element.render) {
                if (type === 'point') {
                    board.renderPoint(idx);
                } else {
                    board.renderVector(idx);
                }
            } else {
                // Enable corresponding option in menu ...
                var option = board.getMenuOption(type, idx);
                option.prop('disabled', false);
                // ... and select it if no option is currently selected
                if (noOptionSelected) {
                    option.prop('selected', true);
                    noOptionSelected = false;
                }
            }
        }

        this.settings.points.forEach(function(point, idx) {
            renderOrEnableOption(point, idx, 'point', this);
        }, this);

        this.settings.vectors.forEach(function(vec, idx) {
            renderOrEnableOption(vec, idx, 'vector', this);
        }, this);

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
            var option = this.getMenuOption('point', idx);
            option.prop('disabled', true).prop('selected', false);
        }
    };

    VectorDraw.prototype.removePoint = function(idx) {
        var point = this.settings.points[idx];
        var object = this.board.elementsByName[point.name];
        if (object) {
            this.board.removeAncestors(object);
            // Enable the <option> element corresponding to point.
            var option = this.getMenuOption('point', idx);
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

    VectorDraw.prototype.getVectorStyle = function(vec) {
        //width, color, size of control point, label (which should be a JSXGraph option)
        var default_style = {
            pointSize: 1,
            pointColor: 'red',
            width: 4,
            color: "blue",
            label: null,
            labelColor: 'black'
        };

        return _.extend(default_style, vec.style);
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

        var line_type = (vec.type === 'vector') ? 'arrow' : vec.type;
        var line = this.board.create(line_type, [tail, tip], {
            name: vec.name,
            strokeWidth: style.width,
            strokeColor: style.color
        });

        tip.label.setAttribute({fontsize: 18, highlightStrokeColor: 'black'});

        // Disable the <option> element corresponding to vector.
        var option = this.getMenuOption('vector', idx);
        option.prop('disabled', true).prop('selected', false);

        return line;
    };

    VectorDraw.prototype.removeVector = function(idx) {
        var vec = this.settings.vectors[idx];
        var object = this.board.elementsByName[vec.name];
        if (object) {
            this.board.removeAncestors(object);
            // Enable the <option> element corresponding to vector.
            var option = this.getMenuOption('vector', idx);
            option.prop('disabled', false);
        }
    };

    VectorDraw.prototype.getMenuOption = function(type, idx) {
        return this.element.find('.menu option[value=' + type + '-' + idx + ']');
    };

    VectorDraw.prototype.getSelectedElement = function() {
        var selector = this.element.find('.menu select').val();
        if (selector) {
            selector = selector.split('-');
            return {
                type: selector[0],
                idx: parseInt(selector[1])
            };
        }
        return {};
    };

    VectorDraw.prototype.addElementFromList = function() {
        this.pushHistory();
        var selected = this.getSelectedElement();
        if (selected.type === 'vector') {
            this.updateVectorProperties(this.renderVector(selected.idx));
        } else {
            this.renderPoint(selected.idx);
        }
    };

    VectorDraw.prototype.reset = function() {
        this.pushHistory();
        JXG.JSXGraph.freeBoard(this.board);
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
        var slope = (y2-y1)/(x2-x1);
        var angle = ((Math.atan2(y2-y1, x2-x1)/Math.PI*180) - vec_settings.base_angle) % 360;
        if (angle < 0) {
            angle += 360;
        }
        $('.vector-prop-name .value', this.element).html(vector.point2.name); // labels are stored as point2 names
        $('.vector-prop-angle .value', this.element).html(angle.toFixed(2));
        if (vector.elType !== "line") {
            $('.vector-prop-length', this.element).show();
            $('.vector-prop-length .value', this.element).html(length.toFixed(2) + ' ' + vec_settings.length_units);
            $('.vector-prop-slope', this.element).hide();
        }
        else {
            $('.vector-prop-length', this.element).hide();
            if (this.settings.show_slope_for_lines) {
                $('.vector-prop-slope', this.element).show();
                $('.vector-prop-slope .value', this.element).html(slope.toFixed(2));
            }
        }
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

    VectorDraw.prototype.objectsUnderMouse = function(coords) {
        var filter = function(el) {
            return !(el instanceof JXG.Image) && el.hasPoint(coords.scrCoords[1], coords.scrCoords[2]);
        };
        return _.filter(_.values(this.board.objects), filter);
    };

    VectorDraw.prototype.onBoardDown = function(evt) {
        this.pushHistory();
        // Can't create a vector if none is selected from the list.
        var selected = this.getSelectedElement();
        var coords = this.getMouseCoords(evt);
        var targetObjects = this.objectsUnderMouse(coords);
        if (selected.idx && (!targetObjects || _.all(targetObjects, this.canCreateVectorOnTopOf.bind(this)))) {
            var point_coords = [coords.usrCoords[1], coords.usrCoords[2]];
            if (selected.type === 'vector') {
                this.drawMode = true;
                this.dragged_vector = this.renderVector(selected.idx, [point_coords, point_coords]);
            } else {
                this.renderPoint(selected.idx, point_coords);
            }
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
        this.drawMode = false;
        if (this.dragged_vector && !this.isVectorTailDraggable(this.dragged_vector)) {
            this.dragged_vector.point1.setProperty({fixed: true});
        }
        this.dragged_vector = null;
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
        this.settings.vectors.forEach(function(vec) {
            var coords = this.getVectorCoords(vec.name);
            if (coords) {
                vectors[vec.name] = coords;
            }
        }, this);
        this.settings.points.forEach(function(point) {
            var obj = this.board.elementsByName[point.name];
            if (obj) {
                points[point.name] = [obj.X(), obj.Y()];
            }
        }, this);
        return {vectors: vectors, points: points};
    };

    VectorDraw.prototype.setState = function(state) {
        this.settings.vectors.forEach(function(vec, idx) {
            var vec_state = state.vectors[vec.name];
            if (vec_state) {
                this.renderVector(idx, [vec_state.tail, vec_state.tip]);
            } else {
                this.removeVector(idx);
            }
        }, this);
        this.settings.points.forEach(function(point, idx) {
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

            [
                'tail', 'tail_x', 'tail_y', 'tip', 'tip_x', 'tip_y', 'coords',
                'length', 'angle', 'segment_angle', 'segment_coords', 'points_on_line'
            ].forEach(function(prop) {
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
        if (data.result.ok) {
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

    // Initialize exercise
    var vectordraw = new VectorDraw('vectordraw', init_args.settings);

    // Load user state
    if (!_.isEmpty(init_args.user_state)) {
        vectordraw.setState(init_args.user_state);
        updateStatus(init_args.user_state);
    }

    // Set up click handlers
    $('.action .check', element).on('click', function(e) { checkAnswer(vectordraw); });

}