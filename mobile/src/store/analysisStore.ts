import { useEffect, useState } from 'react';
import type { CreatorAnalysis } from '../types/creatorAnalysis';

type AnalysisState = {
  analysis: CreatorAnalysis | null;
  selectedSector: string;
};

let state: AnalysisState = {
  analysis: null,
  selectedSector: '',
};

const listeners = new Set<(next: AnalysisState) => void>();

function publish(next: AnalysisState) {
  state = next;
  listeners.forEach((listener) => listener(state));
}

export function setCurrentAnalysis(analysis: CreatorAnalysis) {
  publish({ analysis, selectedSector: '' });
}

export function setSelectedSector(selectedSector: string) {
  publish({ ...state, selectedSector });
}

export function clearCurrentAnalysis() {
  publish({ analysis: null, selectedSector: '' });
}

export function getAnalysisState() {
  return state;
}

export function useAnalysisStore() {
  const [snapshot, setSnapshot] = useState<AnalysisState>(state);

  useEffect(() => {
    const listener = (next: AnalysisState) => setSnapshot(next);
    listeners.add(listener);
    setSnapshot(state);
    return () => {
      listeners.delete(listener);
    };
  }, []);

  return snapshot;
}
