"""
morphic_memory — Public API + Demo
====================================
Author: swordenkisk | github.com/swordenkisk/morphic_memory
"""

import sys, math
sys.path.insert(0, "..")

from morphic_memory.core.memory_manifold import MemoryManifold
from morphic_memory.attractor.hopfield_engine import ModernHopfieldEngine


class MorphicMemory:
    """
    morphic_memory public API.

    Combines:
      - Riemannian memory manifold (geometric recall)
      - Modern Hopfield network   (attractor dynamics)
      - Morphic resonance field   (self-reinforcing patterns)
    """

    def __init__(self, dimensions: int = 128, sigma: float = 0.8):
        self.manifold = MemoryManifold(dimensions, sigma)
        self.hopfield = ModernHopfieldEngine(beta=2.0)
        self.dim      = dimensions

    def encode(self, content, basin_depth: float = 1.0):
        trace  = self.manifold.encode(content, basin_depth)
        vector = self.manifold._vectorize(content)
        self.hopfield.store(vector)
        return trace

    def recall(self, query, max_distance: float = float('inf')):
        return self.manifold.recall(query, max_distance)

    def recall_top_k(self, query, k: int = 3):
        return self.manifold.recall_top_k(query, k)

    def resonate(self, pattern, sigma=None):
        return self.manifold.resonate(pattern, sigma)

    def topology(self):
        return self.manifold.topology()

    def stats(self):
        return self.manifold.stats()


# ─── Demo ─────────────────────────────────────────────────────────

def run_demo():
    print("=" * 65)
    print("  morphic_memory — Riemannian Memory Engine Demo")
    print("  Memory as curvature in information space")
    print("  Author: swordenkisk | March 2026")
    print("=" * 65)

    mem = MorphicMemory(dimensions=64, sigma=0.9)

    # ── Encode Memories ───────────────────────────────────────────
    knowledge = [
        ("physics",    "Einstein's E=mc² unifies mass and energy"),
        ("physics",    "Quantum mechanics describes subatomic behavior"),
        ("physics",    "The speed of light is constant in all frames"),
        ("biology",    "DNA carries genetic information via base pairs"),
        ("biology",    "Evolution proceeds through natural selection"),
        ("biology",    "Cells are the fundamental unit of life"),
        ("math",       "Riemann manifolds generalize Euclidean geometry"),
        ("math",       "Topology studies properties preserved under deformation"),
        ("algeria",    "Algeria gained independence in 1962"),
        ("algeria",    "The Sahara Desert covers most of southern Algeria"),
    ]

    print("\n📚 Encoding memories into the Riemannian manifold...\n")
    for domain, fact in knowledge:
        depth = 1.5 if domain == "physics" else 1.0
        mem.encode(fact, basin_depth=depth)
        print(f"  ✅ [{domain:8s}] {fact[:55]}")

    print(f"\n{mem.stats()}")

    # ── Recall ────────────────────────────────────────────────────
    print("─" * 65)
    print("🧠 RECALL — Geodesic retrieval from partial queries:\n")

    queries = [
        "light speed relativity",
        "genetic DNA heredity",
        "curved space geometry",
        "North Africa history",
    ]
    for query in queries:
        results = mem.recall_top_k(query, k=2)
        print(f"  Query: '{query}'")
        for r in results:
            print(f"    {r}")
        print()

    # ── Morphic Resonance ─────────────────────────────────────────
    print("─" * 65)
    print("🌀 MORPHIC RESONANCE — What resonates with 'quantum energy'?\n")
    resonant = mem.resonate("quantum energy field")
    for r in resonant[:4]:
        print(f"  {r}")

    # ── Modern Hopfield ───────────────────────────────────────────
    print("\n─" * 65)
    print("⚡ HOPFIELD ATTRACTOR DYNAMICS:\n")
    cap = mem.hopfield.storage_capacity(64)
    sep = mem.hopfield.separation_threshold()
    print(f"  Memories stored        : {mem.hopfield.n_memories}")
    print(f"  Theoretical capacity   : {cap:.0f} patterns (exp(n/2) law)")
    print(f"  Separation threshold   : {sep:.4f} rad")

    query_vec = mem.manifold._vectorize("Einstein relativity mass")
    result    = mem.hopfield.retrieve(query_vec)
    print(f"  Retrieval converged    : {'✅' if result.converged else '⚠️'}")
    print(f"  Steps to convergence   : {result.steps}")
    print(f"  Attractor energy       : {result.energy:.4f}")
    top_weights = sorted(enumerate(result.retrieval_pattern), key=lambda x: -x[1])[:3]
    print(f"  Top attractor weights  : {[(i, f'{w:.3f}') for i,w in top_weights]}")

    # ── Topology ──────────────────────────────────────────────────
    print("\n─" * 65)
    print("🔭 KNOWLEDGE TOPOLOGY:\n")
    topo = mem.topology()
    print(topo)

    print("=" * 65)
    print("  🇩🇿 Memory as geometry. Recall as gravity.")
    print("  morphic_memory — swordenkisk, March 2026")
    print("=" * 65)


if __name__ == "__main__":
    run_demo()
