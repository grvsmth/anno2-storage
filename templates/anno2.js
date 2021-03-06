var serverUri = 'https://{{ url }}';

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

launch = function (inDiv) {
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
    var content = $(inDiv).annotator();
    console.log("Welcome, " + window.location.href);
    content.annotator('addPlugin', 'Tags').annotator('addPlugin', 'Store', {
        prefix: serverUri + '/store',
        annotationData: {
            'uri': window.location.href
        },
        loadFromSearch: {
            'limit': 20,
            'uri': window.location.href
        }
    });
    // content.annotator('addPlugin', 'Auth', { tokenUrl: serverUri + '/auth/token' });
};
