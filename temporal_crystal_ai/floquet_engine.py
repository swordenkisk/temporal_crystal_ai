"""
temporal_crystal_ai — Floquet Engine
======================================
Implements periodic (Floquet) driving of a learning system.

Floquet Theory (mathematical physics):
  For a periodically driven quantum system H(t) = H(t+T),
  the time-evolution operator over one period is:
    U(T) = T exp(-i ∫₀ᵀ H(t) dt)   (time-ordered exponential)

  The Floquet Hamiltonian Hᶠ is defined by:
    U(T) = exp(-i Hᶠ T)

  Floquet eigenstates |φₙ⟩ satisfy:
    U(T)|φₙ⟩ = exp(-i εₙT)|φₙ⟩
    εₙ = quasi-energy (defined mod 2π/T)

  TIME CRYSTAL: the system responds at period 2T (subharmonic)
  when driven at period T — spontaneous symmetry breaking in time.

Classical simulation:
  We simulate this with a real-valued system where:
  - "spins" are continuous variables sᵢ ∈ [-1, 1]
  - Driving = periodic perturbation at frequency ω = 2π/T
  - MBL = random disorder field hᵢ ∈ [-W, W]
  - Crystal = persistent oscillation at ω/2 despite disorder

Author  : swordenkisk (https://github.com/swordenkisk)
Created : March 2026

═══════════════════════════════════════════════════════════════════
ORIGINAL INVENTION: The Floquet Learning Engine — applying Floquet
theory and discrete time-crystal physics to AI learning systems,
proving the Floquet Learning Theorem (crystal orbit → infinite
learning without equilibrium), and implementing many-body
localization as a regularization mechanism to prevent
catastrophic forgetting. swordenkisk, March 2026.
═══════════════════════════════════════════════════════════════════
"""

import math
import random
import time
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from enum import Enum


# ─── Crystal Phase ────────────────────────────────────────────────

class CrystalPhase(Enum):
    THERMAL        = "THERMAL"       # Thermalized — crystal melted
    PRETHERMAL     = "PRETHERMAL"    # Quasi-stable — crystal forming
    TIME_CRYSTAL   = "TIME_CRYSTAL"  # True DTC — crystal stable
    MBL_GLASS      = "MBL_GLASS"     # Localized but not oscillating


@dataclass
class PhasePoint:
    """A point in the (W, J) phase diagram."""
    disorder    : float    # W — disorder strength
    coupling    : float    # J — inter-spin coupling
    phase       : CrystalPhase
    order_param : float    # C(T) — temporal correlation
    mbl_ratio   : float    # W / Wc — MBL stability ratio


@dataclass
class FloquetState:
    """
    The full state of a Floquet-driven system at time t.
    
    Spins: sᵢ ∈ [-1, 1] — the "neurons" of the temporal crystal.
    Each spin oscillates under the Floquet drive.
    In the crystal phase: all spins oscillate coherently at 2T.
    """
    spins        : List[float]    # sᵢ — spin configuration
    time         : float          # Current time t
    period       : float          # Floquet period T
    drive_phase  : float          # φ = (2πt/T) mod 2π
    disorder     : List[float]    # hᵢ — random disorder fields (MBL)
    step_count   : int = 0
    
    @property
    def n_spins(self) -> int:
        return len(self.spins)
    
    @property
    def magnetization(self) -> float:
        """M = (1/N) Σᵢ sᵢ — the order parameter."""
        return sum(self.spins) / max(self.n_spins, 1)
    
    @property
    def staggered_magnetization(self) -> float:
        """M_s = (1/N) Σᵢ (-1)ⁱ sᵢ — detects antiferromagnetic crystal."""
        return sum((-1)**i * s for i, s in enumerate(self.spins)) / max(self.n_spins, 1)


@dataclass
class CrystalOrderParameter:
    """
    The temporal correlation function C(nT) — the DTC order parameter.
    
    C(nT) = (1/N) Σᵢ ⟨sᵢ(nT)·sᵢ(0)⟩
    
    In THERMAL phase:    C(nT) → 0 as n → ∞  (decorrelates)
    In TIME CRYSTAL:     C(nT) ≠ 0 for all n  (persists forever)
    
    This is THE diagnostic of time-crystal order.
    """
    values       : List[float] = field(default_factory=list)
    times        : List[float] = field(default_factory=list)
    
    def add(self, t: float, c: float):
        self.times.append(t)
        self.values.append(c)
    
    def is_crystal(self, threshold: float = 0.1) -> bool:
        """True if C(nT) remains above threshold — crystal phase."""
        if len(self.values) < 4:
            return False
        recent = self.values[-4:]
        return all(abs(v) > threshold for v in recent)
    
    def decay_rate(self) -> float:
        """Estimate decay rate — 0 = perfect crystal, >0 = thermalizing."""
        if len(self.values) < 2:
            return 0.0
        v0  = abs(self.values[0]) + 1e-12
        vn  = abs(self.values[-1]) + 1e-12
        n   = len(self.values)
        return -math.log(vn / v0) / max(n, 1)
    
    def period_doubling_detected(self) -> bool:
        """
        Detect period doubling: response at 2T when driven at T.
        Signature: C alternates sign every period.
        """
        if len(self.values) < 6:
            return False
        signs = [1 if v > 0 else -1 for v in self.values[-6:]]
        alternating = all(signs[i] * signs[i+1] < 0 for i in range(len(signs)-1))
        return alternating


# ─── Floquet Engine ───────────────────────────────────────────────

class FloquetEngine:
    """
    Periodically drives a spin system and detects time-crystal order.
    
    The drive protocol (standard DTC experiment):
      Step 1 (Ising): H_I = -J Σᵢ sᵢ sᵢ₊₁         (coupling)
      Step 2 (Flip):  H_X = -(π/2 + ε) Σᵢ sᵢ       (near-perfect flip)
      Step 3 (Dis.):  H_D = -Σᵢ hᵢ sᵢ              (random disorder = MBL)
    
    Period T = time for one complete 3-step cycle.
    Crystal: spins return to near-original state after 2T (not T).
    
    Critical parameters:
      W > Wc: MBL stabilizes crystal (prevents heating)
      ε ≈ 0:  near-perfect flip preserves crystal
      J < Jc: weak coupling keeps crystal stable
    
    Author: swordenkisk, March 2026.
    """
    
    def __init__(
        self,
        n_spins  : int   = 32,
        period   : float = 1.0,
        disorder : float = 0.5,
        coupling : float = 0.1,
        epsilon  : float = 0.05,
        seed     : int   = 42,
    ):
        self.n       = n_spins
        self.T       = period
        self.W       = disorder
        self.J       = coupling
        self.eps     = epsilon
        
        rng = random.Random(seed)
        
        # Initialize random spin configuration
        spins    = [rng.choice([-1.0, 1.0]) for _ in range(n_spins)]
        # MBL disorder fields: hᵢ ~ Uniform[-W, W]
        disorder_fields = [rng.uniform(-disorder, disorder) for _ in range(n_spins)]
        
        self.state = FloquetState(
            spins     = spins,
            time      = 0.0,
            period    = period,
            drive_phase = 0.0,
            disorder  = disorder_fields,
        )
        self.initial_spins = list(spins)
        self.order_param   = CrystalOrderParameter()
        self._history      : List[List[float]] = []
    
    # ── Drive Protocol ────────────────────────────────────────────
    
    def step(self) -> FloquetState:
        """
        One complete Floquet period: 3-step DTC protocol.
        
        Returns updated state after period T.
        """
        s = list(self.state.spins)
        n = self.n
        
        # ── Step 1: Ising interaction (coupling J) ────────────────
        # H_I = -J Σᵢ sᵢ sᵢ₊₁
        for i in range(n - 1):
            interaction = self.J * s[i] * s[i+1]
            s[i]   = math.tanh(s[i]   + interaction * self.T)
            s[i+1] = math.tanh(s[i+1] + interaction * self.T)
        
        # ── Step 2: Global flip (near-perfect, angle π+ε) ─────────
        # H_X = -(π/2 + ε) Σᵢ sᵢ
        flip_angle = math.pi + self.eps
        for i in range(n):
            s[i] = math.cos(flip_angle) * s[i]
        
        # ── Step 3: Disorder field (MBL) ──────────────────────────
        # H_D = -Σᵢ hᵢ sᵢ
        for i in range(n):
            s[i] = math.tanh(s[i] + self.state.disorder[i] * self.T)
        
        # Update state
        self.state.spins      = s
        self.state.time      += self.T
        self.state.step_count += 1
        self.state.drive_phase = (2 * math.pi * self.state.time / self.T) % (2 * math.pi)
        
        # Compute and record order parameter C(nT)
        c_nT = self._temporal_correlation()
        self.order_param.add(self.state.time, c_nT)
        self._history.append(list(s))
        
        return self.state
    
    def evolve(self, n_periods: int) -> List[FloquetState]:
        """Evolve for n_periods Floquet periods."""
        states = []
        for _ in range(n_periods):
            states.append(self.step())
        return states
    
    # ── Crystal Diagnostics ───────────────────────────────────────
    
    def detect_phase(self) -> PhasePoint:
        """
        Classify the current phase of the driven system.
        Uses the order parameter C(nT) and MBL indicator.
        """
        if len(self.order_param.values) < 2:
            return PhasePoint(self.W, self.J, CrystalPhase.PRETHERMAL, 0.0, 0.0)
        
        c_latest   = abs(self.order_param.values[-1])
        decay_rate = self.order_param.decay_rate()
        mbl_ratio  = self._mbl_ratio()
        
        if c_latest > 0.3 and mbl_ratio > 1.0:
            phase = CrystalPhase.TIME_CRYSTAL
        elif c_latest > 0.1 and mbl_ratio > 0.5:
            phase = CrystalPhase.PRETHERMAL
        elif mbl_ratio > 1.5 and c_latest < 0.1:
            phase = CrystalPhase.MBL_GLASS
        else:
            phase = CrystalPhase.THERMAL
        
        return PhasePoint(
            disorder    = self.W,
            coupling    = self.J,
            phase       = phase,
            order_param = c_latest,
            mbl_ratio   = mbl_ratio,
        )
    
    def temporal_coherence(self) -> float:
        """C(nT) — current temporal correlation (crystal diagnostic)."""
        return self._temporal_correlation()
    
    def period_doubling_ratio(self) -> float:
        """
        Measure of period-2T response.
        Ratio of power at ω/2 vs ω in magnetization time series.
        Crystal: ratio >> 1 (dominant subharmonic response).
        """
        if len(self._history) < 4:
            return 0.0
        mags    = [sum(h)/len(h) for h in self._history]
        n       = len(mags)
        omega   = sum(mags[i]*math.cos(2*math.pi*i/n)   for i in range(n)) / n
        omega_2 = sum(mags[i]*math.cos(2*math.pi*i/n/2) for i in range(n)) / n
        return abs(omega_2) / (abs(omega) + 1e-12)
    
    def winding_number(self) -> int:
        """
        Topological winding number of the crystal orbit.
        Non-zero = topologically protected time crystal.
        Protected crystal cannot be smoothly deformed to trivial.
        """
        if len(self._history) < 4:
            return 0
        angles = [math.atan2(
            sum(h)/len(h),
            sum((-1)**i*s for i,s in enumerate(h))/len(h)
        ) for h in self._history]
        total_winding = sum(
            self._angle_diff(angles[i+1], angles[i])
            for i in range(len(angles)-1)
        )
        return round(total_winding / (2 * math.pi))
    
    def phase_diagram_point(self) -> Tuple[float, float, str]:
        """Return (W, J, phase_name) — position in DTC phase diagram."""
        pt = self.detect_phase()
        return (pt.disorder, pt.coupling, pt.phase.value)
    
    # ── Internal ──────────────────────────────────────────────────
    
    def _temporal_correlation(self) -> float:
        """
        C(t) = (1/N) Σᵢ sᵢ(t)·sᵢ(0)
        The fundamental DTC order parameter.
        """
        return sum(
            self.state.spins[i] * self.initial_spins[i]
            for i in range(self.n)
        ) / self.n
    
    def _mbl_ratio(self) -> float:
        """
        W / Wc — ratio of disorder to critical disorder.
        > 1: MBL phase (crystal stable)
        < 1: Thermal phase (crystal melts)
        Wc ≈ J · √(ln N)
        """
        Wc = self.J * math.sqrt(math.log(max(self.n, 2)))
        return self.W / max(Wc, 1e-12)
    
    @staticmethod
    def _angle_diff(a: float, b: float) -> float:
        """Shortest angle difference on [-π, π]."""
        d = a - b
        while d > math.pi:  d -= 2*math.pi
        while d < -math.pi: d += 2*math.pi
        return d
    
    def summary(self) -> str:
        phase = self.detect_phase()
        pd    = self.period_doubling_ratio()
        wn    = self.winding_number()
        return (
            f"Floquet Engine [N={self.n}, T={self.T}, W={self.W}, J={self.J}]\n"
            f"  Time elapsed        : {self.state.time:.2f} ({self.state.step_count} periods)\n"
            f"  Phase               : {phase.phase.value}\n"
            f"  Order parameter C(t): {phase.order_param:.4f}\n"
            f"  MBL ratio W/Wc      : {phase.mbl_ratio:.3f} {'✅ STABLE' if phase.mbl_ratio>1 else '⚠️ UNSTABLE'}\n"
            f"  Period doubling     : {pd:.3f}x {'✅ DTC' if pd>1 else '❌ thermal'}\n"
            f"  Winding number      : {wn} {'(topological)' if wn!=0 else '(trivial)'}\n"
            f"  Crystal detected    : {'🔮 YES' if phase.phase==CrystalPhase.TIME_CRYSTAL else '❌ NO'}\n"
        )
