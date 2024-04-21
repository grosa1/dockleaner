from pykson import JsonObject, IntegerField, StringField

class Smell(JsonObject):
    line = IntegerField()
    code = StringField()
    message = StringField()
    