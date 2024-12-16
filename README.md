# korba.online blog
[Link to the webpage](https://korba.online)

# Github actions setup
For automatic deployment you need to setup secrets in your repository.
## SSH Key setup
1. Generate ssh keypair
```bash
ssh-keygen -t rsa -b 4096 -C "user@remote.com" -q -N ""
# specify the path to the key
```
Copy the private key to the secret `SSH_PRIVATE_KEY` in your repository.

2. Add the public key to your server's `~/.ssh/authorized_keys` file.
```bash
ssh-copy-id -i path_to_pubkey user@remote.com -p port
```

3. Enter the remote server and run:
```bash
ssh-keyscan 127.0.0.1
```
Copy the entry containing RSA key to secret `SSH_KNOWN_HOSTS` in your repository.

4. `REMOTE_SSH_HOST` - remote ssh server address
5. `REMOTE_SSH_PORT` - remote ssh server port
6. `REMOTE_DIR` - directory containing the static file of the website

