from datetime import datetime
from server_manager.models import ServerConfig
from server_manager.ssh_service import run_ssh_command
from .models import Deployment


def deploy_repository(app, user):
    server = ServerConfig.objects.filter(user=user, is_active=True).order_by('-id').first()
    if not server:
        return False, "No active server configured.", None

    deployment = Deployment.objects.create(
        app=app,
        status='pending',
        logs='Deployment started.'
    )

    app_name = app.app_name.strip().replace(" ", "-").lower()
    remote_base = server.deploy_base_path.rstrip("/")
    remote_path = f"{remote_base}/{app_name}"
    image_name = f"{app_name}:latest"
    app.container_name = app_name
    app.save()

    app.container_name = app_name
    app.save()
    
    command = (
        f'mkdir -p "{remote_base}" && '
        f'rm -rf "{remote_path}" && '
        f'git clone "{app.repository_url}" "{remote_path}" && '
        f'cd "{remote_path}" && '
        f'docker build -t "{image_name}" . && '
        f'(docker rm -f "{app_name}" || true) && '
        f'docker run -d -p {app.port}:{app.port} --name "{app_name}" "{image_name}"'
    )

    print("REPO URL:", app.repository_url)
    print("DEPLOY COMMAND:", command)

    deployment.status = 'building'
    deployment.logs = f"Running command: {command}"
    deployment.save()

    success, result = run_ssh_command(
        server.host,
        server.ssh_port,
        server.username,
        server.password,
        command
    )

    if success:
        deployment.status = 'running'
        deployment.logs = result or "Repository deployed successfully."
        deployment.completed_at = datetime.now()
        deployment.save()

        app.status = 'running'
        app.save()

        return True, result or "Repository deployed successfully.", deployment

    deployment.status = 'failed'
    deployment.error_message = result
    deployment.logs = result
    deployment.completed_at = datetime.now()
    deployment.save()

    app.status = 'failed'
    app.save()

    return False, result, deployment