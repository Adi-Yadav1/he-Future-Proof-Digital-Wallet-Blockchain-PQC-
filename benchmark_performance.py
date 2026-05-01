import time
from statistics import mean

from blockchain import Blockchain
from pqc_crypto import decrypt_message, encrypt_message, generate_kem_keypair
from transaction import Transaction
from wallet import Wallet

try:
    from pqcrypto.kem import kyber512 as kem_kyber512
except ImportError:
    from pqcrypto.kem import ml_kem_512 as kem_kyber512


RUNS = 100


def avg_ms(samples):
    return mean(samples) * 1000 if samples else 0.0


def benchmark_dilithium():
    keygen_times = []
    sign_times = []
    verify_times = []

    for _ in range(RUNS):
        t0 = time.perf_counter()
        wallet = Wallet()
        keygen_times.append(time.perf_counter() - t0)

        msg = "benchmark-message"
        t1 = time.perf_counter()
        signature = wallet.sign(msg)
        sign_times.append(time.perf_counter() - t1)

        t2 = time.perf_counter()
        from pqc_crypto import verify_signature

        verify_signature(msg, signature, wallet.public_key)
        verify_times.append(time.perf_counter() - t2)

    return {
        "Dilithium": {
            "Key Generation": avg_ms(keygen_times),
            "Signing": avg_ms(sign_times),
            "Verification": avg_ms(verify_times),
        }
    }


def benchmark_kyber():
    encapsulation_times = []
    decapsulation_times = []
    encrypt_times = []
    decrypt_times = []

    private_key, public_key = generate_kem_keypair()
    pk_bytes = __import__("base64").b64decode(public_key.encode("ascii"))
    sk_bytes = __import__("base64").b64decode(private_key.encode("ascii"))

    for _ in range(RUNS):
        t0 = time.perf_counter()
        encapsulated, _shared_secret = kem_kyber512.encrypt(pk_bytes)
        encapsulation_times.append(time.perf_counter() - t0)

        t1 = time.perf_counter()
        kem_kyber512.decrypt(sk_bytes, encapsulated)
        decapsulation_times.append(time.perf_counter() - t1)

        payload = {"receiver": "bench", "amount": 12.34}
        t2 = time.perf_counter()
        encrypted = encrypt_message(public_key, payload)
        encrypt_times.append(time.perf_counter() - t2)

        t3 = time.perf_counter()
        decrypt_message(private_key, encrypted)
        decrypt_times.append(time.perf_counter() - t3)

    return {
        "Kyber": {
            "Encapsulation": avg_ms(encapsulation_times),
            "Decapsulation": avg_ms(decapsulation_times),
            "Encryption": avg_ms(encrypt_times),
            "Decryption": avg_ms(decrypt_times),
        }
    }


def benchmark_blockchain():
    mining_times = []
    verify_times = []

    chain = Blockchain(difficulty=1, reward_enabled=False)
    sender = Wallet()
    receiver = Wallet()

    verify_samples = 0
    verify_t0 = time.perf_counter()

    for _ in range(RUNS):
        draft = Transaction(
            sender=sender.get_address(),
            receiver=receiver.get_address(),
            amount=5.0,
            signature=None,
            public_key=None,
        )
        draft.signature = sender.sign(draft.calculate_hash())
        draft.public_key = sender.public_key

        t0 = time.perf_counter()
        chain.add_block([draft], sender)
        mining_times.append(time.perf_counter() - t0)

        if draft.verify():
            verify_samples += 1

    verify_elapsed = time.perf_counter() - verify_t0
    avg_verify_ms = (verify_elapsed / max(1, RUNS)) * 1000
    throughput = verify_samples / max(verify_elapsed, 1e-9)

    return {
        "Blockchain": {
            "Block Mining": avg_ms(mining_times),
            "Tx Verify Avg": avg_verify_ms,
            "Tx Verify Throughput": throughput,
        }
    }


def print_table(rows):
    print("Algorithm | Operation | Avg Time (ms)")
    print("---|---|---")
    for algorithm, operation, value in rows:
        print(f"{algorithm} | {operation} | {value:.4f}")


def main():
    results = {}
    results.update(benchmark_dilithium())
    results.update(benchmark_kyber())
    results.update(benchmark_blockchain())

    rows = []
    for algorithm, operations in results.items():
        for op_name, value in operations.items():
            if op_name == "Tx Verify Throughput":
                # Throughput is printed separately because units are tx/sec.
                continue
            rows.append((algorithm, op_name, value))

    print_table(rows)
    print(f"\nBlockchain | Tx Verify Throughput | {results['Blockchain']['Tx Verify Throughput']:.2f} tx/sec")


if __name__ == "__main__":
    main()
