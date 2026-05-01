"""Educational simulation of a quantum attack concept on classical signatures.

This script does NOT implement Shor's algorithm.  Instead it uses a tiny toy
elliptic-curve-like setting where private-key recovery is brute-force feasible,
then explains why Shor would scale that idea to real-world curves.
"""


def toy_discrete_log_attack() -> tuple[int, int, int]:
    """Recover x from y = g^x mod p in a tiny group by brute force.

    This is a conceptual stand-in for solving discrete logarithms.
    """
    p = 1019
    g = 2
    private_key = 137
    public_key = pow(g, private_key, p)

    recovered = None
    for guess in range(1, p):
        if pow(g, guess, p) == public_key:
            recovered = guess
            break

    return private_key, public_key, recovered if recovered is not None else -1


def main() -> None:
    original, public, recovered = toy_discrete_log_attack()

    print("=== Quantum Attack Simulation (Educational) ===")
    print("Context:")
    print("- Classical ECDSA security relies on hardness of elliptic-curve discrete log.")
    print("- Shor's algorithm solves discrete log in polynomial time on a large quantum computer.")

    print("\nToy Demonstration:")
    print("- We use a tiny group where brute force can recover the private key quickly.")
    print(f"- Public value observed: {public}")
    print(f"- Recovered secret value: {recovered}")
    print(f"- Recovery successful: {recovered == original}")

    print("\nAttack Interpretation:")
    print("1. In classical blockchain systems, public keys are visible to all peers.")
    print("2. A quantum attacker can run Shor's algorithm against exposed ECDSA keys.")
    print("3. Recovered private keys allow forging signatures and stealing funds.")
    print("4. Blockchain trust collapses because forged transactions look valid.")

    print("\nWhy PQC helps:")
    print("- Dilithium (ML-DSA) and Kyber (ML-KEM) are designed to resist known quantum attacks.")
    print("- They are based on lattice problems, not discrete logarithms.")


if __name__ == "__main__":
    main()
