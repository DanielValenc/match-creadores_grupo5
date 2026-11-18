import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import RootNavigator from './src/presentation/navigation/RootNavigator';
import { CreatorAnalysisProvider } from './src/presentation/hooks/useCreatorAnalysis';

export default function App() {
  return (
    <SafeAreaProvider>
      <CreatorAnalysisProvider>
        <NavigationContainer>
          <RootNavigator />
        </NavigationContainer>
      </CreatorAnalysisProvider>
    </SafeAreaProvider>
  );
}
