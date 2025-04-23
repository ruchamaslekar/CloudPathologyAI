import os
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

class ScyllaConnection:
    def __init__(self, keyspace):
        self.keyspace = keyspace
        self.cluster = None
        self.session = None

    def connect(self):
        self.cluster = Cluster([os.getenv('SCYLLA_HOST')], port=9042, auth_provider = PlainTextAuthProvider(username=os.getenv('SCYLLA_USER'), password=os.getenv('SCYLLA_PASS')))
        print("u:",os.getenv('SCYLLA_USER'))
        print("auth",PlainTextAuthProvider(username=os.getenv('SCYLLA_USER'), password=os.getenv('SCYLLA_PASS')).__dict__)
        print("p:",os.getenv('SCYLLA_USER'))
        print("Host: ",os.getenv('SCYLLA_HOST'))
        print("Cluster: ",str(self.cluster.__dict__))
        print("Keyspace: ",self.keyspace)
        self.session = self.cluster.connect(self.keyspace)
        print(f"Connected to {self.keyspace}")

    def close(self):
        if self.session:
            self.session.shutdown()
        if self.cluster:
            self.cluster.shutdown()
        print("Connection closed")

print("Connecting to scylladb")
scylla_connection = ScyllaConnection(keyspace='dev_keyspace')

def get_db_connection():
    if not scylla_connection.session:
        scylla_connection.connect()
    return scylla_connection