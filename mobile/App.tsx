import React, { useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import FrontScreen from './src/screens/FrontScreen';
import OnboardingScreen from './src/screens/OnboardingScreen';
import LoadingScreen from './src/screens/LoadingScreen';
import DashboardScreen from './src/screens/DashboardScreen';
import ReporteScreen from './src/screens/ReporteScreen';
import SectoresCompatiblesScreen from './src/screens/SectoresCompatiblesScreen';
import PropuestaScreen from './src/screens/PropuestaScreen';

export type RootStackParamList = {
  Front: undefined;
  Onboarding: undefined;
  Loading: undefined;
  Dashboard: undefined;
  Reporte: undefined;
  Sectores: undefined;
  Propuesta: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

// OPCIONAL: cuando quieras usar datos reales de tu JSON, descomenta y pásalos a Dashboard.
// import perfil from './assets/data/perfil.json';
// const bigFive = (perfil as any)?.analisis_bigfive;

export default function App() {
  const [usuario, setUsuario] = useState('danielvalencia365');

  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <Stack.Navigator
          initialRouteName="Front"
          screenOptions={{ headerShown: false, animation: 'fade' }}
        >
          <Stack.Screen name="Front">
            {({ navigation }) => (
              <FrontScreen onDone={() => navigation.replace('Onboarding')} />
            )}
          </Stack.Screen>

          <Stack.Screen name="Onboarding">
            {({ navigation }) => (
              <OnboardingScreen
                onSubmit={(u) => {
                  setUsuario(u);
                  navigation.navigate('Loading');
                }}
              />
            )}
          </Stack.Screen>

          <Stack.Screen name="Loading">
            {({ navigation }) => (
              <LoadingScreen
                usuario={usuario}
                onDone={() => navigation.replace('Dashboard')}
              />
            )}
          </Stack.Screen>

          <Stack.Screen name="Dashboard">
            {({ navigation }) => (
              <DashboardScreen
                // bigFive={bigFive}
                // resumen={bigFive?.resumen}
                onNext={() => navigation.navigate('Reporte')}
              />
            )}
          </Stack.Screen>

          <Stack.Screen name="Reporte">
            {({ navigation }) => (
              <ReporteScreen onNext={() => navigation.navigate('Sectores')} />
            )}
          </Stack.Screen>

          <Stack.Screen name="Sectores">
            {({ navigation }) => (
              <SectoresCompatiblesScreen
                onContact={() => navigation.navigate('Propuesta')}
                onCancel={() => navigation.goBack()}
              />
            )}
          </Stack.Screen>

          <Stack.Screen name="Propuesta">
            {({ navigation }) => (
              <PropuestaScreen
                usuario={usuario}
                onHome={() =>
                  navigation.reset({ index: 0, routes: [{ name: 'Onboarding' }] })
                }
              />
            )}
          </Stack.Screen>
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}