function VectorDrawXBlockEdit(runtime, element, init_args) {
    'use strict';

    var VectorDraw = function(element_id, settings) {
        this.board = null;
        this.dragged_vector = null;
        this.drawMode = false;
        this.wasUsed = false;
        this.settings = settings;
        this.numberOfVectors = this.settings.vectors.length;
        this.element = $('#' + element_id, element);

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

        this.settings.points.forEach(function(point, idx) {
            this.renderPoint(idx);
        }, this);

        this.settings.vectors.forEach(function(vec, idx) {
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
        var titleElement = $("<title>").attr("id", titleID).text(vec.name);
        lineElement.append(titleElement);
        lineElement.attr("aria-labelledby", titleID);

        var descID = lineID + "-desc";
        var descElement = $("<desc>").attr("id", descID).text(vec.description);
        lineElement.append(descElement);
        lineElement.attr("aria-describedby", descID);

        return line;
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
        var name = "" + this.numberOfVectors,
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
            // Add vector to board
            var point_coords = [coords.usrCoords[1], coords.usrCoords[2]];
            var defaultVector = this.getDefaultVector([point_coords, point_coords]);
            this.settings.vectors.push(defaultVector);
            var lastIndex = this.numberOfVectors - 1;
            this.drawMode = true;
            this.dragged_vector = this.renderVector(lastIndex);
        }
        else {
            // Move existing vector around
            this.drawMode = false;
            var vectorPoint = _.find(targetObjects, this.getVectorForObject.bind(this));
            if (vectorPoint) {
                this.dragged_vector = this.getVectorForObject(vectorPoint);
                this.dragged_vector.point1.setProperty({fixed: false});
            }
        }
    };

    VectorDraw.prototype.onBoardMove = function(evt) {
        if (this.drawMode) {
            var coords = this.getMouseCoords(evt);
            this.dragged_vector.point2.moveTo(coords.usrCoords);
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

    VectorDraw.prototype.getVectorCoords = function(name) {
        var object = this.board.elementsByName[name];
        return {
            tail: [object.point1.X(), object.point1.Y()],
            tip: [object.point2.X(), object.point2.Y()]
        };
    };

    VectorDraw.prototype.getState = function() {
        var vectors = [];
        this.settings.vectors.forEach(function(vec) {
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
            vec.length = Math.sqrt(Math.pow(x2-x1, 2) + Math.pow(y2-y1, 2));;
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
            var state = vectordraw.getState();
            data = { vectors: state };
        }
        fieldEditor.save(data);
    });
    $('.cancel-button', element).on('click', function(e) {
        e.preventDefault();
        fieldEditor.cancel();
    });

}
