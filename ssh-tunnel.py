from sshtunnel import SSHTunnelForwarder

server = SSHTunnelForwarder(
    'pivpn.serveo.net',
    remote_bind_address=('127.0.0.1', 8194)
)

server.start()

print(server.local_bind_port)  # show assigned local port
# work with `SECRET SERVICE` through `server.local_bind_port`.

server.stop()