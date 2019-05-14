from app import db, ma


# Model
class Model(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    def __repr__(self):
        return f""


# Model Schema
class ModelSchema(ma.ModelSchema):
    class Meta:
        model = Model


# Init Model schema
model_schema = ModelSchema(strict=True)
models_schema = ModelSchema(many=True, strict=True)
