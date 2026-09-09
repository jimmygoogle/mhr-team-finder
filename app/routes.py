from flask import Blueprint, Flask, render_template, request, jsonify
from app.services.hockey import load_association_data, get_association_data, find_associations, find_teams

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template('index.html')

@main_bp.route("/hockey")
def get_mhr_data():
    data = get_association_data(request)
    return jsonify(data)

@main_bp.route("/associations")
def get_associations():
    data = find_associations(request)
    return jsonify(data)

@main_bp.route("/teams")
def get_teams():
    data = find_teams(request)
    return jsonify(data)
