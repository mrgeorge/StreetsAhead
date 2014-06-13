from flask.ext.wtf import Form
from wtforms import TextField
from wtforms.validators import Required

class EntryForm(Form):
    query = TextField('Search', validators = [Required()])
