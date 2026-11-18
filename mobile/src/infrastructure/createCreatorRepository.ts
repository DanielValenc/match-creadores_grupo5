import type { CreatorRepository } from '../domain/creator-profiling/CreatorRepository';
import { ApiCreatorRepository } from './api/ApiCreatorRepository';
import { config } from './config';
import { MockCreatorRepository } from './mock/MockCreatorRepository';

/** Elige la implementación del puerto según EXPO_PUBLIC_USE_MOCK y EXPO_PUBLIC_API_URL. */
export function createCreatorRepository(): CreatorRepository {
  if (config.useMock) return new MockCreatorRepository();
  if (!config.apiUrl) {
    throw new Error(
      'Falta EXPO_PUBLIC_API_URL. Configúrala en mobile/.env.local o usa EXPO_PUBLIC_USE_MOCK=true.',
    );
  }
  return new ApiCreatorRepository(config.apiUrl);
}
