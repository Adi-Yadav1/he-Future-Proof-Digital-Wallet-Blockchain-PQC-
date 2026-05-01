import time

from pqc_crypto import (
    generate_keypair,
    generate_lamport_keypair,
    sign_message,
    verify_signature,
)


def _avg(values):
    return sum(values) / len(values) if values else 0.0


def benchmark_lamport(iterations=5):
    keygen_times = []
    sign_times = []
    verify_times = []
    signature_sizes = []
    message = "benchmark-message-lamport"

    for _ in range(iterations):
        start = time.perf_counter()
        private_key, public_key = generate_lamport_keypair()
        keygen_times.append(time.perf_counter() - start)

        start = time.perf_counter()
        signature = sign_message(message, private_key)
        sign_times.append(time.perf_counter() - start)

        start = time.perf_counter()
        valid = verify_signature(message, signature, public_key)
        verify_times.append(time.perf_counter() - start)

        if not valid:
            raise RuntimeError("Lamport verification failed during benchmark")

        signature_sizes.append(sum(len(chunk) for chunk in signature))

    return {
        "keygen_ms": _avg(keygen_times) * 1000,
        "sign_ms": _avg(sign_times) * 1000,
        "verify_ms": _avg(verify_times) * 1000,
        "signature_bytes": int(_avg(signature_sizes)),
    }


def benchmark_dilithium(iterations=20):
    keygen_times = []
    sign_times = []
    verify_times = []
    signature_sizes = []
    message = "benchmark-message-dilithium"

    for _ in range(iterations):
        start = time.perf_counter()
        private_key, public_key = generate_keypair()
        keygen_times.append(time.perf_counter() - start)

        start = time.perf_counter()
        signature = sign_message(message, private_key)
        sign_times.append(time.perf_counter() - start)

        start = time.perf_counter()
        valid = verify_signature(message, signature, public_key)
        verify_times.append(time.perf_counter() - start)

        if not valid:
            raise RuntimeError("Dilithium verification failed during benchmark")

        # signature is base64 for Dilithium; convert to raw bytes size estimate
        signature_sizes.append((len(signature) * 3) // 4)

    return {
        "keygen_ms": _avg(keygen_times) * 1000,
        "sign_ms": _avg(sign_times) * 1000,
        "verify_ms": _avg(verify_times) * 1000,
        "signature_bytes": int(_avg(signature_sizes)),
    }


def print_comparison(lamport, dilithium):
    print("\n=== PQC Benchmark: Lamport vs Dilithium2 ===")
    print(f"Lamport   keygen: {lamport['keygen_ms']:.3f} ms")
    print(f"Dilithium keygen: {dilithium['keygen_ms']:.3f} ms")
    print(f"Lamport   sign:   {lamport['sign_ms']:.3f} ms")
    print(f"Dilithium sign:   {dilithium['sign_ms']:.3f} ms")
    print(f"Lamport   verify: {lamport['verify_ms']:.3f} ms")
    print(f"Dilithium verify: {dilithium['verify_ms']:.3f} ms")
    print(f"Lamport   signature size: {lamport['signature_bytes']} bytes")
    print(f"Dilithium signature size: {dilithium['signature_bytes']} bytes")


if __name__ == "__main__":
    lamport_result = benchmark_lamport(iterations=5)
    dilithium_result = benchmark_dilithium(iterations=20)
    print_comparison(lamport_result, dilithium_result)
