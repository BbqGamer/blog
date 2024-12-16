# Script to deploy the hugo site to the server. It assumes that the server
# is reachable via ssh configured in ~/.ssh/config with hostname $REMOTE_SSH_HOST
# and that it has the webserver configured to serve content from the $REMOTE_DIR directory.

if [ -z "$REMOTE_SSH_HOST" ]; then
  echo "Please set REMOTE_SSH_HOST"
  exit 1
fi

if [ -z "$REMOTE_DIR" ]; then
  echo "Please set REMOTE_DIR"
  exit 1
fi

hugo

if [ -z "$REMOTE_SSH_PORT" ]; then
    rsync -avz --delete public/ $REMOTE_SSH_HOST:$REMOTE_DIR
else
    rsync -avze "ssh -p $REMOTE_SSH_PORT" --delete public/ $REMOTE_SSH_HOST:$REMOTE_DIR
fi
