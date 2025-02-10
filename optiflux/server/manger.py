import os

LOCK_FILE = ".deploy_lock"

def deploy():
    """Run deployment tasks."""
    if os.path.exists(LOCK_FILE):
        print("Deploy has already been run. Skipping...")
        return

    from .app import create_app, db
    from flask_migrate import upgrade, migrate, init, stamp
    from .models import User

    app = create_app()
    app.app_context().push()
    db.create_all()

    # migrate database to latest revision
    init()
    stamp()
    migrate()
    upgrade()

    # Create lock file to indicate deploy has been run
    with open(LOCK_FILE, "w") as f:
        f.write("Deploy has been run.")

# 在 base.py 中
# deploy()
