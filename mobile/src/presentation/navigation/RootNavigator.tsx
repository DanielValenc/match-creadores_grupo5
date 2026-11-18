import React, { useState } from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import FrontScreen from '../screens/FrontScreen';
import OnboardingScreen from '../screens/OnboardingScreen';
import LoadingScreen from '../screens/LoadingScreen';
import DashboardScreen from '../screens/DashboardScreen';
import ReporteScreen from '../screens/ReporteScreen';
import SectoresCompatiblesScreen from '../screens/SectoresCompatiblesScreen';
import PropuestaScreen from '../screens/PropuestaScreen';

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

export default function RootNavigator() {
  const [usuario, setUsuario] = useState('');

  return (
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
            onBack={() => navigation.goBack()}
          />
        )}
      </Stack.Screen>

      <Stack.Screen name="Dashboard">
        {({ navigation }) => (
          <DashboardScreen onNext={() => navigation.navigate('Reporte')} />
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
  );
}
