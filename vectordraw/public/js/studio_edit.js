/* Javascript for StudioEditableXBlockMixin. */
function StudioEditableXBlockMixin(runtime, element) {
    "use strict";

    var fields = [];
    var tinyMceAvailable = (typeof $.fn.tinymce !== 'undefined'); // Studio includes a copy of tinyMCE and its jQuery plugin
    var errorMessage = gettext("This may be happening because of an error with our server or your internet connection. Make sure you are online, and try refreshing the page.");

    $(element).find('.field-data-control').each(function() {
        var $field = $(this);
        var $wrapper = $field.closest('li');
        var $resetButton = $wrapper.find('button.setting-clear');
        var type = $wrapper.data('cast');
        fields.push({
            name: $wrapper.data('field-name'),
            isSet: function() { return $wrapper.hasClass('is-set'); },
            hasEditor: function() { return tinyMceAvailable && $field.tinymce(); },
            val: function() {
                var val = $field.val();
                // Cast values to the appropriate type so that we send nice clean JSON over the wire:
                if (type === 'boolean')
                    return (val === 'true' || val === '1');
                if (type === "integer")
                    return parseInt(val, 10);
                if (type === "float")
                    return parseFloat(val);
                return val;
            },
            removeEditor: function() {
                $field.tinymce().remove();
            }
        });
        var fieldChanged = function() {
            // Field value has been modified:
            $wrapper.addClass('is-set');
            $resetButton.removeClass('inactive').addClass('active');
        };
        $field.bind("change input paste", fieldChanged);
        $resetButton.click(function() {
            $field.val($wrapper.attr('data-default')); // Use attr instead of data to force treating the default value as a string
            $wrapper.removeClass('is-set');
            $resetButton.removeClass('active').addClass('inactive');
        });
        if (type === 'html' && tinyMceAvailable) {
            tinyMCE.baseURL = baseUrl + "/js/vendor/tinymce/js/tinymce";
            $field.tinymce({
                theme: 'modern',
                skin: 'studio-tmce4',
                height: '200px',
                formats: { code: { inline: 'code' } },
                codemirror: { path: "" + baseUrl + "/js/vendor" },
                convert_urls: false,
                plugins: "link codemirror",
                menubar: false,
                statusbar: false,
                toolbar_items_size: 'small',
                toolbar: "formatselect | styleselect | bold italic underline forecolor wrapAsCode | bullist numlist outdent indent blockquote | link unlink | code",
                resize: "both",
                setup : function(ed) {
                    ed.on('change', fieldChanged);
                }
            });
        }

    });

    var studio_submit = function(data) {
        var handlerUrl = runtime.handlerUrl(element, 'submit_studio_edits');
        runtime.notify('save', {state: 'start', message: gettext("Saving")});
        $.ajax({
            type: "POST",
            url: handlerUrl,
            data: JSON.stringify(data),
            dataType: "json",
            notifyOnError: false
        }).done(function(response) {
            runtime.notify('save', {state: 'end'});
        }).fail(function(jqXHR) {
            if (jqXHR.responseText) { // Is there a more specific error message we can show?
                try {
                    errorMessage = JSON.parse(jqXHR.responseText).error;
                    if (_.isObject(errorMessage) && errorMessage.messages) {
                        // e.g. {"error": {"messages": [{"text": "Unknown user 'bob'!", "type": "error"}, ...]}} etc.
                        var errorMessages = _.pluck(errorMessage.messages, "text");
                        errorMessage = errorMessages.join(", ");
                    }
                } catch (error) { errorMessage = jqXHR.responseText.substr(0, 300); }
            }
            runtime.notify('error', {title: gettext("Unable to update settings"), message: errorMessage});
        });
    };

    return {

        getContents: function(fieldName) {
            return _.findWhere(fields, {name: fieldName}).val();
        },

        save: function(data) {
            var values = {};
            var notSet = []; // List of field names that should be set to default values
            _.each(fields, function(field) {
                if (field.isSet()) {
                    values[field.name] = field.val();
                } else {
                    notSet.push(field.name);
                }
                // Remove TinyMCE instances to make sure jQuery does not try to access stale instances
                // when loading editor for another block:
                if (field.hasEditor()) {
                    field.removeEditor();
                }
            });
            // If WYSIWYG editor was used,
            // prefer its data over values of "Vectors" and "Expected result" fields:
            if (!_.isEmpty(data)) {
                values.vectors = JSON.stringify(data.vectors, undefined, 4);
                values.expected_result_positions = data.expected_result_positions;
                values.expected_result = JSON.stringify(data.expected_result, undefined, 4);
            }

            studio_submit({values: values, defaults: notSet});
        },

        cancel: function() {
            // Remove TinyMCE instances to make sure jQuery does not try to access stale instances
            // when loading editor for another block:
            _.each(fields, function(field) {
                if (field.hasEditor()) {
                    field.removeEditor();
                }
            });
            runtime.notify('cancel', {});
        }

    };

}
