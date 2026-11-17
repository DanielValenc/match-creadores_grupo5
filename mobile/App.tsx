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
import type { Documento } from "./src/api";

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
  const [usuario, setUsuario] = useState("danielvalencia365");
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
                onSubmit={(u) => {
                  setUsuario(u);
                  navigation.navigate("Loading");
                }}
              />
            )}
          </Stack.Screen>

          <Stack.Screen name="Loading">
            {({ navigation }) => (
              <LoadingScreen
                usuario={usuario}
                onDone={(d) => {
                  setDatos(d);
                  navigation.replace("Dashboard");
                }}
                onBack={() => navigation.goBack()}
              />
            )}
          </Stack.Screen>

          <Stack.Screen name="Dashboard">
            {({ navigation }) => (
              <DashboardScreen
                bigFive={datos?.analisis_bigfive}
                resumen={datos?.analisis_bigfive?.resumen}
                puntajeOrganico={
                  datos
                    ? (datos.auditoria_audiencia?.puntaje_organico ?? null)
                    : undefined
                }
                onNext={() => navigation.navigate("Reporte")}
              />
            )}
          </Stack.Screen>

          <Stack.Screen name="Reporte">
            {({ navigation }) => (
              <ReporteScreen onNext={() => navigation.navigate("Sectores")} />
            )}
          </Stack.Screen>

          <Stack.Screen name="Sectores">
            {({ navigation }) => (
              <SectoresCompatiblesScreen
                onContact={() => navigation.navigate("Propuesta")}
                onCancel={() => navigation.goBack()}
              />
            )}
          </Stack.Screen>

          <Stack.Screen name="Propuesta">
            {({ navigation }) => (
              <PropuestaScreen
                usuario={usuario}
                onHome={() =>
                  navigation.reset({
                    index: 0,
                    routes: [{ name: "Onboarding" }],
                  })
                }
              />
            )}
          </Stack.Screen>
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
