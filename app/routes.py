from app import app, db
from flask import request, jsonify, Response
from .models import Model, model_schema, models_schema
import os


@app.route('/')
def home():
    return Response('working so far')
