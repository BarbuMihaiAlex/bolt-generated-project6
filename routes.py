"""
Update the routes to handle the new multi-port functionality
"""

@containers_bp.route('/api/request', methods=['POST'])
@authed_only
@during_ctf_time_only
@require_verified_emails
@ratelimit(method="POST", limit=100, interval=300, key_prefix='rl_request_container_post')
def route_request_container():
    """
    Request a new container instance with support for multiple ports.
    """
    user = get_current_user()
    log("containers_debug", format="Requesting container")

    if request.json is None or request.json.get("chal_id") is None or user is None:
        log("containers_errors", format="Invalid request to /api/request")
        return {"error": "Invalid request"}, 400

    try:
        docker_assignment = current_app.container_manager.settings.get("docker_assignment")
        log("containers_debug", 
            format="CHALL_ID:{challenge_id}|Docker assignment mode: {mode}",
            challenge_id=request.json.get("chal_id"),
            mode=docker_assignment)

        response, status_code = create_container(
            current_app.container_manager,
            request.json.get("chal_id"),
            user.id,
            user.team_id,
            docker_assignment
        )
        return response, status_code

    except Exception as e:
        log("containers_errors", 
            format="CHALL_ID:{challenge_id}|Error creating container: {error}",
            challenge_id=request.json.get("chal_id"),
            error=str(e))
        return {"error": "An error has occurred"}, 500

@containers_bp.route('/dashboard', methods=['GET'])
@admins_only
def route_containers_dashboard():
    """
    Display the admin dashboard with enhanced port information.
    """
    admin_user = get_current_user()
    log("containers_actions", format="Admin accessing container dashboard")

    try:
        running_containers = ContainerInfoModel.query.order_by(
            ContainerInfoModel.timestamp.desc()).all()

        connected = current_app.container_manager.is_connected()

        # Check container status and port information
        for container in running_containers:
            try:
                container.is_running = current_app.container_manager.is_container_running(
                    container.container_id)
                if container.is_running:
                    # Update port mappings if container is running
                    current_ports = current_app.container_manager.get_container_ports(
                        container.container_id)
                    container.ports = json.dumps(current_ports)
                    db.session.commit()
            except Exception as e:
                log("containers_errors", 
                    format="Error checking container '{container_id}' status: {error}",
                    container_id=container.container_id,
                    error=str(e))
                container.is_running = False

        docker_assignment = current_app.container_manager.settings.get("docker_assignment")

        return render_template(
            'container_dashboard.html',
            containers=running_containers,
            connected=connected,
            settings={'docker_assignment': docker_assignment}
        )

    except Exception as e:
        log("containers_errors", format="Error loading dashboard: {error}", error=str(e))
        return "An error occurred while loading the dashboard", 500

# ... [rest of the routes remain the same] ...
