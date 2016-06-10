// Ao carregar a página, realiza os seguintes procedimentos automaticamente:
jQuery(document).ready(function($) {
    $('#form-texto').submit(function(event) {
        //var text = $('#form-texto #id_text').val();
        var text = tinyMCE.activeEditor.getContent({format : 'text'});
        var cache_reload = $('#id_cache_reload').val();
        var data = {text: text, cache_reload: cache_reload};

        event.preventDefault();
        $.ajax({
            type: 'POST',
            url: '{% url "post-v1" %}',
            data: JSON.stringify(data),
            contentType: 'application/json',
            dataType: 'json',
            success: function(response) {
                var sobek_output = convert_list_of_strings_to_string(response.sobek_output);
                console.log('Saída do Sobek: %s', sobek_output);

                var element = google.search.cse.element.getElement('gsearch');
                element.execute(response.sobek_output);
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log(jqXHR.responseJSON);
            },
            beforeSend: function(jqXHR, settings) {
                jqXHR.setRequestHeader('X-CSRFToken', $('input[name=csrfmiddlewaretoken]').val());
            }
        });
    });
});


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
        '//cse.google.com.br/cse.js?hl=pt-br&cx=' + cx;
    var s = document.getElementsByTagName('script')[0];
    s.parentNode.insertBefore(gcse, s);
})();
