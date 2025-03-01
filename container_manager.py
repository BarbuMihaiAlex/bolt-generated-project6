"""
Container manager modifications for multi-port support
"""

def create_container(self, image: str, ports: dict, command: str, volumes: str):
    """
    Create a new Docker container with multiple port mappings.

    Args:
        image (str): The Docker image to use
        ports (dict): Dictionary of port mappings
        command (str): The command to run
        volumes (str): JSON string of volume configurations

    Returns:
        docker.models.containers.Container: The created container
    """
    kwargs = {}

    # Set memory limits
    if self.settings.get("container_maxmemory"):
        try:
            mem_limit = int(self.settings.get("container_maxmemory"))
            if mem_limit > 0:
                kwargs["mem_limit"] = f"{mem_limit}m"
        except ValueError:
            raise ContainerException("Container memory limit must be an integer")

    # Set CPU limits
    if self.settings.get("container_maxcpu"):
        try:
            cpu_period = float(self.settings.get("container_maxcpu"))
            if cpu_period > 0:
                kwargs["cpu_quota"] = int(cpu_period * 100000)
                kwargs["cpu_period"] = 100000
        except ValueError:
            raise ContainerException("Container CPU limit must be a number")

    # Handle volumes
    if volumes:
        try:
            volumes_dict = json.loads(volumes)
            kwargs["volumes"] = volumes_dict
        except json.JSONDecodeError:
            raise ContainerException("Invalid volumes JSON")

    # Create port mapping configuration
    port_bindings = {}
    for container_port in ports.keys():
        port_bindings[str(container_port)] = None

    try:
        return self.client.containers.run(
            image,
            ports=port_bindings,
            command=command,
            detach=True,
            auto_remove=True,
            **kwargs
        )
    except docker.errors.ImageNotFound:
        raise ContainerException("Docker image not found")

def get_container_ports(self, container_id: str) -> dict:
    """
    Get all mapped ports for a container.

    Args:
        container_id (str): The container ID

    Returns:
        dict: Dictionary of container ports to host ports
    """
    try:
        container = self.client.containers.get(container_id)
        port_mappings = {}
        
        for container_port, host_bindings in container.ports.items():
            if host_bindings:
                # Extract the actual port number from the container_port string
                container_port = container_port.split('/')[0]
                port_mappings[container_port] = host_bindings[0]["HostPort"]
                
        return port_mappings
    except Exception as e:
        raise ContainerException(f"Failed to get container ports: {str(e)}")
