"""
Helper functions for container routes with multi-port support
"""

import time
import json
from typing import Dict, Any, Tuple

from CTFd.models import db
from flask import current_app

from .logs import log
from .models import ContainerInfoModel, ContainerChallengeModel
from .container_challenge import ContainerChallenge

def create_container(container_manager, challenge_id: int, user_id: int, team_id: int, docker_assignment: str) -> Tuple[Dict[str, Any], int]:
    """
    Create a new container instance with support for multiple ports.

    Args:
        container_manager: The container manager instance
        challenge_id: The ID of the challenge
        user_id: The ID of the user
        team_id: The ID of the team
        docker_assignment: The docker assignment mode

    Returns:
        Tuple containing response dict and status code
    """
    log("containers_debug", format="CHALL_ID:{challenge_id}|Initiating container creation process",
        challenge_id=challenge_id)

    # Get challenge details
    challenge = ContainerChallengeModel.query.filter_by(id=challenge_id).first()
    if not challenge:
        log("containers_errors", format="CHALL_ID:{challenge_id}|Challenge not found",
            challenge_id=challenge_id)
        return {"error": "Challenge not found"}, 404

    # Check existing containers based on assignment mode
    if docker_assignment in ["user", "unlimited"]:
        running_containers = ContainerInfoModel.query.filter_by(
            challenge_id=challenge.id, user_id=user_id)
    else:
        running_containers = ContainerInfoModel.query.filter_by(
            challenge_id=challenge.id, team_id=team_id)

    running_container = running_containers.first()

    # Handle existing container
    if running_container:
        try:
            if container_manager.is_container_running(running_container.container_id):
                log("containers_actions", 
                    format="CHALL_ID:{challenge_id}|Container '{container_id}' already running",
                    challenge_id=challenge_id,
                    container_id=running_container.container_id)
                
                return {
                    "status": "already_running",
                    "hostname": challenge.connection_info,
                    "ports": running_container.port_mappings,
                    "port_descriptions": challenge.port_mappings,
                    "expires": running_container.expires
                }, 200
            else:
                log("containers_debug", 
                    format="CHALL_ID:{challenge_id}|Container '{container_id}' not running, removing from database",
                    challenge_id=challenge_id,
                    container_id=running_container.container_id)
                db.session.delete(running_container)
                db.session.commit()
        except Exception as e:
            log("containers_errors", 
                format="CHALL_ID:{challenge_id}|Error checking container status: {error}",
                challenge_id=challenge_id,
                error=str(e))
            return {"error": "Error checking container status"}, 500

    # Check for other running containers based on assignment mode
    if docker_assignment != "unlimited":
        if docker_assignment == "user":
            other_container = ContainerInfoModel.query.filter_by(user_id=user_id).first()
        else:
            other_container = ContainerInfoModel.query.filter_by(team_id=team_id).first()

        if other_container:
            other_challenge = ContainerChallengeModel.query.filter_by(
                id=other_container.challenge_id).first()
            log("containers_errors", 
                format="CHALL_ID:{challenge_id}|Other container running for challenge '{other_challenge}'",
                challenge_id=challenge_id,
                other_challenge=other_challenge.name)
            return {"error": f"Stop other instance running ({other_challenge.name})"}, 400

    try:
        # Create new container with multiple port mappings
        created_container = container_manager.create_container(
            challenge.image,
            challenge.port_mappings,
            challenge.command,
            challenge.volumes
        )
    except Exception as e:
        log("containers_errors", 
            format="CHALL_ID:{challenge_id}|Container creation failed: {error}",
            challenge_id=challenge_id,
            error=str(e))
        return {"error": "Failed to create container"}, 500

    try:
        # Get all port mappings
        port_mappings = container_manager.get_container_ports(created_container.id)
        if not port_mappings:
            log("containers_errors", 
                format="CHALL_ID:{challenge_id}|Could not get ports for container '{container_id}'",
                challenge_id=challenge_id,
                container_id=created_container.id)
            return {"error": "Could not get container ports"}, 500

        # Calculate expiration time
        expires = int(time.time() + container_manager.expiration_seconds)

        # Create new container record
        new_container = ContainerInfoModel(
            container_id=created_container.id,
            challenge_id=challenge.id,
            user_id=user_id,
            team_id=team_id,
            ports=json.dumps(port_mappings),
            timestamp=int(time.time()),
            expires=expires
        )

        db.session.add(new_container)
        db.session.commit()

        log("containers_actions", 
            format="CHALL_ID:{challenge_id}|Container '{container_id}' created successfully",
            challenge_id=challenge_id,
            container_id=created_container.id)

        return {
            "status": "created",
            "hostname": challenge.connection_info,
            "ports": port_mappings,
            "port_descriptions": challenge.port_mappings,
            "expires": expires
        }, 200

    except Exception as e:
        log("containers_errors", 
            format="CHALL_ID:{challenge_id}|Error saving container info: {error}",
            challenge_id=challenge_id,
            error=str(e))
        return {"error": "Failed to save container information"}, 500

def kill_container(container_manager, container_id: str, challenge_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Kill a container and clean up its records.

    Args:
        container_manager: The container manager instance
        container_id: The ID of the container to kill
        challenge_id: The ID of the challenge (for logging)

    Returns:
        Tuple containing response dict and status code
    """
    log("containers_debug", 
        format="CHALL_ID:{challenge_id}|Killing container '{container_id}'",
        challenge_id=challenge_id,
        container_id=container_id)

    container = ContainerInfoModel.query.filter_by(container_id=container_id).first()
    if not container:
        log("containers_errors", 
            format="CHALL_ID:{challenge_id}|Container '{container_id}' not found",
            challenge_id=challenge_id,
            container_id=container_id)
        return {"error": "Container not found"}, 404

    try:
        container_manager.kill_container(container_id)
        db.session.delete(container)
        db.session.commit()
        
        log("containers_actions", 
            format="CHALL_ID:{challenge_id}|Container '{container_id}' killed successfully",
            challenge_id=challenge_id,
            container_id=container_id)
        return {"success": "Container killed"}, 200

    except Exception as e:
        log("containers_errors", 
            format="CHALL_ID:{challenge_id}|Error killing container: {error}",
            challenge_id=challenge_id,
            error=str(e))
        return {"error": "Failed to kill container"}, 500

def renew_container(container_manager, challenge_id: int, user_id: int, team_id: int, docker_assignment: str) -> Tuple[Dict[str, Any], int]:
    """
    Renew a container's expiration time.

    Args:
        container_manager: The container manager instance
        challenge_id: The ID of the challenge
        user_id: The ID of the user
        team_id: The ID of the team
        docker_assignment: The docker assignment mode

    Returns:
        Tuple containing response dict and status code
    """
    log("containers_debug", 
        format="CHALL_ID:{challenge_id}|Renewing container",
        challenge_id=challenge_id)

    # Get the running container based on assignment mode
    if docker_assignment in ["user", "unlimited"]:
        container = ContainerInfoModel.query.filter_by(
            challenge_id=challenge_id,
            user_id=user_id
        ).first()
    else:
        container = ContainerInfoModel.query.filter_by(
            challenge_id=challenge_id,
            team_id=team_id
        ).first()

    if not container:
        log("containers_errors", 
            format="CHALL_ID:{challenge_id}|No container found to renew",
            challenge_id=challenge_id)
        return {"error": "No container found"}, 404

    try:
        # Update expiration time
        new_expires = int(time.time() + container_manager.expiration_seconds)
        container.expires = new_expires
        db.session.commit()

        log("containers_actions", 
            format="CHALL_ID:{challenge_id}|Container '{container_id}' renewed",
            challenge_id=challenge_id,
            container_id=container.container_id)

        return {
            "success": "Container renewed",
            "expires": new_expires,
            "ports": container.port_mappings,
            "port_descriptions": container.challenge.port_mappings
        }, 200

    except Exception as e:
        log("containers_errors", 
            format="CHALL_ID:{challenge_id}|Error renewing container: {error}",
            challenge_id=challenge_id,
            error=str(e))
        return {"error": "Failed to renew container"}, 500
