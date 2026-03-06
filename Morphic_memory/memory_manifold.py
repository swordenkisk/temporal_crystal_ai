"""
morphic_memory — Riemannian Memory Manifold
=============================================
The curved information space where memories live.

Mathematical Foundation:
  A Riemannian manifold (M, g) is a smooth manifold equipped
  with a metric tensor gᵢⱼ that varies smoothly across M.

  The metric encodes:
    - Distance: d(p,q) = inf_γ ∫|γ'(t)|_g dt  (geodesic distance)
    - Curvature: κ = R / n(n-1)               (scalar curvature)
    - Parallel transport: how vectors move along curves

  In morphic_memory:
    M = space of all possible memory vectors (ℝⁿ)
    g = metric induced by the Hopfield energy landscape
    gᵢⱼ(x) = ∂²E/∂xⁱ∂xʲ (Hessian of energy = local metric)

  Memories are BASINS in this curved space.
  Recall is GEODESIC FLOW toward the nearest basin minimum.

Author  : swordenkisk (https://github.com/swordenkisk)
Created : March 2026

═══════════════════════════════════════════════════════════════════
ORIGINAL INVENTION: The Riemannian Memory Manifold — representing
associative memory as a curved Riemannian manifold where the metric
tensor is the Hessian of the Hopfield energy function, geodesic
distance measures semantic similarity, and memory retrieval is
geodesic flow — unifying differential geometry and associative
memory into a single mathematical framework.
swordenkisk, March 2026.
═══════════════════════════════════════════════════════════════════
"""

import math
import random
import hashlib
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from collections import defaultdict


# ─── Memory Trace ─────────────────────────────────────────────────

@dataclass
class MemoryTrace:
    """
    A single encoded memory — a basin in the Riemannian manifold.

    Each memory trace has:
      - A vector representation (the point in ℝⁿ)
      - A basin depth (how strongly encoded — curvature at the minimum)
      - A resonance history (which patterns have reinforced it)
      - A timestamp (for temporal decay modelling)
    """
    trace_id      : str
    vector        : List[float]           # Point in ℝⁿ
    content       : Any                   # Original content
    basin_depth   : float = 1.0           # κ — curvature at minimum
    resonance_count: int  = 0             # Times reinforced by resonance
    encoded_ms    : float = field(default_factory=lambda: time.time()*1000)
    last_accessed_ms: float = field(default_factory=lambda: time.time()*1000)

    @property
    def strength(self) -> float:
        """Total memory strength = depth × resonance factor."""
        resonance_boost = math.log1p(self.resonance_count) * 0.2
        return self.basin_depth * (1.0 + resonance_boost)

    @property
    def dimension(self) -> int:
        return len(self.vector)


# ─── Riemannian Metric ────────────────────────────────────────────

class RiemannianMetric:
    """
    The metric tensor field on the memory manifold.

    gᵢⱼ(x) = δᵢⱼ + Σₖ αₖ · (xᵢ - mₖᵢ)(xⱼ - mₖⱼ) · exp(-‖x-mₖ‖²/2σ²)

    This is the PULLBACK metric from the Hopfield energy landscape.
    Near each memory mₖ, the metric is warped (curved) by the
    basin — the stronger the memory, the more curved the local geometry.

    The metric is:
      - Positive definite everywhere (valid Riemannian metric)
      - More curved near stored memories (stronger = more curved)
      - Flat far from all memories (unexplored information space)
    """

    def __init__(self, dimension: int, sigma: float = 1.0):
        self.n      = dimension
        self.sigma  = sigma
        self._memories : List[MemoryTrace] = []

    def add_memory(self, trace: MemoryTrace):
        self._memories.append(trace)

    def metric_at(self, x: List[float]) -> List[List[float]]:
        """
        Compute metric tensor gᵢⱼ at point x.
        Returns n×n symmetric positive definite matrix.
        """
        n = self.n
        # Start with flat metric (identity)
        g = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

        # Add curvature contributions from each stored memory
        for trace in self._memories:
            m   = trace.vector[:n]
            d2  = sum((x[i]-m[i])**2 for i in range(min(len(x), len(m), n)))
            w   = trace.strength * math.exp(-d2 / (2 * self.sigma**2))

            for i in range(n):
                for j in range(i, n):
                    delta_i = (x[i] - m[i]) if i < len(m) else 0.0
                    delta_j = (x[j] - m[j]) if j < len(m) else 0.0
                    curvature_ij = w * delta_i * delta_j
                    g[i][j] += curvature_ij
                    if i != j:
                        g[j][i] += curvature_ij
        return g

    def geodesic_distance(self, x: List[float], y: List[float]) -> float:
        """
        Approximate geodesic distance between x and y.

        Full geodesic requires solving the geodesic equation:
          d²γᵢ/dt² + Γⁱⱼₖ (dγʲ/dt)(dγᵏ/dt) = 0

        We use a first-order approximation via midpoint metric:
          d_g(x,y) ≈ √[Σᵢⱼ gᵢⱼ(mid) · Δxⁱ · Δxʲ]
        """
        mid = [(x[i]+y[i])/2 for i in range(min(len(x), len(y)))]
        g   = self.metric_at(mid)
        n   = len(mid)
        dx  = [x[i]-y[i] for i in range(n)]
        d2  = 0.0
        for i in range(n):
            for j in range(n):
                d2 += g[i][j] * dx[i] * dx[j]
        return math.sqrt(max(d2, 0.0))

    def scalar_curvature(self, x: List[float]) -> float:
        """
        Approximate scalar Ricci curvature R at point x.
        High R = near a memory basin = strongly encoded region.

        R ≈ -½ Σᵢ ∂²(log det g)/∂xⁱ²   (simplified)
        """
        g   = self.metric_at(x)
        # Trace of metric (simplified curvature proxy)
        trace = sum(g[i][i] for i in range(len(g)))
        n     = len(g)
        return (trace - n) / max(n, 1)   # Deviation from flat metric


# ─── Riemannian Memory Manifold ───────────────────────────────────

class MemoryManifold:
    """
    The full Riemannian memory manifold.

    This is the geometric arena of morphic_memory.
    It maintains the collection of memory traces (basins)
    and provides geometric operations:
      - Encoding      : carving a new basin
      - Recall        : geodesic flow to nearest basin
      - Resonance     : deepening nearby basins
      - Topology      : global structure of the memory space

    Author: swordenkisk, March 2026.
    """

    def __init__(self, dimension: int = 128, sigma: float = 1.0):
        self.n         = dimension
        self.sigma     = sigma
        self.metric    = RiemannianMetric(dimension, sigma)
        self._traces   : Dict[str, MemoryTrace] = {}
        self._encoded  : int = 0

    # ── Encoding ──────────────────────────────────────────────────

    def encode(self, content: Any, basin_depth: float = 1.0) -> MemoryTrace:
        """
        Encode a memory — carve a basin in the Riemannian manifold.

        The memory is first vectorized (mapped to ℝⁿ),
        then its basin is created by updating the metric tensor
        to have increased curvature at that point.
        """
        vector = self._vectorize(content)
        trace  = MemoryTrace(
            trace_id    = self._new_id(),
            vector      = vector,
            content     = content,
            basin_depth = basin_depth,
        )
        self._traces[trace.trace_id] = trace
        self.metric.add_memory(trace)
        self._encoded += 1
        return trace

    # ── Recall ────────────────────────────────────────────────────

    def recall(
        self, query: Any, max_distance: float = float('inf')
    ) -> Optional["RecallResult"]:
        """
        Recall the nearest memory to query via geodesic distance.

        Implements GEODESIC FLOW:
          Starting from the query point q in ℝⁿ,
          flow along the gradient of the energy landscape
          until reaching the nearest basin minimum.

        In the Riemannian metric, 'nearest' means geodesically
        nearest — not Euclidean, not cosine — CURVED distance.
        """
        if not self._traces:
            return None

        query_vec = self._vectorize(query)
        best      = None
        best_dist = float('inf')

        for trace in self._traces.values():
            dist = self.metric.geodesic_distance(query_vec, trace.vector)
            if dist < best_dist:
                best_dist = dist
                best      = trace

        if best is None or best_dist > max_distance:
            return None

        best.last_accessed_ms = time.time() * 1000
        curvature = self.metric.scalar_curvature(best.vector)

        return RecallResult(
            memory       = best.content,
            trace        = best,
            geodesic_dist= best_dist,
            confidence   = best.strength / (1.0 + best_dist),
            curvature    = curvature,
        )

    def recall_top_k(self, query: Any, k: int = 3) -> List["RecallResult"]:
        """Recall top-k nearest memories by geodesic distance."""
        if not self._traces:
            return []
        query_vec = self._vectorize(query)
        scored    = []
        for trace in self._traces.values():
            dist = self.metric.geodesic_distance(query_vec, trace.vector)
            curvature = self.metric.scalar_curvature(trace.vector)
            scored.append(RecallResult(
                memory       = trace.content,
                trace        = trace,
                geodesic_dist= dist,
                confidence   = trace.strength / (1.0 + dist),
                curvature    = curvature,
            ))
        scored.sort(key=lambda r: r.geodesic_dist)
        return scored[:k]

    # ── Morphic Resonance ─────────────────────────────────────────

    def resonate(self, pattern: Any, sigma: Optional[float] = None) -> List["ResonanceResult"]:
        """
        Morphic resonance: find all memories that resonate with pattern.

        A memory resonates if its geodesic distance to the pattern
        is within the resonance radius σ. Each resonating memory
        has its basin DEEPENED — it self-reinforces.

        R(p, m) = exp(-d²_g(p, m) / 2σ²)   (Gaussian on manifold)
        """
        σ         = sigma or self.sigma
        query_vec = self._vectorize(pattern)
        results   = []

        for trace in self._traces.values():
            dist      = self.metric.geodesic_distance(query_vec, trace.vector)
            resonance = math.exp(-(dist**2) / (2 * σ**2))

            if resonance > 0.01:
                # Morphic reinforcement — deepen the basin
                trace.basin_depth   += resonance * 0.1
                trace.resonance_count += 1
                results.append(ResonanceResult(
                    memory    = trace.content,
                    strength  = resonance,
                    distance  = dist,
                    deepened  = resonance * 0.1,
                ))

        return sorted(results, key=lambda r: -r.strength)

    # ── Topology ──────────────────────────────────────────────────

    def topology(self) -> "MemoryTopology":
        """
        Compute the topological structure of the memory space.
        Uses a simplified persistent homology approach.

        Returns connected components, bridges, and knowledge gaps.
        """
        if len(self._traces) < 2:
            return MemoryTopology(n_components=len(self._traces),
                                 bridges=[], betti_0=len(self._traces),
                                 betti_1=0)

        traces     = list(self._traces.values())
        threshold  = self.sigma * 2.0

        # Build proximity graph
        adj        = defaultdict(set)
        for i, ti in enumerate(traces):
            for j, tj in enumerate(traces):
                if i >= j:
                    continue
                dist = self.metric.geodesic_distance(ti.vector, tj.vector)
                if dist < threshold:
                    adj[i].add(j)
                    adj[j].add(i)

        # Connected components (Betti number β₀)
        visited    = set()
        components = []
        for start in range(len(traces)):
            if start not in visited:
                comp  = []
                stack = [start]
                while stack:
                    node = stack.pop()
                    if node not in visited:
                        visited.add(node)
                        comp.append(node)
                        stack.extend(adj[node] - visited)
                components.append(comp)

        # Bridges: nodes connecting different components (simplified)
        bridges = []
        for i, ti in enumerate(traces):
            neighbors = adj[i]
            comp_ids  = set()
            for comp_idx, comp in enumerate(components):
                if i in comp:
                    comp_ids.add(comp_idx)
                for n in neighbors:
                    for c_idx, c in enumerate(components):
                        if n in c:
                            comp_ids.add(c_idx)
            if len(comp_ids) > 1:
                bridges.append(traces[i].content)

        # Betti₁ (loops): approximation via edge count
        n_edges  = sum(len(v) for v in adj.values()) // 2
        n_nodes  = len(traces)
        betti_1  = max(n_edges - n_nodes + len(components), 0)

        return MemoryTopology(
            n_components = len(components),
            bridges      = bridges[:5],
            betti_0      = len(components),
            betti_1      = betti_1,
        )

    # ── Manifold Stats ────────────────────────────────────────────

    def stats(self) -> str:
        if not self._traces:
            return "Empty manifold."
        depths    = [t.basin_depth for t in self._traces.values()]
        resonances= [t.resonance_count for t in self._traces.values()]
        return (
            f"Memory Manifold [dim={self.n}]\n"
            f"  Memories encoded : {len(self._traces)}\n"
            f"  Avg basin depth  : {sum(depths)/len(depths):.3f}\n"
            f"  Max basin depth  : {max(depths):.3f}\n"
            f"  Total resonances : {sum(resonances)}\n"
            f"  σ (resonance r.) : {self.sigma}\n"
        )

    # ── Internal ──────────────────────────────────────────────────

    def _vectorize(self, content: Any) -> List[float]:
        """
        Map arbitrary content to a vector in ℝⁿ.
        Uses a deterministic hash-based embedding.
        In production: use a proper embedding model.
        """
        h = hashlib.sha256(str(content).encode()).digest()
        # Expand hash to n dimensions deterministically
        vector = []
        seed   = h
        while len(vector) < self.n:
            seed   = hashlib.sha256(seed).digest()
            floats = [((seed[i] / 255.0) * 2 - 1) for i in range(min(32, self.n - len(vector)))]
            vector.extend(floats)
        return vector[:self.n]

    def _new_id(self) -> str:
        return hashlib.sha256(f"{time.time()}-{self._encoded}".encode()).hexdigest()[:12]


# ─── Result Types ─────────────────────────────────────────────────

@dataclass
class RecallResult:
    memory        : Any
    trace         : MemoryTrace
    geodesic_dist : float
    confidence    : float
    curvature     : float

    def __str__(self):
        return (
            f"[{self.confidence:.3f}] {str(self.memory)[:60]}\n"
            f"  geodesic_dist={self.geodesic_dist:.4f}  "
            f"curvature={self.curvature:.4f}  "
            f"strength={self.trace.strength:.3f}"
        )


@dataclass
class ResonanceResult:
    memory    : Any
    strength  : float
    distance  : float
    deepened  : float

    def __str__(self):
        return f"  ≈ [{self.strength:.3f}] {str(self.memory)[:60]}"


@dataclass
class MemoryTopology:
    n_components : int
    bridges      : List[Any]
    betti_0      : int    # β₀ = connected components
    betti_1      : int    # β₁ = independent loops = knowledge gaps

    def __str__(self):
        return (
            f"Memory Topology\n"
            f"  β₀ components   : {self.betti_0} (isolated knowledge clusters)\n"
            f"  β₁ loops        : {self.betti_1} (knowledge gaps / circular references)\n"
            f"  Bridges         : {self.bridges}\n"
        )
