"""
This module defines the database models for the containers plugin in CTFd.
It includes models for container challenges, container information, and container settings.
"""

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import json

from CTFd.models import db
from CTFd.models import Challenges

class ContainerChallengeModel(Challenges):
    """
    Represents a container-based challenge in CTFd.
    """
    __mapper_args__ = {"polymorphic_identity": "container"}
    id = db.Column(
        db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE"), primary_key=True
    )
    image = db.Column(db.Text)
    ports = db.Column(db.Text)  # JSON string of port mappings
    command = db.Column(db.Text, default="")
    volumes = db.Column(db.Text, default="")
    initial = db.Column(db.Integer, default=0)
    minimum = db.Column(db.Integer, default=0)
    decay = db.Column(db.Integer, default=0)

    def __init__(self, *args, **kwargs):
        super(ContainerChallengeModel, self).__init__(**kwargs)
        self.value = kwargs["initial"]
        
    @property
    def port_mappings(self):
        """Get port mappings as a dictionary"""
        if not self.ports:
            return {}
        try:
            return json.loads(self.ports)
        except json.JSONDecodeError:
            return {}

class ContainerInfoModel(db.Model):
    """
    Represents information about a running container instance.
    """
    __mapper_args__ = {"polymorphic_identity": "container_info"}
    container_id = db.Column(db.String(512), primary_key=True)
    challenge_id = db.Column(
        db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE")
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE")
    )
    team_id = db.Column(
        db.Integer, db.ForeignKey("teams.id", ondelete="CASCADE")
    )
    ports = db.Column(db.Text)  # JSON string of assigned ports
    timestamp = db.Column(db.Integer)
    expires = db.Column(db.Integer)

    user = db.relationship("Users", foreign_keys=[user_id])
    team = db.relationship("Teams", foreign_keys=[team_id])
    challenge = db.relationship(ContainerChallengeModel,
                              foreign_keys=[challenge_id])

    @property
    def port_mappings(self):
        """Get assigned port mappings as a dictionary"""
        if not self.ports:
            return {}
        try:
            return json.loads(self.ports)
        except json.JSONDecodeError:
            return {}

class ContainerSettingsModel(db.Model):
    """
    Represents configuration settings for the containers plugin.
    """
    key = db.Column(db.String(512), primary_key=True)
    value = db.Column(db.Text)

    @classmethod
    def apply_default_config(cls, key, value):
        if not cls.query.filter_by(key=key).first():
            db.session.add(cls(key=key, value=value))
