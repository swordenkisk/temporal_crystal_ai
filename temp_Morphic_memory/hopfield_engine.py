"""
morphic_memory — Modern Hopfield Engine
=========================================
Implements Modern Hopfield Networks (Ramsauer et al. 2020)
and their connection to Transformer attention mechanisms.

Key results:
  Classical Hopfield (1982): stores O(n) memories in n neurons
  Modern Hopfield  (2020): stores exp(n/2) memories — exponential!
  Transformer attention = ONE STEP of Modern Hopfield retrieval

Energy function:
  E(x) = -LSE(β, Xᵀx) + ½‖x‖² + (1/β)log(M) + ½n

  where:
    LSE(β, z) = (1/β) log Σₖ exp(βzₖ)   (log-sum-exp)
    X = [x₁,...,xₘ] stored memories (columns)
    β = inverse temperature (controls separation)
    M = number of stored memories

Update rule (one step retrieves memory):
  x(t+1) = X · softmax(β · Xᵀ · x(t))

This IS the attention mechanism:
  Attention(Q,K,V) = V · softmax(QKᵀ/√d)
  ≡ Hopfield retrieval with Q=query, K=V=memories, β=1/√d

Author  : swordenkisk (https://github.com/swordenkisk)
Created : March 2026
"""

import math
from typing import List, Optional, Tuple
from dataclasses import dataclass


def log_sum_exp(beta: float, values: List[float]) -> float:
    """
    Numerically stable log-sum-exp:
    LSE(β, z) = (1/β) log Σₖ exp(β·zₖ)
    """
    if not values:
        return 0.0
    max_v  = max(values)
    total  = sum(math.exp(beta * (v - max_v)) for v in values)
    return max_v + (1/beta) * math.log(total + 1e-12)


def softmax(beta: float, values: List[float]) -> List[float]:
    """
    Softmax with inverse temperature β:
    pₖ = exp(β·zₖ) / Σⱼ exp(β·zⱼ)
    """
    max_v = max(values) if values else 0.0
    exps  = [math.exp(beta * (v - max_v)) for v in values]
    total = sum(exps) + 1e-12
    return [e / total for e in exps]


def dot(a: List[float], b: List[float]) -> float:
    """Inner product ⟨a, b⟩."""
    return sum(x*y for x, y in zip(a, b))


def norm(v: List[float]) -> float:
    """Euclidean norm ‖v‖."""
    return math.sqrt(sum(x**2 for x in v))


@dataclass
class HopfieldRetrievalResult:
    retrieved_vector : List[float]
    energy           : float
    steps            : int
    converged        : bool
    retrieval_pattern: List[float]   # softmax weights — which memories contributed


class ModernHopfieldEngine:
    """
    Modern Hopfield Network with exponential storage capacity.

    Storage capacity: M* = exp(n/2) / (2·n·√(n))  patterns
    Retrieval: ONE update step sufficient for well-separated memories.

    The deep connection to Transformers (Ramsauer et al. 2020):
      x(t+1) = X · softmax(β · Xᵀ · x(t))
                 ↕
      Attention = V · softmax(QKᵀ / √d)

    This means: EVERY TRANSFORMER IS A HOPFIELD NETWORK.
    morphic_memory makes this explicit — memory AS attention,
    attention AS geometry.

    Author: swordenkisk, March 2026.
    """

    def __init__(self, beta: float = 2.0, max_steps: int = 20, eps: float = 1e-5):
        self.beta      = beta        # Inverse temperature
        self.max_steps = max_steps
        self.eps       = eps
        self._memories : List[List[float]] = []   # Stored patterns (columns of X)

    def store(self, pattern: List[float]):
        """Store a pattern in the Hopfield memory."""
        # Normalize to unit sphere (standard for Hopfield)
        n = norm(pattern)
        self._memories.append([x / (n + 1e-12) for x in pattern])

    def energy(self, x: List[float]) -> float:
        """
        Modern Hopfield energy:
        E(x) = -LSE(β, Xᵀx) + ½‖x‖² + C
        """
        if not self._memories:
            return 0.0
        overlaps = [dot(m, x) for m in self._memories]
        return -log_sum_exp(self.beta, overlaps) + 0.5 * sum(xi**2 for xi in x)

    def retrieve(self, query: List[float]) -> HopfieldRetrievalResult:
        """
        Retrieve the stored memory nearest to query.

        Update rule (one step often sufficient):
          x(t+1) = Σₖ pₖ(t) · mₖ
          where pₖ(t) = softmax(β · ⟨mₖ, x(t)⟩)

        This is equivalent to scaled dot-product attention.
        """
        if not self._memories:
            return HopfieldRetrievalResult(query, 0.0, 0, False, [])

        # Normalize query
        n = norm(query)
        x = [xi / (n + 1e-12) for xi in query]

        for step in range(self.max_steps):
            # Compute overlaps: ⟨mₖ, x⟩ for all stored memories
            overlaps = [dot(m, x) for m in self._memories]

            # Softmax weights: attention pattern
            weights  = softmax(self.beta, overlaps)

            # Update: weighted combination of memories
            dim = len(self._memories[0])
            x_new = [0.0] * dim
            for k, (mem, w) in enumerate(zip(self._memories, weights)):
                for i in range(min(dim, len(mem))):
                    x_new[i] += w * mem[i]

            # Check convergence
            change = norm([x_new[i]-x[i] for i in range(len(x_new))])
            x = x_new
            if change < self.eps:
                return HopfieldRetrievalResult(
                    retrieved_vector  = x,
                    energy            = self.energy(x),
                    steps             = step + 1,
                    converged         = True,
                    retrieval_pattern = weights,
                )

        return HopfieldRetrievalResult(
            retrieved_vector  = x,
            energy            = self.energy(x),
            steps             = self.max_steps,
            converged         = False,
            retrieval_pattern = softmax(self.beta, [dot(m, x) for m in self._memories]),
        )

    def storage_capacity(self, n: int) -> float:
        """
        Theoretical maximum storage capacity for n-dimensional patterns.
        Modern Hopfield: C ≈ exp(n/2) / (2n√n)
        """
        return math.exp(n / 2) / (2 * n * math.sqrt(n))

    def separation_threshold(self) -> float:
        """
        Minimum separation between memories for perfect retrieval.
        Δ* = 2 · arccos(1 - 1/(2M²))   where M = number of memories
        """
        M = len(self._memories)
        if M < 2:
            return math.pi
        arg = max(-1.0, min(1.0, 1 - 1/(2*M**2)))
        return 2 * math.acos(arg)

    @property
    def n_memories(self) -> int:
        return len(self._memories)
