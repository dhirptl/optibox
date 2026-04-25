import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { runSimulation } from "../lib/api";
import {
  applyGridChangesBackwardInPlace,
  applyGridChangesForwardInPlace,
  cloneSiloState,
} from "../lib/parsing";
import type {
  EventLogEntry,
  Pallet,
  RunSimulationResponse,
  SiloState,
  SimulationMetrics,
  SimulationTimelineFrame,
  ShuttleSnapshot,
} from "../lib/types";

const DEFAULT_METRICS: SimulationMetrics = {
  full_pallets_out_of_8: 0,
  pallets_completed: 0,
  avg_time_per_pallet: 0,
};

export function useSimulationPlayback(selectedY: number) {
  const [data, setData] = useState<RunSimulationResponse | null>(null);
  const [currentTick, setCurrentTick] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [baseSilo, setBaseSilo] = useState<SiloState | null>(null);
  const [playbackSilo, setPlaybackSilo] = useState<SiloState>(new Map());
  const appliedTickRef = useRef(0);

  const totalTicks = data?.duration_seconds ?? 0;
  const frameByTick = useMemo(() => {
    const index = new Map<number, SimulationTimelineFrame>();
    if (!data) return index;
    for (const frame of data.timeline) {
      index.set(frame.t, frame);
    }
    return index;
  }, [data]);

  const frame = useMemo<SimulationTimelineFrame | null>(() => {
    if (!data || frameByTick.size === 0) return null;
    return frameByTick.get(currentTick) ?? null;
  }, [currentTick, data, frameByTick]);

  useEffect(() => {
    if (!playing || totalTicks <= 0) return;
    const tickMs = 1000;
    const id = window.setInterval(() => {
      setCurrentTick((prev) => {
        const next = Math.min(totalTicks, prev + speed);
        if (next >= totalTicks) {
          setPlaying(false);
          return totalTicks;
        }
        return next;
      });
    }, tickMs);
    return () => window.clearInterval(id);
  }, [playing, speed, totalTicks]);

  useEffect(() => {
    if (!data || !baseSilo) return;
    setPlaybackSilo((prev) => {
      let next = prev.size > 0 ? cloneSiloState(prev) : cloneSiloState(baseSilo);
      const appliedTick = appliedTickRef.current;
      if (currentTick === appliedTick) return next;

      if (currentTick > appliedTick) {
        for (let tick = appliedTick + 1; tick <= currentTick; tick += 1) {
          const tickFrame = frameByTick.get(tick) ?? frameByTick.get(tick + 1);
          if (!tickFrame) continue;
          applyGridChangesForwardInPlace(next, tickFrame.grid_changes ?? []);
        }
      } else {
        for (let tick = appliedTick; tick > currentTick; tick -= 1) {
          const tickFrame = frameByTick.get(tick) ?? frameByTick.get(tick + 1);
          if (!tickFrame) continue;
          applyGridChangesBackwardInPlace(next, tickFrame.grid_changes ?? []);
        }
      }
      appliedTickRef.current = currentTick;
      return next;
    });
  }, [baseSilo, currentTick, data, frameByTick]);

  const finalMetrics =
    data?.final_metrics ??
    frameByTick.get(totalTicks)?.final_metrics ??
    frameByTick.get(totalTicks)?.metrics ??
    data?.metrics ??
    DEFAULT_METRICS;
  const metrics = frame?.metrics ?? DEFAULT_METRICS;
  const pallets: Pallet[] = frame?.pallet_slots ?? [];
  const shuttles: ShuttleSnapshot[] = frame?.shuttles ?? [];
  const frameTick = Math.max(0, currentTick);
  const actionMessage =
    frameTick === 0
      ? "Awaiting simulation start..."
      : (frame?.action_message ?? "Awaiting simulation start...");

  const events: EventLogEntry[] = useMemo(() => {
    if (!data) return [];
    return data.events
      .filter((event) => event.t <= frameTick)
      .slice(-100)
      .reverse();
  }, [data, frameTick]);

  const shuttleXByAisle = useMemo(() => {
    const byAisle: Record<number, number> = {};
    for (const shuttle of shuttles) {
      if (shuttle.y !== selectedY) continue;
      byAisle[shuttle.aisle] = shuttle.x;
    }
    return byAisle;
  }, [selectedY, shuttles]);

  const startSimulation = useCallback(
    async (args: {
      ticks?: number;
      inboundSeed?: number;
      numBoxes?: number;
      baseSilo: SiloState;
    }) => {
      setLoading(true);
      setError(null);
      try {
        const next = await runSimulation(args);
        setData(next);
        const clonedBase = cloneSiloState(args.baseSilo);
        setBaseSilo(clonedBase);
        setPlaybackSilo(clonedBase);
        appliedTickRef.current = 0;
        setCurrentTick(0);
        setSpeed(1);
        setPlaying(next.duration_seconds > 0 && next.timeline.length > 0);
        return true;
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        return false;
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const seek = useCallback(
    (tick: number) => {
      if (!data) return;
      const clamped = Math.min(Math.max(Math.round(tick), 0), totalTicks);
      setCurrentTick(clamped);
    },
    [data, totalTicks],
  );

  const togglePlay = useCallback(() => {
    if (!data || totalTicks <= 0) return;
    setPlaying((prev) => !prev);
  }, [data, totalTicks]);

  const reset = useCallback(() => {
    setData(null);
    setCurrentTick(0);
    setPlaying(false);
    setSpeed(1);
    setLoading(false);
    setError(null);
    setBaseSilo(null);
    setPlaybackSilo(new Map());
    appliedTickRef.current = 0;
  }, []);

  return {
    loading,
    error,
    hasSimulation: data !== null,
    actionMessage,
    currentTick,
    totalTicks,
    speed,
    playing,
    metrics,
    finalMetrics,
    pallets,
    shuttles,
    shuttleXByAisle,
    playbackSilo,
    events,
    startSimulation,
    seek,
    setSpeed,
    togglePlay,
    reset,
  };
}
