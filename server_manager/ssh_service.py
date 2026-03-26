import paramiko
import socket
import paramiko


def test_ssh_connection(host, port, username, password):
    client=None
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
        client.connect(
            hostname=host,
            port=int(port),
            username=username,
            password=password,
            timeout=10,
            auth_timeout=10,
            banner_timeout=10,
            look_for_keys=False,
            allow_agent=False,
            
        )

        stdin, stdout, stderr = client.exec_command("echo connected")
        result = stdout.read().decode().strip()
        error =stderr.read().decode().strip()
        if error:
            return False,error
        return True,result or"connected"

    except paramiko.AuthenticationException as e:
        return False, f"Authentication failed: {str(e)}"

    except paramiko.SSHException as e:
        return False, f"SSH error: {str(e)}"

    except socket.timeout as e:
        return False, f"Connection timeout: {str(e)}"

    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)}"

    finally:
        if client is not None:
            client.close()

def run_ssh_command(host, port, username, password, command):
    client = None
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=host,
            port=int(port),
            username=username,
            password=password,
            timeout=30,
        )
        _, stdout, stderr = client.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        out = stdout.read().decode(errors="replace").strip()
        err = stderr.read().decode(errors="replace").strip()

        if exit_status != 0:
            detail = err or out or f"Command exited with status {exit_status}"
            return False, detail

        return True, out

    except Exception as e:
        return False, str(e)

    finally:
        if client is not None:
            client.close()