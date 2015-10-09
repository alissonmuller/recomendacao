// Ao carregar a página, realiza os seguintes procedimentos automaticamente:
$(document).ready(function() {
    $('#form-texto').submit(function(event) {
        //var text = $('#form-texto #id_text').val();
        var text = tinyMCE.activeEditor.getContent({format : 'text'});
        
        $.ajax({
            type: 'POST',
            url: '{% url "envia_texto_sobek" %}',
            data: JSON.stringify({text:text}),
            success: function(response) {
                var sobek_output = convert_list_of_strings_to_string(response.sobek_output);
                console.log('Saída do Sobek: %s', sobek_output);
                
                var element = google.search.cse.element.getElement('gsearch');
                element.execute(response.sobek_output);
            },
            beforeSend: function(jqXHR, settings) {
                jqXHR.setRequestHeader('X-CSRFToken', $('input[name=csrfmiddlewaretoken]').val());
            }
        });
        
        return false;
    });
    
    $('#form-texto-post').submit(function(event) {
        var text = tinyMCE.activeEditor.getContent({format : 'text'});
        var data = {text:text};
        
        append_hidden_inputs(event.target, data);
        $(event.target).prop('action', '{% url "post" %}');
    });
    
    $('#btn-enviar-texto-ajax').click(function(event) {
        var text = tinyMCE.activeEditor.getContent({format : 'text'});
        var mode = $('#id_mode').val();
        
        $.ajax({
            type: 'POST',
            url: '{% url "post" %}',
            data: JSON.stringify({text: text, mode: mode}),
            contentType: 'application/json',
            dataType: 'json',
            success: function(response) {
                var sobek_output = convert_list_of_strings_to_string(response.sobek_output);
                console.log('Saída do Sobek: %s', sobek_output);
                
                var results_container = $('#results-ajax');
                var words_string = '';
                var result = {};
                var results_string = '';
                
                results_container.html('');
                
                if (is_defined(response.sobek_output)) {
                    for (word_index in response.sobek_output) {
                        words_string += response.sobek_output[word_index] + ' ';
                    }
                    words_string = words_string.slice(0, -1);
                    
                    $('<div/>').html(words_string).appendTo(results_container);
                }
                
                if (is_defined(response.results_list)) {
                    for (result_index in response.results_list) {
                        result = response.results_list[result_index];
                        
                        results_string += '\
                            <h3><a href="' + result.url + '" target="_blank">' + result.title + '</a></h3>\
                            <cite>' + result.url + '</cite><br />' +
                            result.snippet;
                    }
                    
                    $('<div/>').html(results_string).appendTo(results_container);
                }
            },
            beforeSend: function(jqXHR, settings) {
                jqXHR.setRequestHeader('X-CSRFToken', $('input[name=csrfmiddlewaretoken]').val());
            }
        });
    });
});

function append_hidden_inputs(form, data) {
    for (i in data) {
        input = $('<input/>').prop({'type': 'hidden', 'name': i}).val(data[i]);
        old_input = $(form).find('[name="' + i +'"]').first();
        input_exists = old_input.length;
        
        if (!input_exists) {
            $(form).append(input);
        }
        else {
            old_input.replaceWith(input);
        }
    }
}

function convert_list_of_strings_to_string(list) {
    var output_string = '';
    for (string_index in list) {
        output_string += list[string_index] + ',';
    }
    output_string = output_string.slice(0, -1);
    return output_string;
}

function is_defined(variable) {
    if (typeof variable !== 'undefined') {
        return true; // variable is defined
    }
    else {
        return false; // variable is undefined
    }
}


//Scripts do Google Custom Search Engine
function gcseCallback() {
    /*
    if (document.readyState != 'complete') {
        return google.setOnLoadCallback(gcseCallback, true);
    }
    */
    google.search.cse.element.render({gname:'gsearch', div:'results', tag:'searchresults-only', attributes:{linkTarget:''}});
};
window.__gcse = {
    parsetags: 'explicit',
    callback: gcseCallback
};
(function() {
    var cx = '{{ CSE_ID }}';
    var gcse = document.createElement('script');
    gcse.type = 'text/javascript';
    gcse.async = true;
    gcse.src = (document.location.protocol == 'https:' ? 'https:' : 'http:') +
        '//cse.google.com/cse.js?cx=' + cx;
    var s = document.getElementsByTagName('script')[0];
    s.parentNode.insertBefore(gcse, s);
})();
