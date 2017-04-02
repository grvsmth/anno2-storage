# anno2-storage
Anno2-storage is a Django storage backend for Annotatorjs annotations.  It
implements the [Annotator Storage API](http://docs.annotatorjs.org/en/v1.2.x/storage.html)
using the [Django Rest Framework](http://www.django-rest-framework.org/), with
support for the *Tag* plugin using [Django-taggit](https://github.com/alex/django-taggit)
and [django-taggit-serializer](https://github.com/glemmaPaul/django-taggit-serializer).
There is also support for the *auth* plugin using [django-registration-redux](https://django-registration-redux.readthedocs.io/en/latest/).
Thanks to these frameworks and libraries, the specific code to implment the Annotator Storage API is less than 300 lines.

There is currently no support for the Filter, Markdown or Permissions plugins.

This has been tested for annotatorjs linked directly from the HTML file (see
static/test.html), but may be able to provide a backend for hypothes.is
annotations in a Chrome extension.