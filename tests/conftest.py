import pytest

from blockchain import Blockchain
from wallet import Wallet


@pytest.fixture
def wallet_pair():
    """Create two temporary wallets for isolated tests."""
    return Wallet(), Wallet()


@pytest.fixture
def temp_blockchain():
    """Use low PoW difficulty so tests complete quickly."""
    return Blockchain(difficulty=1, reward_enabled=False)


@pytest.fixture
def temp_transaction_pool():
    """Dedicated in-memory pool to avoid touching persistent demo pools."""
    return []
