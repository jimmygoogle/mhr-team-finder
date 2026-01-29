from flask import Blueprint, Flask, render_template, request, jsonify
from app.services.association_service import load_association_data, get_association_data
#app = Flask(__name__)

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template('index.html')

@main_bp.route("/load")
def load_data():
    load_association_data()
    return "Hello from Jim!"

@main_bp.route("/associations")
def get_associations():
    print(request.args)
    data = get_association_data(request)
    return jsonify(data)


# @main_bp.route("/api/teams")
# def api_teams():
#     session = SessionLocal()

#     filters = []
#     params = {}

#     state = request.args.get("state")
#     if state:
#         filters.append("state = :state")
#         params["state"] = state

#     age = request.args.get("age")
#     if age:
#         filters.append("age_group = :age")
#         params["age"] = age

#     where = ""
#     if filters:
#         where = "WHERE " + " AND ".join(filters)

#     rows = session.execute(
#         text(f"""
#             SELECT name, latitude, longitude, age_group
#             FROM teams
#             {where}
#         """),
#         params
#     ).fetchall()

#     session.close()

#     return jsonify({
#         "type": "FeatureCollection",
#         "features": [
#             {
#                 "type": "Feature",
#                 "geometry": {
#                     "type": "Point",
#                     "coordinates": [r.longitude, r.latitude],
#                 },
#                 "properties": {
#                     "name": r.name,
#                     "age": r.age_group,
#                 },
#             }
#             for r in rows
#         ]
#     })

# @app.route("/api/associations")
# def api_associations():
#     session = SessionLocal()

#     filters = []
#     params = {}

#     state = request.args.get("state")
#     if state:
#         filters.append("a.state = :state")
#         params["state"] = state

#     age = request.args.get("age")
#     if age:
#         filters.append("t.age_group = :age")
#         params["age"] = age

#     min_rating = request.args.get("min_rating")
#     if min_rating:
#         filters.append("t.current_rating >= :min_rating")
#         params["min_rating"] = float(min_rating)

#     where = ""
#     if filters:
#         where = "WHERE " + " AND ".join(filters)

#     rows = session.execute(
#         text(f"""
#             SELECT DISTINCT
#                 a.id,
#                 a.name,
#                 a.latitude,
#                 a.longitude
#             FROM associations a
#             JOIN teams t ON t.association_id = a.id
#             {where}
#         """),
#         params
#     ).fetchall()

#     session.close()

#     return jsonify({
#         "type": "FeatureCollection",
#         "features": [
#             {
#                 "type": "Feature",
#                 "geometry": {
#                     "type": "Point",
#                     "coordinates": [r.longitude, r.latitude],
#                 },
#                 "properties": {
#                     "id": r.id,
#                     "name": r.name,
#                 },
#             }
#             for r in rows
#         ],
#     })

# @app.route("/api/association/<int:association_id>/teams")
# def api_association_teams(association_id):
#     session = SessionLocal()

#     rows = session.execute(
#         text("""
#             SELECT id, name, age_group, current_rating
#             FROM teams
#             WHERE association_id = :id
#             ORDER BY age_group
#         """),
#         {"id": association_id}
#     ).fetchall()

#     session.close()

#     return jsonify([
#         {
#             "id": r.id,
#             "name": r.name,
#             "age": r.age_group,
#             "rating": r.current_rating,
#         }
#         for r in rows
#     ])


# @app.route("/api/team/<int:team_id>/ratings")
# def api_team_ratings(team_id):
#     session = SessionLocal()

#     rows = session.execute(
#         text("""
#             SELECT mhr_rating_date, rating
#             FROM rating_history
#             WHERE team_id = :id
#             ORDER BY mhr_rating_date
#         """),
#         {"id": team_id}
#     ).fetchall()

#     session.close()

#     return jsonify([
#         {
#             "date": r.mhr_rating_date.isoformat(),
#             "rating": float(r.rating),
#         }
#         for r in rows
#     ])

# @app.route("/api/associations/nearby")
# def api_associations_nearby():
#     lat = float(request.args["lat"])
#     lon = float(request.args["lon"])
#     miles = float(request.args.get("miles", 50))

#     meters = miles * 1609.34

#     session = SessionLocal()

#     rows = session.execute(
#         text("""
#             SELECT
#                 id,
#                 name,
#                 latitude,
#                 longitude,
#                 ST_Distance(
#                     geom,
#                     ST_MakePoint(:lon, :lat)::geography
#                 ) / 1609.34 AS miles
#             FROM associations
# JOIN teams t ON t.association_id = a.id
# WHERE
#     ST_DWithin(a.geom, :point, :meters)
#     AND t.age_group = '12U'
#     AND t.current_rating >= 80
#             ORDER BY miles
#         """),
#         {
#             "lat": lat,
#             "lon": lon,
#             "meters": meters,
#         }
#     ).fetchall()

#     session.close()

#     return jsonify([
#         {
#             "id": r.id,
#             "name": r.name,
#             "lat": r.latitude,
#             "lon": r.longitude,
#             "miles": round(r.miles, 2),
#         }
#         for r in rows
#     ])
