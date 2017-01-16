# anno2-storage
Anno2-storage is a Django storage backend for Annotatorjs annotations.  It implements the [Annotator Storage API](http://docs.annotatorjs.org/en/v1.2.x/storage.html) using the [Django Rest Framework](http://www.django-rest-framework.org/), with support for the Tag plugin using [Django-taggit](https://github.com/alex/django-taggit) and [django-taggit-serializer](https://github.com/glemmaPaul/django-taggit-serializer).  Thanks to these frameworks, the specific code to implment the Annotator Storage API is less than 150 lines.

There is currently no support for the Auth, Filter, Markdown or Permissions plugins.
