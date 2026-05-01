import requests


class NodeNetwork:
    """Simple networking helper for peer management and propagation."""

    def __init__(self, node_id, socketio_client=None, timeout=5):
        self.node_id = node_id
        self.peers = set()
        self.socketio = socketio_client
        self.timeout = timeout

    def _normalize_peer(self, peer_url):
        return str(peer_url).rstrip("/")

    def has_peer(self, peer_url):
        normalized = self._normalize_peer(peer_url)
        return normalized in self.peers

    def register_peer(self, peer_url):
        """Register a peer URL in local peer set."""
        normalized = self._normalize_peer(peer_url)
        if normalized:
            self.peers.add(normalized)
        return normalized

    def remove_peer(self, peer_url):
        """Remove a peer URL from local peer set."""
        normalized = self._normalize_peer(peer_url)
        self.peers.discard(normalized)
        return normalized

    def broadcast_transaction(self, tx):
        """Broadcast a validated transaction to all known peers."""
        payload = dict(tx)
        payload["propagated_by"] = self.node_id

        for peer in list(self.peers):
            try:
                requests.post(
                    f"{peer}/add_transaction",
                    json=payload,
                    timeout=self.timeout,
                )
            except requests.RequestException:
                # Dead peers are removed to keep the peer list healthy.
                self.remove_peer(peer)

        if self.socketio is not None:
            self.socketio.emit("transaction_propagated", payload)

    def broadcast_block(self, block):
        """Broadcast a newly mined block to all known peers."""
        payload = {
            "block": block,
            "propagated_by": self.node_id,
        }

        for peer in list(self.peers):
            try:
                requests.post(
                    f"{peer}/nodes/receive_block",
                    json=payload,
                    timeout=self.timeout,
                )
            except requests.RequestException:
                self.remove_peer(peer)

        if self.socketio is not None:
            self.socketio.emit("block_propagated", payload)

    def sync_chain(self, peer_url):
        """Fetch chain data from a peer for conflict resolution/sync."""
        normalized = self._normalize_peer(peer_url)
        response = requests.get(f"{normalized}/chain", timeout=self.timeout)
        response.raise_for_status()
        return response.json()
