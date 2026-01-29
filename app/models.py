from app import db
from geoalchemy2 import Geography, WKTElement
from datetime import datetime

class Association(db.Model):
    __tablename__ = "associations"

    __table_args__ = (
        db.Index(
            "idx_associations_geom",
            "geom",
            postgresql_using="gist"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    association_name = db.Column(db.String, nullable=False)
    city = db.Column(db.String, nullable=False)
    state = db.Column(db.String, nullable=False)
    mhr_association_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String, nullable=True)
    url = db.Column(db.String, nullable=True)

    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    geom = db.Column(Geography(geometry_type="POINT", srid=4326), nullable=True)

    def set_location(self, lat, lon):
        self.latitude = lat
        self.longitude = lon
        self.geom = WKTElement(f"POINT({lon} {lat})", srid=4326)

    teams = db.relationship(
        "Team",
        back_populates="association",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.UniqueConstraint('association_name', name='idx_unique_association_name'),
    )

class Team(db.Model):
    __tablename__ = "teams"
    
    id = db.Column(db.Integer, primary_key=True)
    association_id = db.Column(db.Integer, db.ForeignKey("associations.id"), nullable=False)
    team_name = db.Column(db.String, nullable=False)
    age_tier_id = db.Column(db.Integer, db.ForeignKey("age_tier.id"), nullable=True)
    mhr_team_id = db.Column(db.String, nullable=True)
    current_rating = db.Column(db.Float, nullable=True)

    association = db.relationship("Association", back_populates="teams")
    #rating_history = db.relationship("RatingHistory", backref="teams", cascade="all, delete-orphan")
    age_tier = db.relationship("AgeTier", backref="teams")

    __table_args__ = (
        db.UniqueConstraint('team_name', name='idx_unique_team_name'),
    )

class League(db.Model):
    __tablename__ = "leagues"
    
    id = db.Column(db.Integer, primary_key=True)
    league_name = db.Column(db.String, nullable=False)
    mhr_league_id = db.Column(db.Integer, nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('league_name', name='idx_unique_league_name'),
    )

class TeamLeague(db.Model):
    __tablename__ = "team_leagues"
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    league_id = db.Column(db.Integer, db.ForeignKey("leagues.id"), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('team_id', 'league_id', name='idx_unique_team_league'),
    )

class RatingHistory(db.Model):
    __tablename__ = "rating_history"
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    mhr_rating_week = db.Column(db.Integer, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('team_id', 'mhr_rating_week', name='idx_unique_team_id_mhr_rating_week'),
    )

class AgeTier(db.Model):
    __tablename__ = "age_tier"
    
    id = db.Column(db.Integer, primary_key=True)
    age = db.Column(db.String, nullable=False)
    tier = db.Column(db.String, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('age', 'tier', name='idx_unique_age_tier'),
    )
