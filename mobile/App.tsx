import React, { useState } from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { SafeAreaProvider } from "react-native-safe-area-context";

import FrontScreen from "./src/screens/FrontScreen";
import OnboardingScreen from "./src/screens/OnboardingScreen";
import LoadingScreen from "./src/screens/LoadingScreen";
import DashboardScreen from "./src/screens/DashboardScreen";
import ReporteScreen from "./src/screens/ReporteScreen";
import SectoresCompatiblesScreen from "./src/screens/SectoresCompatiblesScreen";
import PropuestaScreen from "./src/screens/PropuestaScreen";
import type { Documento } from "./src/services/api";

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

export default function App() {
  const [usuario, setUsuario] = useState("");
  const [datos, setDatos] = useState<Documento | null>(null);

  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <Stack.Navigator
          initialRouteName="Front"
          screenOptions={{ headerShown: false, animation: "fade" }}
        >
          <Stack.Screen name="Front">
            {({ navigation }) => (
              <FrontScreen onDone={() => navigation.replace("Onboarding")} />
            )}
          </Stack.Screen>

          <Stack.Screen name="Onboarding">
            {({ navigation }) => (
              <OnboardingScreen
                onSubmit={(username) => {
                  setUsuario(username);
                  setDatos(null);
                  navigation.navigate("Loading");
                }}
              />
            )}
          </Stack.Screen>

          <Stack.Screen name="Loading">
            {({ navigation }) => (
              <LoadingScreen
                usuario={usuario}
                onDone={(documento) => {
                  setDatos(documento);
                  navigation.replace("Dashboard");
                }}
                onBack={() => navigation.goBack()}
              />
            )}
          </Stack.Screen>

          <Stack.Screen name="Dashboard">
            {({ navigation }) => (
              <DashboardScreen
                datos={datos}
                onNext={() => navigation.navigate("Reporte")}
              />
            )}
          </Stack.Screen>

          <Stack.Screen name="Reporte">
            {({ navigation }) => (
              <ReporteScreen
                auditoria={datos?.auditoria_audiencia}
                onNext={() => navigation.navigate("Sectores")}
              />
            )}
          </Stack.Screen>

          <Stack.Screen name="Sectores">
            {({ navigation }) => (
              <SectoresCompatiblesScreen
                perfilComercial={datos?.perfil_comercial}
                onContact={() => navigation.navigate("Propuesta")}
                onCancel={() => navigation.goBack()}
              />
            )}
          </Stack.Screen>

          <Stack.Screen name="Propuesta">
            {({ navigation }) => (
              <PropuestaScreen
                usuario={usuario}
                onHome={() => {
                  setDatos(null);
                  navigation.reset({
                    index: 0,
                    routes: [{ name: "Onboarding" }],
                  });
                }}
              />
            )}
          </Stack.Screen>
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
