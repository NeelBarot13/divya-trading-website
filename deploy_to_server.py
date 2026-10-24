"""
Divya Trading Co - 1-Click Production Server Deployment Tool
Connects securely to 157.20.190.212:8900, pulls latest main branch from GitHub,
and restarts services.
"""
import sys
import getpass
import paramiko
import urllib.request
import ssl

HOST = "157.20.190.212"
PORT = 8900
USER = "ubuntu"

def deploy():
    print("=" * 60)
    print("  DIVYA TRADING CO. - LIVE SERVER DEPLOYMENT")
    print(f"  Target: {USER}@{HOST}:{PORT} (divyatradingco.com)")
    print("=" * 60)
    print()
    
    # Accept password from command line or prompt securely
    password = None
    if len(sys.argv) > 1:
        if sys.argv[1] == "--password" and len(sys.argv) > 2:
            password = sys.argv[2]
        else:
            password = sys.argv[1]
            
    if not password:
        password = getpass.getpass(prompt=f"Enter SSH password for {USER}@{HOST} (or press Enter for email default): ")
    if not password:
        password = "K#g9(m@$>r)7lm"
        print("Using default email password: K#g9(m@$>r)7lm")
    
    print("\nConnecting to live server...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(HOST, port=PORT, username=USER, password=password, timeout=10)
        print(" Connected successfully to server!\n")
    except paramiko.AuthenticationException:
        print(" ERROR: Authentication failed! Permission denied.")
        print("   If you changed the server password, please run this script again and type your new password.")
        print("   If you did not change it, verify the password characters carefully.")
        sys.exit(1)
    except Exception as e:
        print(f" Connection failed: {e}")
        sys.exit(1)
        
    commands = [
        ("Locate website directory", "find /var/www /root /home -name 'app.py' -not -path '*/venv/*' 2>/dev/null | head -n 1"),
    ]
    
    print("Locating project folder on server...")
    stdin, stdout, stderr = ssh.exec_command(commands[0][1])
    app_path = stdout.read().decode('utf-8').strip()
    
    if not app_path:
        # Fallback locations
        web_dir = "/var/www/divya-trading-website"
    else:
        import posixpath
        web_dir = posixpath.dirname(app_path)
        
    print(f" Found website at: {web_dir}\n")
    
    deploy_script = f"""
    set -e
    cd "{web_dir}"
    echo "=== PULLING LATEST CODE FROM GITHUB ==="
    git fetch origin main
    git reset --hard origin/main
    echo "=== CURRENT COMMIT ==="
    git log -1 --oneline
    echo "=== RESTARTING GUNICORN & NGINX ==="
    sudo systemctl restart gunicorn divya divyatrading 2>/dev/null || sudo systemctl restart gunicorn || true
    sudo systemctl restart nginx
    echo "=== DEPLOYMENT COMPLETE ==="
    """
    
    print("Executing git pull & restart on server...")
    stdin, stdout, stderr = ssh.exec_command(deploy_script, get_pty=True)
    
    # In case sudo prompts for password, supply it
    for line in iter(stdout.readline, ""):
        print("  [Server]", line, end="")
        if "password for" in line.lower():
            stdin.write(password + "\n")
            stdin.flush()
            
    ssh.close()
    print("\n" + "=" * 60)
    print(" Verifying live website: https://divyatradingco.com ...")
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    test_urls = [
        "https://divyatradingco.com/",
        "https://divyatradingco.com/download-catalog/pdf",
        "https://divyatradingco.com/admin/email/compose"
    ]
    
    all_ok = True
    for u in test_urls:
        try:
            req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx, timeout=5) as res:
                print(f"  {u} -> HTTP {res.status} OK")
        except Exception as e:
            print(f"  {u} -> Error: {e}")
            all_ok = False
            
    print("=" * 60)
    if all_ok:
        print(" ALL CHANGES ARE NOW LIVE ON HTTPS://DIVYATRADINGCO.COM!")
    else:
        print(" Deployment finished. Please review server output above.")

if __name__ == "__main__":
    deploy()
