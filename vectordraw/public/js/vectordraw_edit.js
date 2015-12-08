function VectorDrawXBlockEdit(runtime, element, init_args) {
    'use strict';

    var VectorDraw = function(element_id, settings) {
        this.board = null;
        this.dragged_vector = null;
        this.selectedVector = null;
        this.drawMode = false;
        this.wasUsed = false;
        this.resultMode = false;
        this.settings = settings;
        this.numberOfVectors = this.settings.vectors.length;
        this.editableProperties = ['name', 'label', 'tail', 'length', 'angle'];
        this.checks = [
            'tail', 'tail_x', 'tail_y', 'tip', 'tip_x', 'tip_y', 'coords', 'length', 'angle'
        ];
        this.element = $('#' + element_id, element);

        this.element.on('click', '.controls .add-vector', this.onAddVector.bind(this));
        this.element.on('click', '.controls .result-mode', this.onEditResult.bind(this));
        this.element.on('change', '.menu .element-list-edit', this.onEditStart.bind(this));
        this.element.on('click', '.menu .update', this.onEditSubmit.bind(this));
        this.element.on('click', '.menu .remove', this.onRemoveVector.bind(this));
        // Prevents default image drag and drop actions in some browsers.
        this.element.on('mousedown', '.jxgboard image', function(evt) { evt.preventDefault(); });

        this.discardStaleData();
        this.render();
    };

    VectorDraw.prototype.discardStaleData = function() {
        // If author removed or renamed vectors via the "Vectors" field
        // (without making necessary adjustments in "Expected results" field)
        // discard stale information about expected positions and checks
        var vectorData = JSON.parse(fieldEditor.getContents('vectors')),
            vectorNames = this.getVectorNames(vectorData);
        var isStale = function(key) { return !_.contains(vectorNames, key); };
        this.settings.expected_result_positions = _.omit(this.settings.expected_result_positions, isStale);
        this.settings.expected_result = _.omit(this.settings.expected_result, isStale);
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
            var img = new Image();

            $(img).load(function() {
                var ratio = this.height / this.width;
                callback(bg, ratio);
            }).attr({
                src: bg.src
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

        _.each(this.settings.points, function(point, idx) {
            this.renderPoint(idx);
        }, this);

        _.each(this.settings.vectors, function(vec, idx) {
            this.renderVector(idx);
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
    };

    VectorDraw.prototype.getVectorNames = function(vectorData) {
        if (vectorData) {
            return _.pluck(vectorData, 'name');
        }
        return _.pluck(this.settings.vectors, 'name');
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

        // a11y

        var lineElement = $(line.rendNode);
        var lineID = lineElement.attr("id");

        var titleID = lineID + "-title";
        var titleElement = $("<title>", {"id": titleID, "text": vec.name});
        lineElement.append(titleElement);
        lineElement.attr("aria-labelledby", titleID);

        var descID = lineID + "-desc";
        var descElement = $("<desc>").attr("id", descID).text(vec.description);
        lineElement.append(descElement);
        lineElement.attr("aria-describedby", descID);

        return line;
    };

    VectorDraw.prototype.getEditMenuOption = function(type, idx) {
        return this.element.find('.menu .element-list-edit option[value=' + type + '-' + idx + ']');
    };

    VectorDraw.prototype.onAddVector = function(evt) {
        if (!this.wasUsed) {
            this.wasUsed = true;
        }
        // Add vector that starts at center of board and has a predefined length and angle
        var defaultCoords = [[0, 0], [0, 3]],
            defaultVector = this.getDefaultVector(defaultCoords);
        this.settings.vectors.push(defaultVector);
        var lastIndex = this.numberOfVectors - 1,
            vector = this.renderVector(lastIndex);
        this.addEditMenuOption(defaultVector.name, lastIndex);
        this.updateVectorProperties(vector);
    };

    VectorDraw.prototype.addEditMenuOption = function(vectorName, idx) {
        // Find dropdown for selecting vector to edit
        var editMenu = this.element.find('.menu .element-list-edit');
        // Remove current selection(s)
        editMenu.find('option').attr('selected', false);
        // Create option for newly added vector
        var newOption = $('<option>')
            .attr('value', 'vector-' + idx)
            .attr('data-vector-name', vectorName)
            .text(vectorName);
        // Append option to dropdown
        editMenu.append(newOption);
        // Select newly added option
        newOption.attr('selected', true);
    };

    VectorDraw.prototype.onRemoveVector = function(evt) {
        if (!this.wasUsed) {
            this.wasUsed = true;
        }
        // Remove selected vector from board
        var vectorName = $('.element-list-edit', element).find('option:selected').data('vector-name');
        var boardObject = this.board.elementsByName[vectorName];
        this.board.removeAncestors(boardObject);
        // Mark vector as "deleted" so it will be removed from "vectors" field on save
        var vectorSettings = this.getVectorSettingsByName(String(vectorName));
        vectorSettings.deleted = true;
        // Remove entry that corresponds to selected vector from menu for selecting vector to edit
        var idx = _.indexOf(this.settings.vectors, vectorSettings),
            editOption = this.getEditMenuOption("vector", idx);
        editOption.remove();
        // Discard information about expected position (if any)
        delete this.settings.expected_result_positions[vectorName];
        // Discard information about expected result (if any)
        delete this.settings.expected_result[vectorName];
        // Reset input fields for vector properties to default values
        this.resetVectorProperties();
        // Reset selected vector
        this.selectedVector = null;
        // Hide message about pending changes
        $('.vector-prop-update .update-pending', element).hide();
    };

    VectorDraw.prototype.onEditResult = function(evt) {
        // Switch to result mode
        this.resultMode = true;
        // Save vector positions
        this.settings.vectors = this.getState();  // Discards vectors that were removed from board
        // Vector positions saved, so hide message about pending changes
        this.selectedVector = null;
        $('.vector-prop-update .update-pending', element).hide();
        // Update vector positions using positions from expected result
        var expectedResultPositions = this.settings.expected_result_positions;
        if (!_.isEmpty(expectedResultPositions)) {
            _.each(this.settings.vectors, function(vec) {
                var vectorName = vec.name,
                    resultPosition = expectedResultPositions[vectorName];
                if (resultPosition) {
                    var resultTail = resultPosition.tail,
                        resultTip = resultPosition.tip,
                        boardObject = this.board.elementsByName[vectorName];
                    boardObject.point1.setPosition(JXG.COORDS_BY_USER, resultTail);
                    boardObject.point2.setPosition(JXG.COORDS_BY_USER, resultTip);
                }
            }, this);
            this.board.update();
        }
        // Hide or disable buttons for operations that are specific to defining initial state
        $(evt.currentTarget).prop('disabled', true);
        $('.add-vector', element).css('visibility', 'hidden');
        $('.vector-remove button').hide();
        // Reset vector properties to ensure a clean slate
        this.resetVectorProperties();
        // Show controls for opting in and out of checks
        $('.checks', element).show();
    };

    VectorDraw.prototype.resetVectorProperties = function(vector) {
        // Reset dropdown for selecting vector to default value
        $('.element-list-edit option[value="-"]', element).attr('selected', true);
        // Reset input fields and disable them
        // (users should not be able to interact with them unless a vector is selected)
        _.each(this.editableProperties, function(propName) {
            $('.vector-prop-' + propName + ' input', element).prop('disabled', true).val('');
        });
        // Disable buttons
        $('.vector-properties button').prop('disabled', true);
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
        // If user selected different vector, hide message about pending changes
        if (this.selectedVector && vector.name !== this.selectedVector.name) {
            $('.vector-prop-update .update-pending', element).hide();
        }
        // Update selected vector
        this.selectedVector = vector;
        // Update menu for selecting vector to edit
        this.element.find('.menu .element-list-edit option').attr('selected', false);
        var idx = _.indexOf(this.settings.vectors, vec_settings),
            editOption = this.getEditMenuOption("vector", idx);
        editOption.attr('selected', true);
        // Update properties
        $('.vector-prop-name input', this.element).val(vector.name);
        $('.vector-prop-label input', this.element).val(vec_settings.style.label || '');
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
        }
        else {
            $('.vector-prop-length', this.element).hide();
        }
        // Enable input fields
        $('.vector-properties input').prop('disabled', false);
        // Enable buttons
        $('.vector-properties button').prop('disabled', false);
    };

    VectorDraw.prototype.updateChecks = function(vector) {
        var expectedResult = this.settings.expected_result[vector.name] || {};
        _.each(this.checks, function(check) {
            var checkElement = $('#check-' + check, element);
            // Update checkbox
            if (expectedResult[check]) {
                checkElement.find('input[type="checkbox"]').prop('checked', true);
            } else {
                checkElement.find('input[type="checkbox"]').prop('checked', false);
            }
            // Update tolerance
            var tolerance = expectedResult[check + '_tolerance'];
            if (tolerance) {
                checkElement.find('input[type="number"]').val(tolerance.toFixed(1));
            } else {
                var defaultTolerance = check === 'angle' ? 2.0 : 1.0;
                checkElement.find('input[type="number"]').val(defaultTolerance.toFixed(1));
            }
        });
    };

    VectorDraw.prototype.saveExpectedPosition = function(vectorName, coords, length, angle) {
        var expectedPosition = {
            coords: coords,
            tail: coords[0],
            tip: coords[1],
            tail_x: coords[0][0],
            tail_y: coords[0][1],
            tip_x: coords[1][0],
            tip_y: coords[1][1],
            length: length,
            angle: angle
        };
        this.settings.expected_result_positions[vectorName] = expectedPosition;
    };

    VectorDraw.prototype.saveChecks = function(vectorName) {
        var expectedResult = {};
        _.each(this.checks, function(check) {
            var checkElement = $('#check-' + check, element);
            if (checkElement.find('input[type="checkbox"]').prop('checked')) {
                // Insert (or update) check: Need current position of selected vector
                expectedResult[check] = this.settings.expected_result_positions[vectorName][check];
                // Insert (or update) tolerance
                var tolerance = checkElement.find('input[type="number"]').val();
                expectedResult[check + '_tolerance'] = parseFloat(tolerance);
            }
        }, this);
        if (_.isEmpty(expectedResult)) {  // If author doesn't select any checks,
                                          // assume they also want to skip the presence check
                                          // (which the grader will perform automatically
                                          // for each vector that has an entry in expected_result)
            delete this.settings.expected_result[vectorName];
        } else {
            this.settings.expected_result[vectorName] = expectedResult;
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

    VectorDraw.prototype.getDefaultVector = function(coords) {
        this.numberOfVectors += 1;
        var name = String(this.numberOfVectors),
            description =  "Vector " + name;
        return {
            name: name,
            description: description,
            coords: coords,
            type: "vector",
            render: false,
            length_factor: 1,
            length_units: "",
            base_angle: 0,
            style: {
                pointSize: 1,
                pointColor: "red",
                width: 4,
                color: "blue",
                label: null,
                labelColor: "black"
            }
        };
    };

    VectorDraw.prototype.onBoardDown = function(evt) {
        var coords = this.getMouseCoords(evt);
        var targetObjects = this.objectsUnderMouse(coords);
        if (!targetObjects || _.all(targetObjects, this.canCreateVectorOnTopOf.bind(this))) {
            if (this.resultMode) {
                return;
            }
            // Add vector to board
            var point_coords = [coords.usrCoords[1], coords.usrCoords[2]];
            var defaultVector = this.getDefaultVector([point_coords, point_coords]);
            this.settings.vectors.push(defaultVector);
            var lastIndex = this.numberOfVectors - 1;
            this.drawMode = true;
            this.dragged_vector = this.renderVector(lastIndex);
            this.addEditMenuOption(defaultVector.name, lastIndex);
        }
        else {
            // Move existing vector around
            this.drawMode = false;
            var vectorPoint = _.find(targetObjects, this.getVectorForObject.bind(this));
            if (vectorPoint) {
                this.dragged_vector = this.getVectorForObject(vectorPoint);
                this.dragged_vector.point1.setProperty({fixed: false});
                this.updateVectorProperties(this.dragged_vector);
                if (this.resultMode) {
                    _.each(['name', 'label'], function(propName) {
                        $('.vector-prop-' + propName + ' input', element).prop('disabled', true);
                    });
                    this.updateChecks(this.dragged_vector);
                    $('.checks input', element).prop('disabled', false);
                }
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
        if (!this.wasUsed) {
            this.wasUsed = true;
        }
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
        if (this.resultMode) {
            _.each(['name', 'label'], function(propName) {
                $('.vector-prop-' + propName + ' input', element).prop('disabled', true);
            });
            this.updateChecks(vectorObject);
            $('.checks input', element).prop('disabled', false);
        }
    };

    VectorDraw.prototype.onEditSubmit = function(evt) {
        if (!this.wasUsed) {
            this.wasUsed = true;
        }
        // About to save changes, so hide message about pending changes
        $('.vector-prop-update .update-pending', element).hide();
        // Get name of vector that is currently "selected"
        var vectorName = String($('.element-list-edit', element).find('option:selected').data('vector-name')),
            newValues = {};
        // Get values from input fields
        _.each(this.editableProperties, function(prop) {
            newValues[prop] = $.trim($('.vector-prop-' + prop + ' input', element).val());
        });
        // Process values
        var newName = newValues.name,
            newLabel = newValues.label,
            newTail = _.map(newValues.tail.split(/ *, */), function(coord) { return parseFloat(coord); }),
            newLength = parseFloat(newValues.length),
            newAngle = parseFloat(newValues.angle);
        // Validate and update values
        var vectorNames = this.getVectorNames(),
            vectorSettings = this.getVectorSettingsByName(vectorName),
            boardObject = this.board.elementsByName[vectorName];
        // 1. Update name
        if (newName && newName !== vectorName && !_.contains(vectorNames, newName)) {
            // Update vector settings
            vectorSettings.name = newName;
            // Update dropdown for selecting vector to edit
            var editOption = $('.menu .element-list-edit option[data-vector-name="' + vectorName + '"]', element);
            editOption.data('vector-name', newName);
            editOption.text(newName);
            // Update board
            boardObject.name = newName;
            boardObject.point2.name = newName;
            this.board.elementsByName[newName] = boardObject;
            delete this.board.elementsByName[vectorName];
            // Update expected position
            var expectedPositions = this.settings.expected_result_positions,
                expectedPosition = expectedPositions[vectorName];
            if (expectedPosition) {
                expectedPositions[newName] = expectedPosition;
                delete expectedPositions[vectorName];
            }
            // Update expected result
            var expectedResults = this.settings.expected_result,
                expectedResult = expectedResults[vectorName];
            if (expectedResult) {
                expectedResults[newName] = expectedResult;
                delete expectedResults[vectorName];
            }
        } else {
            $('.vector-prop-name input', element).val(vectorName);
        }
        // 2. Update label
        if (newLabel) {
            vectorSettings.style.label = newLabel;
            boardObject.point2.name = newLabel;  // Always prefer label for labeling vector on board
        } else {
            vectorSettings.style.label = null;
            boardObject.point2.name = newName || vectorName;  // ... but fall back on name if label was removed
        }
        // 3. Update tail, length, angle
        var values = [newTail[0], newTail[1], newLength, newAngle];
        if (!_.some(values, Number.isNaN)) {
            $('.vector-prop-update .update-error', element).hide();
            // Use coordinates of new tail, new length, new angle to calculate new position of tip
            var radians = newAngle * Math.PI / 180;
            var newTip = [
                newTail[0] + Math.cos(radians) * newLength,
                newTail[1] + Math.sin(radians) * newLength
            ];
            // Update position of vector
            boardObject.point1.setPosition(JXG.COORDS_BY_USER, newTail);
            boardObject.point2.setPosition(JXG.COORDS_BY_USER, newTip);
            this.board.update();
            // If board is in result mode, also save
            // - expected position
            // - check data
            // for "selected" vector
            if (this.resultMode) {
                this.saveExpectedPosition(vectorName, [newTail, newTip], newLength, newAngle);
                this.saveChecks(vectorName);
            }
        } else {
            $('.vector-prop-update .update-error', element).show();
        }
    };

    VectorDraw.prototype.getVectorCoords = function(name) {
        var object = this.board.elementsByName[name];
        return {
            tail: [object.point1.X(), object.point1.Y()],
            tip: [object.point2.X(), object.point2.Y()]
        };
    };

    VectorDraw.prototype.getState = function() {
        var vectors = [];
        _.each(this.settings.vectors, function(vec) {
            if (vec.deleted) {
                return;
            }
            var coords = this.getVectorCoords(vec.name),
                tail = coords.tail,
                tip = coords.tip,
                x1 = tail[0],
                y1 = tail[1],
                x2 = tip[0],
                y2 = tip[1];
            // Update coordinates
            vec.coords = [tail, tip];
            vec.tail = tail;
            vec.tip = tip;
            // Update length, angle
            vec.length = Math.sqrt(Math.pow(x2-x1, 2) + Math.pow(y2-y1, 2));
            // Update angle
            vec.angle = ((Math.atan2(y2-y1, x2-x1)/Math.PI*180)) % 360;
            vectors.push(vec);
        }, this);
        return vectors;
    };

    // Initialization logic

    // Initialize functionality for non-WYSIWYG editing functionality
    var fieldEditor = StudioEditableXBlockMixin(runtime, element);

    // Initialize WYSIWYG editor
    var vectordraw = new VectorDraw('vectordraw', init_args.settings);

    // Set up click handlers
    $('.save-button', element).on('click', function(e) {
        e.preventDefault();
        var data = {};
        if (vectordraw.wasUsed) {
            // If author edited both initial state and result,
            // vectordraw.settings.vectors corresponds to state vectors were in
            // when author switched to result mode
            data.vectors = vectordraw.resultMode ? vectordraw.settings.vectors : vectordraw.getState();
            data.expected_result_positions = vectordraw.settings.expected_result_positions;
            data.expected_result = vectordraw.settings.expected_result;
        }
        fieldEditor.save(data);
    });

    $('.cancel-button', element).on('click', function(e) {
        e.preventDefault();
        fieldEditor.cancel();
    });

    $('.info-button', element).on('click', function(e) {
        e.preventDefault();
        $('#wysiwyg-description', element).toggle();
    });

    $('input', element).on('change', function(e) {
        $('.update-error').hide();
        $('.update-pending').show();
    });
}
