import React, { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react';

import { AnalyzeCreator } from '../../application/AnalyzeCreator';
import type { Creator } from '../../domain/creator-profiling/Creator';
import { parseUsername } from '../../domain/creator-profiling/Username';
import { createCreatorRepository } from '../../infrastructure/createCreatorRepository';

export type AnalysisStatus = 'idle' | 'loading' | 'success' | 'error';

interface CreatorAnalysisValue {
  readonly status: AnalysisStatus;
  readonly creator: Creator | null;
  readonly errorMessage: string | null;
  /** Analiza al usuario escrito en el Onboarding. Devuelve true si terminó bien. */
  analyze(rawUsername: string): Promise<boolean>;
}

const CreatorAnalysisContext = createContext<CreatorAnalysisValue | null>(null);

// Único lugar donde se crea el repositorio (API real o mock) y el caso de uso.
// Si falta la configuración, el error se guarda y se muestra al intentar analizar.
function buildUseCase(): { useCase: AnalyzeCreator | null; configError: string | null } {
  try {
    return { useCase: new AnalyzeCreator(createCreatorRepository()), configError: null };
  } catch (error) {
    return { useCase: null, configError: messageOf(error) };
  }
}

function messageOf(error: unknown): string {
  if (error instanceof Error && error.message.trim() !== '') return error.message;
  return 'Ocurrió un error inesperado al analizar el perfil.';
}

export function CreatorAnalysisProvider({ children }: { children: React.ReactNode }) {
  const { useCase, configError } = useMemo(buildUseCase, []);
  const [status, setStatus] = useState<AnalysisStatus>('idle');
  const [creator, setCreator] = useState<Creator | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  // Si se lanza otro análisis antes de que termine el anterior, se ignora el resultado viejo.
  const requestId = useRef(0);

  const analyze = useCallback(
    async (rawUsername: string): Promise<boolean> => {
      const id = ++requestId.current;
      setStatus('loading');
      setCreator(null);
      setErrorMessage(null);

      const fail = (message: string) => {
        if (id !== requestId.current) return false;
        setErrorMessage(message);
        setStatus('error');
        return false;
      };

      if (!useCase) return fail(configError ?? 'La app no está configurada.');
      const username = parseUsername(rawUsername);
      if (!username) {
        return fail(
          `"${rawUsername}" no es un usuario de TikTok válido. Usa de 2 a 24 letras, números, puntos o guiones bajos.`,
        );
      }

      try {
        const result = await useCase.execute(username);
        if (id !== requestId.current) return false;
        setCreator(result);
        setStatus('success');
        return true;
      } catch (error) {
        return fail(messageOf(error));
      }
    },
    [useCase, configError],
  );

  const value = useMemo(
    () => ({ status, creator, errorMessage, analyze }),
    [status, creator, errorMessage, analyze],
  );

  return <CreatorAnalysisContext.Provider value={value}>{children}</CreatorAnalysisContext.Provider>;
}

export function useCreatorAnalysis(): CreatorAnalysisValue {
  const value = useContext(CreatorAnalysisContext);
  if (!value) {
    throw new Error('useCreatorAnalysis debe usarse dentro de <CreatorAnalysisProvider>.');
  }
  return value;
}
